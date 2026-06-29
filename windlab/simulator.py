"""Application-level simulation orchestration."""

import csv
import io
import json
from collections.abc import Iterable
from dataclasses import dataclass
from math import exp

from windlab.airfoils import estimate_airfoil_performance
from windlab.bemt import calculate_bemt_lite
from windlab.blade_geometry import estimate_blade_planform_area, summarize_blade_geometry
from windlab.generator import simulate_generator
from windlab.materials import get_material, get_surface_finish
from windlab.models import SimulationInput, SimulationResult
from windlab.physics import (
    angular_speed,
    available_wind_power,
    estimate_cp,
    estimate_tip_speed_ratio,
    rotor_swept_area,
    rpm_from_angular_speed,
    torque_from_power,
)
from windlab.scoring import build_recommendations, design_score
from windlab.section_airfoils import get_section_airfoil

DEFAULT_AIR_DYNAMIC_VISCOSITY_KG_M_S = 1.81e-5
DEFAULT_SURFACE_FINISH = "Raw 3D print"


@dataclass(frozen=True, slots=True)
class SectionAirfoilBlend:
    """Weighted section-airfoil result for the simplified pre-BEMT model."""

    representative_airfoil_name: str
    representative_airfoil_family: str
    lift_coefficient: float
    drag_coefficient: float
    lift_drag_ratio: float
    efficiency_factor: float
    stall_risk: bool
    warnings: tuple[str, ...]


def estimate_representative_angle_of_attack(
    pitch_angle_deg: float,
    representative_twist_deg: float,
) -> float:
    """Estimate a mid-span angle of attack for the educational airfoil model."""

    return pitch_angle_deg + 0.35 * representative_twist_deg


def estimate_reynolds_number(
    *,
    air_density_kg_m3: float,
    wind_speed_m_s: float,
    chord_m: float,
    dynamic_viscosity_kg_m_s: float = DEFAULT_AIR_DYNAMIC_VISCOSITY_KG_M_S,
) -> float:
    """Estimate blade-section Reynolds number from wind speed and representative chord."""

    return air_density_kg_m3 * wind_speed_m_s * chord_m / dynamic_viscosity_kg_m_s


def adjust_tip_speed_ratio_for_airfoil(
    tip_speed_ratio: float,
    airfoil_efficiency_factor: float,
) -> float:
    """Let draggy airfoils slow the rotor while efficient sections preserve RPM."""

    speed_factor = 0.75 + 0.25 * airfoil_efficiency_factor
    return min(12.0, max(1.0, tip_speed_ratio * speed_factor))


def _thickness_factor(thickness_percent: float | None, radius_fraction: float) -> float:
    """Approximate root strength benefit and tip drag penalty from airfoil thickness."""

    if thickness_percent is None:
        return 1.0

    factor = 1.0
    if radius_fraction < 0.30 and thickness_percent >= 15.0:
        factor += 0.05
    if radius_fraction < 0.30 and thickness_percent < 12.0:
        factor -= 0.06
    if radius_fraction > 0.65 and thickness_percent > 12.0:
        factor -= min(0.18, 0.02 * (thickness_percent - 12.0))
    if radius_fraction > 0.80 and thickness_percent <= 12.0:
        factor += 0.03
    return max(0.70, min(1.10, factor))


def estimate_section_airfoil_blend(inputs: SimulationInput) -> SectionAirfoilBlend:
    """Blend all section airfoils so root, mid-span, and tip choices all matter."""

    weighted_lift = 0.0
    weighted_drag = 0.0
    weighted_efficiency = 0.0
    total_weight = 0.0
    representative_weight = -1.0
    representative_airfoil_name = inputs.blade_sections[0].airfoil_name
    representative_airfoil_family = get_section_airfoil(representative_airfoil_name).family
    stall_risk = False
    warnings: list[str] = []

    active_span = max(inputs.rotor_radius_m - inputs.hub_radius_m, 0.001)
    for section in inputs.blade_sections:
        airfoil_definition = get_section_airfoil(section.airfoil_name)
        radius_fraction = max(
            0.0,
            min(1.0, (section.position_m - inputs.hub_radius_m) / active_span),
        )
        radius_weight = 0.20 + radius_fraction
        if radius_fraction > 0.72:
            radius_weight *= 1.20
        if radius_fraction < 0.25:
            radius_weight *= 0.90

        weight = section.chord_m * radius_weight
        angle_of_attack = estimate_representative_angle_of_attack(
            inputs.pitch_angle_deg,
            section.twist_angle_deg,
        )
        reynolds_number = estimate_reynolds_number(
            air_density_kg_m3=inputs.air_density_kg_m3,
            wind_speed_m_s=inputs.wind_speed_m_s,
            chord_m=section.chord_m,
            dynamic_viscosity_kg_m_s=inputs.air_dynamic_viscosity_kg_m_s,
        )
        performance = estimate_airfoil_performance(
            airfoil_definition.family,
            angle_of_attack_deg=angle_of_attack,
            reynolds_number=reynolds_number if inputs.use_reynolds_correction else 200_000.0,
        )
        thickness_factor = _thickness_factor(
            airfoil_definition.thickness_percent,
            radius_fraction,
        )
        section_efficiency = performance.efficiency_factor * thickness_factor

        weighted_lift += weight * performance.lift_coefficient
        weighted_drag += weight * performance.drag_coefficient / max(thickness_factor, 0.001)
        weighted_efficiency += weight * section_efficiency
        total_weight += weight
        stall_risk = stall_risk or performance.stall_risk
        warnings.extend(performance.warnings)

        representative_score = weight * section_efficiency
        if representative_score > representative_weight:
            representative_weight = representative_score
            representative_airfoil_name = airfoil_definition.name
            representative_airfoil_family = airfoil_definition.family

    if total_weight <= 0.0:
        fallback = estimate_airfoil_performance(
            inputs.airfoil_type,
            angle_of_attack_deg=inputs.pitch_angle_deg,
            reynolds_number=200_000.0,
        )
        return SectionAirfoilBlend(
            representative_airfoil_name=inputs.airfoil_type,
            representative_airfoil_family=inputs.airfoil_type,
            lift_coefficient=fallback.lift_coefficient,
            drag_coefficient=fallback.drag_coefficient,
            lift_drag_ratio=fallback.lift_drag_ratio,
            efficiency_factor=fallback.efficiency_factor,
            stall_risk=fallback.stall_risk,
            warnings=fallback.warnings,
        )

    lift = weighted_lift / total_weight
    drag = weighted_drag / total_weight
    return SectionAirfoilBlend(
        representative_airfoil_name=representative_airfoil_name,
        representative_airfoil_family=representative_airfoil_family,
        lift_coefficient=round(lift, 3),
        drag_coefficient=round(drag, 4),
        lift_drag_ratio=round(abs(lift) / max(drag, 0.001), 2),
        efficiency_factor=round(max(0.45, min(1.12, weighted_efficiency / total_weight)), 3),
        stall_risk=stall_risk,
        warnings=tuple(dict.fromkeys(warnings)),
    )


def has_custom_calibration(inputs: SimulationInput) -> bool:
    """Return whether the simulation differs from the classroom defaults."""

    return any(
        (
            inputs.air_dynamic_viscosity_kg_m_s != DEFAULT_AIR_DYNAMIC_VISCOSITY_KG_M_S,
            inputs.practical_cp_limit != 0.50,
            inputs.airfoil_efficiency_multiplier != 1.0,
            inputs.mechanical_loss_percent != 0.0,
            inputs.startup_torque_n_m != 0.0,
            inputs.surface_finish != DEFAULT_SURFACE_FINISH,
            inputs.use_custom_material_properties,
            inputs.use_estimated_blade_mass,
            not inputs.use_hub_area_loss,
            not inputs.use_airfoil_correction,
            not inputs.use_material_roughness,
            not inputs.use_generator_power_cap,
            not inputs.use_generator_load_feedback,
            not inputs.use_practical_cp_limit,
            not inputs.use_reynolds_correction,
            not inputs.use_prandtl_loss,
            not inputs.use_startup_torque_loss,
            not inputs.use_bemt_lite_section_model,
        )
    )


def estimate_rotor_inertia_kg_m2(inputs: SimulationInput, blade_mass_kg: float) -> float:
    """Estimate rotor inertia from blade mass and radius.

    This treats each blade as a tapered classroom blade distributed from hub to
    tip. It is intentionally approximate, but it makes heavy 3D-printed blades
    slower to reach useful RPM during a timed competition run.
    """

    radial_mass_factor = (
        inputs.rotor_radius_m**2
        + inputs.rotor_radius_m * inputs.hub_radius_m
        + inputs.hub_radius_m**2
    ) / 3.0
    return inputs.blade_count * blade_mass_kg * radial_mass_factor


def estimate_required_startup_torque_n_m(
    inputs: SimulationInput,
    blade_mass_kg: float,
    rotor_inertia_kg_m2: float,
) -> float:
    """Estimate torque that must be exceeded before useful rotation begins."""

    mass_friction_torque = blade_mass_kg * inputs.blade_count * inputs.rotor_radius_m * 0.004
    inertia_breakaway_torque = rotor_inertia_kg_m2 * 0.015
    return inputs.startup_torque_n_m + mass_friction_torque + inertia_breakaway_torque


def estimate_spinup_factor(
    *,
    rotor_inertia_kg_m2: float,
    target_angular_speed_rad_s: float,
    torque_n_m: float,
    trial_duration_s: float,
) -> float:
    """Estimate how much of steady-state RPM/power is reached during the trial."""

    if torque_n_m <= 0.0 or target_angular_speed_rad_s <= 0.0:
        return 0.0
    time_constant_s = rotor_inertia_kg_m2 * target_angular_speed_rad_s / max(torque_n_m, 1e-6)
    if time_constant_s <= 0.0:
        return 1.0
    return max(0.0, min(1.0, 1.0 - exp(-trial_duration_s / time_constant_s)))


def simulate(inputs: SimulationInput) -> SimulationResult:
    """Run one deterministic educational simulation."""

    material = get_material(inputs.material)
    surface_finish = get_surface_finish(inputs.surface_finish)
    material_density = (
        inputs.custom_material_density_kg_m3
        if inputs.use_custom_material_properties
        else material.density_kg_m3
    )
    material_roughness_default = (
        inputs.custom_material_roughness_factor
        if inputs.use_custom_material_properties
        else material.roughness_factor
    )
    material_durability = (
        inputs.custom_material_durability_factor
        if inputs.use_custom_material_properties
        else material.durability_factor
    )
    geometry = summarize_blade_geometry(inputs)
    blade_planform_area = estimate_blade_planform_area(inputs)
    effective_blade_mass = (
        blade_planform_area * inputs.blade_thickness_m * material_density
        if inputs.use_estimated_blade_mass
        else inputs.blade_mass_kg
    )
    hub_radius = inputs.hub_radius_m if inputs.use_hub_area_loss else 0.0
    area = rotor_swept_area(inputs.rotor_radius_m, hub_radius)
    wind_power = available_wind_power(inputs.air_density_kg_m3, area, inputs.wind_speed_m_s)
    angle_of_attack = estimate_representative_angle_of_attack(
        inputs.pitch_angle_deg,
        geometry.representative_twist_deg,
    )
    reynolds_number = estimate_reynolds_number(
        air_density_kg_m3=inputs.air_density_kg_m3,
        wind_speed_m_s=inputs.wind_speed_m_s,
        chord_m=geometry.mean_chord_m,
        dynamic_viscosity_kg_m_s=inputs.air_dynamic_viscosity_kg_m_s,
    )
    if inputs.blade_sections:
        airfoil = estimate_section_airfoil_blend(inputs)
        effective_airfoil_type = airfoil.representative_airfoil_family
    else:
        effective_airfoil_type = inputs.airfoil_type
        airfoil = estimate_airfoil_performance(
            effective_airfoil_type,
            angle_of_attack_deg=angle_of_attack,
            reynolds_number=reynolds_number if inputs.use_reynolds_correction else 200_000.0,
        )
    effective_airfoil_efficiency = (
        airfoil.efficiency_factor * inputs.airfoil_efficiency_multiplier
        if inputs.use_airfoil_correction
        else 1.0
    )
    effective_airfoil_efficiency = max(0.1, min(2.0, effective_airfoil_efficiency))
    material_roughness = (
        material_roughness_default * surface_finish.drag_factor
        if inputs.use_material_roughness
        else 1.0
    )
    surface_speed_factor = max(0.55, min(1.05, material_roughness**0.65))
    tsr = (
        adjust_tip_speed_ratio_for_airfoil(
            estimate_tip_speed_ratio(
                inputs.blade_count,
                inputs.pitch_angle_deg,
                geometry.representative_twist_deg,
            ),
            effective_airfoil_efficiency,
        )
        * surface_speed_factor
    )
    cp = estimate_cp(
        tip_speed_ratio=tsr,
        blade_count=inputs.blade_count,
        root_chord_m=geometry.root_chord_m,
        tip_chord_m=geometry.tip_chord_m,
        rotor_radius_m=inputs.rotor_radius_m,
        pitch_angle_deg=inputs.pitch_angle_deg,
        twist_angle_deg=geometry.representative_twist_deg,
        roughness_factor=material_roughness * effective_airfoil_efficiency,
        mean_chord_m=geometry.mean_chord_m,
        practical_cp_limit=inputs.practical_cp_limit,
        use_practical_cp_limit=inputs.use_practical_cp_limit,
    )
    mechanical_power = cp * wind_power
    omega = angular_speed(tsr, inputs.wind_speed_m_s, inputs.rotor_radius_m)
    rpm = rpm_from_angular_speed(omega)
    torque = torque_from_power(mechanical_power, omega)
    model_mode = "Empirical Cp"
    bemt_section_count = 0
    bemt_mean_relative_wind_speed = 0.0
    bemt_mean_angle_of_attack = angle_of_attack
    bemt_mean_prandtl_loss_factor = 1.0
    bemt_warnings: tuple[str, ...] = ()

    if inputs.blade_sections and inputs.use_bemt_lite_section_model:
        bemt = calculate_bemt_lite(
            inputs,
            tip_speed_ratio=tsr,
            material_roughness_factor=material_roughness,
            airfoil_efficiency_multiplier=inputs.airfoil_efficiency_multiplier,
            use_airfoil_correction=inputs.use_airfoil_correction,
            use_reynolds_correction=inputs.use_reynolds_correction,
            practical_cp_limit=inputs.practical_cp_limit,
            use_practical_cp_limit=inputs.use_practical_cp_limit,
            use_prandtl_loss=inputs.use_prandtl_loss,
        )
        section_airfoil_drive_factor = max(0.45, min(1.0, effective_airfoil_efficiency))
        mechanical_power = bemt.mechanical_power_w * section_airfoil_drive_factor
        torque = bemt.torque_n_m * section_airfoil_drive_factor
        cp = bemt.cp * section_airfoil_drive_factor
        model_mode = "BEMT-lite"
        bemt_section_count = bemt.section_count
        bemt_mean_relative_wind_speed = bemt.mean_relative_wind_speed_m_s
        bemt_mean_angle_of_attack = bemt.mean_angle_of_attack_deg
        bemt_mean_prandtl_loss_factor = bemt.mean_prandtl_loss_factor
        bemt_warnings = bemt.warnings

    rotor_inertia = estimate_rotor_inertia_kg_m2(inputs, effective_blade_mass)
    required_startup_torque = estimate_required_startup_torque_n_m(
        inputs,
        effective_blade_mass,
        rotor_inertia,
    )
    spinup_factor = 1.0
    warnings: list[str] = []
    if inputs.use_startup_torque_loss and torque < required_startup_torque:
        mechanical_power = 0.0
        cp = 0.0
        omega = 0.0
        rpm = 0.0
        torque = 0.0
        spinup_factor = 0.0
        warnings.append(
            "Startup torque loss: estimated torque is below the required startup torque "
            "from the generator and blade mass."
        )
    else:
        spinup_factor = estimate_spinup_factor(
            rotor_inertia_kg_m2=rotor_inertia,
            target_angular_speed_rad_s=omega,
            torque_n_m=torque,
            trial_duration_s=inputs.trial_duration_s,
        )
        if spinup_factor < 0.995:
            mechanical_power *= spinup_factor
            omega *= spinup_factor
            rpm = rpm_from_angular_speed(omega)
            torque = torque_from_power(mechanical_power, omega)
            cp = mechanical_power / wind_power if wind_power > 0.0 else 0.0
        if 0.0 < spinup_factor < 0.80:
            warnings.append(
                "Heavy rotor response: blade mass may prevent the rotor from reaching full "
                "RPM during the timed run."
            )

    if inputs.mechanical_loss_percent > 0.0 and mechanical_power > 0.0:
        mechanical_power *= 1.0 - inputs.mechanical_loss_percent / 100.0
        torque = torque_from_power(mechanical_power, omega)
        cp = mechanical_power / wind_power if wind_power > 0.0 else 0.0

    generator = simulate_generator(
        rotor_rpm=rpm,
        mechanical_power_w=mechanical_power,
        volts_per_1000_rpm=inputs.generator_volts_per_1000_rpm,
        internal_resistance_ohm=inputs.generator_internal_resistance_ohm,
        load_resistance_ohm=inputs.load_resistance_ohm,
        efficiency_percent=inputs.generator_efficiency_percent,
        gear_ratio=inputs.gear_ratio,
        trial_duration_s=inputs.trial_duration_s,
        cap_output_by_mechanical_power=inputs.use_generator_power_cap,
        apply_load_feedback=inputs.use_generator_load_feedback,
    )
    if inputs.use_generator_load_feedback and generator.generator_load_factor < 0.999:
        rpm *= generator.generator_load_factor
        omega *= generator.generator_load_factor
        tsr = omega * inputs.rotor_radius_m / inputs.wind_speed_m_s
        torque = torque_from_power(mechanical_power, omega)

    if has_custom_calibration(inputs):
        warnings.append(
            "Custom calibration active: constants or model toggles differ from classroom defaults."
        )
    if inputs.wind_speed_m_s > 25.0:
        warnings.append(
            "High wind speed: this model does not simulate structural or shutdown limits."
        )
    if inputs.rotor_radius_m > 10.0:
        warnings.append("Large rotor: simplified assumptions become increasingly unrealistic.")
    warnings.extend(airfoil.warnings)
    warnings.extend(bemt_warnings)

    return SimulationResult(
        rotor_area_m2=round(area, 4),
        available_wind_power_w=round(wind_power, 3),
        mechanical_power_w=round(mechanical_power, 3),
        rpm=round(rpm, 2),
        torque_n_m=round(torque, 3),
        cp=round(cp, 4),
        tip_speed_ratio=round(tsr, 3),
        efficiency_percent=round(cp * 100.0, 2),
        effective_blade_mass_kg=round(effective_blade_mass, 4),
        blade_planform_area_m2=round(blade_planform_area, 4),
        material_density_kg_m3=round(material_density, 2),
        model_mode=model_mode,
        bemt_section_count=bemt_section_count,
        bemt_mean_relative_wind_speed_m_s=round(bemt_mean_relative_wind_speed, 3),
        bemt_mean_angle_of_attack_deg=round(bemt_mean_angle_of_attack, 3),
        bemt_mean_prandtl_loss_factor=round(bemt_mean_prandtl_loss_factor, 3),
        rotor_inertia_kg_m2=round(rotor_inertia, 5),
        spinup_factor_percent=round(spinup_factor * 100.0, 2),
        required_startup_torque_n_m=round(required_startup_torque, 4),
        design_score=design_score(
            inputs=inputs.model_copy(update={"blade_mass_kg": effective_blade_mass}),
            cp=cp,
            tip_speed_ratio=tsr,
            material_durability=material_durability,
        ),
        generator_rpm=round(generator.generator_rpm, 2),
        unloaded_generator_rpm=round(generator.unloaded_generator_rpm, 2),
        generator_load_factor=round(generator.generator_load_factor, 4),
        open_circuit_voltage_v=round(generator.open_circuit_voltage_v, 4),
        load_voltage_v=round(generator.load_voltage_v, 4),
        load_current_ma=round(generator.load_current_ma, 4),
        electrical_power_mw=round(generator.electrical_power_mw, 4),
        electrical_energy_mj=round(generator.electrical_energy_mj, 4),
        conversion_efficiency_percent=round(generator.conversion_efficiency_percent, 2),
        airfoil_lift_coefficient=airfoil.lift_coefficient,
        airfoil_drag_coefficient=airfoil.drag_coefficient,
        airfoil_lift_drag_ratio=airfoil.lift_drag_ratio,
        airfoil_efficiency_factor=round(effective_airfoil_efficiency, 3),
        airfoil_angle_of_attack_deg=round(angle_of_attack, 2),
        airfoil_reynolds_number=round(reynolds_number, 0),
        airfoil_stall_risk=airfoil.stall_risk,
        representative_airfoil_name=(
            airfoil.representative_airfoil_name
            if inputs.blade_sections
            else geometry.representative_airfoil_name
        ),
        representative_airfoil_family=effective_airfoil_type,
        recommendations=build_recommendations(
            inputs,
            cp,
            tsr,
            representative_twist_deg=geometry.representative_twist_deg,
            airfoil_stall_risk=airfoil.stall_risk,
            airfoil_efficiency_factor=effective_airfoil_efficiency,
        ),
        warnings=tuple(warnings),
    )


def performance_curve(
    inputs: SimulationInput,
    wind_speeds: Iterable[float],
) -> list[dict[str, float]]:
    """Simulate one design across several wind speeds."""

    rows: list[dict[str, float]] = []
    for speed in wind_speeds:
        point_input = inputs.model_copy(update={"wind_speed_m_s": float(speed)})
        result = simulate(point_input)
        rows.append(
            {
                "Wind speed (m/s)": float(speed),
                "RPM": result.rpm,
                "Torque (N·m)": result.torque_n_m,
                "Power (W)": result.mechanical_power_w,
                "Electrical power (mW)": result.electrical_power_mw,
            }
        )
    return rows


def result_as_json(inputs: SimulationInput, result: SimulationResult) -> str:
    """Serialize inputs and results for download."""

    payload = {"inputs": inputs.model_dump(), "results": result.model_dump()}
    return json.dumps(payload, indent=2, ensure_ascii=False)


def result_as_csv(inputs: SimulationInput, result: SimulationResult) -> str:
    """Serialize a flat one-row result for spreadsheet use."""

    row = {**inputs.model_dump(), **result.model_dump(exclude={"recommendations", "warnings"})}
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(row))
    writer.writeheader()
    writer.writerow(row)
    return output.getvalue()


def result_as_design_sheet(inputs: SimulationInput, result: SimulationResult) -> str:
    """Serialize a student-facing printable design sheet as Markdown."""

    lines = [
        "# Wind Turbine Design Sheet",
        "",
        "## Competition estimate",
        "",
        f"- Competition power: {result.electrical_power_mw:.4f} mW",
        f"- Rotor speed: {result.rpm:.2f} RPM",
        f"- Torque: {result.torque_n_m:.3f} N·m",
        f"- Mechanical power: {result.mechanical_power_w:.3f} W",
        f"- Cp: {result.cp:.4f}",
        f"- Tip-speed ratio: {result.tip_speed_ratio:.3f}",
        f"- Spin-up factor: {result.spinup_factor_percent:.2f}%",
        f"- Design score: {result.design_score:.1f}/100",
        "",
        "## Build inputs",
        "",
        f"- Wind speed: {inputs.wind_speed_m_s:.2f} m/s",
        f"- Rotor radius / blade length: {inputs.rotor_radius_m:.3f} m",
        f"- Hub radius: {inputs.hub_radius_m:.3f} m",
        f"- Number of blades: {inputs.blade_count}",
        f"- Whole-blade pitch: {inputs.pitch_angle_deg:.1f}°",
        f"- Material: {inputs.material}",
        f"- Surface finish: {inputs.surface_finish}",
        f"- Blade mass: {result.effective_blade_mass_kg:.4f} kg",
        f"- Generator voltage constant: {inputs.generator_volts_per_1000_rpm:.3f} V/1000 RPM",
        f"- Generator internal resistance: {inputs.generator_internal_resistance_ohm:.3f} Ω",
        f"- Load resistance: {inputs.load_resistance_ohm:.3f} Ω",
        f"- Trial duration: {inputs.trial_duration_s:.1f} s",
        "",
    ]

    if inputs.blade_sections:
        lines.extend(
            [
                "## Blade section table",
                "",
                "| Section | Position (cm) | Chord (cm) | Twist (deg) | Airfoil | Role |",
                "|---:|---:|---:|---:|---|---|",
            ]
        )
        for index, section in enumerate(inputs.blade_sections, start=1):
            section_label = (
                "1 (Root)"
                if index == 1
                else f"{index} (Tip)"
                if index == len(inputs.blade_sections)
                else str(index)
            )
            lines.append(
                "| "
                f"{section_label} | "
                f"{section.position_m * 100.0:.1f} | "
                f"{section.chord_m * 100.0:.1f} | "
                f"{section.twist_angle_deg:.1f} | "
                f"{section.airfoil_name} | "
                f"{section.airfoil_role} |"
            )
        lines.append("")
    else:
        lines.extend(
            [
                "## Simple blade geometry",
                "",
                f"- Root chord: {inputs.root_chord_m:.3f} m",
                f"- Tip chord: {inputs.tip_chord_m:.3f} m",
                f"- Twist: {inputs.twist_angle_deg:.1f}°",
                f"- Airfoil family: {inputs.airfoil_type}",
                "",
            ]
        )

    lines.extend(
        [
            "## Notes and recommendations",
            "",
            *[f"- {recommendation}" for recommendation in result.recommendations],
            "",
            "## Model warning",
            "",
            "This sheet is generated by an educational simulator. Use measured wind-tunnel "
            "or competition data as the final judge.",
        ]
    )
    if result.warnings:
        lines.extend(["", "## Active warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)

    return "\n".join(lines) + "\n"
