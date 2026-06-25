"""Application-level simulation orchestration."""

import csv
import io
import json
from collections.abc import Iterable

from windlab.blade_geometry import summarize_blade_geometry
from windlab.generator import simulate_generator
from windlab.materials import get_material
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


def simulate(inputs: SimulationInput) -> SimulationResult:
    """Run one deterministic educational simulation."""

    material = get_material(inputs.material)
    geometry = summarize_blade_geometry(inputs)
    area = rotor_swept_area(inputs.rotor_radius_m, inputs.hub_radius_m)
    wind_power = available_wind_power(inputs.air_density_kg_m3, area, inputs.wind_speed_m_s)
    tsr = estimate_tip_speed_ratio(
        inputs.blade_count,
        inputs.pitch_angle_deg,
        geometry.representative_twist_deg,
    )
    cp = estimate_cp(
        tip_speed_ratio=tsr,
        blade_count=inputs.blade_count,
        root_chord_m=geometry.root_chord_m,
        tip_chord_m=geometry.tip_chord_m,
        rotor_radius_m=inputs.rotor_radius_m,
        pitch_angle_deg=inputs.pitch_angle_deg,
        twist_angle_deg=geometry.representative_twist_deg,
        roughness_factor=material.roughness_factor,
        mean_chord_m=geometry.mean_chord_m,
    )
    mechanical_power = cp * wind_power
    omega = angular_speed(tsr, inputs.wind_speed_m_s, inputs.rotor_radius_m)
    rpm = rpm_from_angular_speed(omega)
    torque = torque_from_power(mechanical_power, omega)
    generator = simulate_generator(
        rotor_rpm=rpm,
        mechanical_power_w=mechanical_power,
        volts_per_1000_rpm=inputs.generator_volts_per_1000_rpm,
        internal_resistance_ohm=inputs.generator_internal_resistance_ohm,
        load_resistance_ohm=inputs.load_resistance_ohm,
        efficiency_percent=inputs.generator_efficiency_percent,
        gear_ratio=inputs.gear_ratio,
        trial_duration_s=inputs.trial_duration_s,
    )

    warnings: list[str] = []
    if inputs.wind_speed_m_s > 25.0:
        warnings.append(
            "High wind speed: this model does not simulate structural or shutdown limits."
        )
    if inputs.rotor_radius_m > 10.0:
        warnings.append("Large rotor: simplified assumptions become increasingly unrealistic.")

    return SimulationResult(
        rotor_area_m2=round(area, 4),
        available_wind_power_w=round(wind_power, 3),
        mechanical_power_w=round(mechanical_power, 3),
        rpm=round(rpm, 2),
        torque_n_m=round(torque, 3),
        cp=round(cp, 4),
        tip_speed_ratio=round(tsr, 3),
        efficiency_percent=round(cp * 100.0, 2),
        design_score=design_score(
            inputs=inputs,
            cp=cp,
            tip_speed_ratio=tsr,
            material_durability=material.durability_factor,
        ),
        generator_rpm=round(generator.generator_rpm, 2),
        open_circuit_voltage_v=round(generator.open_circuit_voltage_v, 4),
        load_voltage_v=round(generator.load_voltage_v, 4),
        load_current_ma=round(generator.load_current_ma, 4),
        electrical_power_mw=round(generator.electrical_power_mw, 4),
        electrical_energy_mj=round(generator.electrical_energy_mj, 4),
        conversion_efficiency_percent=round(generator.conversion_efficiency_percent, 2),
        recommendations=build_recommendations(
            inputs,
            cp,
            tsr,
            representative_twist_deg=geometry.representative_twist_deg,
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
