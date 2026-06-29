"""BEMT-lite section-force model for classroom wind-turbine comparisons."""

from dataclasses import dataclass
from math import acos, atan2, cos, degrees, exp, pi, radians, sin, sqrt

from windlab.airfoils import estimate_airfoil_performance
from windlab.models import BladeSection, SimulationInput
from windlab.physics import (
    BETZ_LIMIT,
    PRACTICAL_CP_LIMIT,
    angular_speed,
    available_wind_power,
    rotor_swept_area,
)
from windlab.section_airfoils import get_section_airfoil


@dataclass(frozen=True, slots=True)
class BemtLiteResult:
    """Aggregated BEMT-lite output."""

    mechanical_power_w: float
    torque_n_m: float
    cp: float
    section_count: int
    mean_relative_wind_speed_m_s: float
    mean_angle_of_attack_deg: float
    mean_prandtl_loss_factor: float
    mean_axial_induction_factor: float
    mean_tangential_induction_factor: float
    warnings: tuple[str, ...]


def _interpolate(start: float, end: float, fraction: float) -> float:
    """Linearly interpolate between two station values."""

    return start + (end - start) * fraction


def _clamp(value: float, lower: float, upper: float) -> float:
    """Clamp a value into a safe numerical range."""

    return max(lower, min(upper, value))


def _simple_airfoil_name(airfoil_type: str) -> str:
    """Map whole-blade classroom airfoil families to section-airfoil names."""

    return {
        "Flat plate / Foam board": "Flat plate",
        "Cambered plate": "NACA 2412",
        "Symmetric airfoil": "NACA 0012",
        "High-lift airfoil": "NACA 4412",
    }[airfoil_type]


def _bemt_sections(inputs: SimulationInput) -> tuple[BladeSection, ...]:
    """Return measured sections or synthesize stations from root/tip inputs."""

    if inputs.blade_sections:
        return inputs.blade_sections

    active_span = inputs.rotor_radius_m - inputs.hub_radius_m
    airfoil_name = _simple_airfoil_name(inputs.airfoil_type)
    fractions = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
    return tuple(
        BladeSection(
            position_m=max(0.001, inputs.hub_radius_m + active_span * fraction),
            chord_m=_interpolate(inputs.root_chord_m, inputs.tip_chord_m, fraction),
            twist_angle_deg=_interpolate(
                inputs.twist_angle_deg,
                max(0.0, inputs.twist_angle_deg * 0.25),
                fraction,
            ),
            airfoil_name=airfoil_name,
            airfoil_role="Synthetic BEMT-lite station from simple root/tip geometry.",
        )
        for fraction in fractions
    )


def _prandtl_loss_factor(
    *,
    blade_count: int,
    radius_m: float,
    hub_radius_m: float,
    rotor_radius_m: float,
    inflow_angle_rad: float,
) -> float:
    """Approximate Prandtl tip/root loss factor for BEM-style section forces."""

    sin_phi = max(abs(sin(inflow_angle_rad)), 1e-4)

    def loss(distance_m: float, denominator_radius_m: float) -> float:
        if distance_m <= 0.0:
            return 0.05
        exponent = -blade_count * distance_m / (2.0 * max(denominator_radius_m, 1e-6) * sin_phi)
        return 2.0 / pi * acos(max(0.0, min(1.0, exp(exponent))))

    tip_loss = loss(rotor_radius_m - radius_m, radius_m)
    root_loss = loss(radius_m - hub_radius_m, max(hub_radius_m, 1e-6))
    return max(0.05, min(1.0, tip_loss * root_loss))


def calculate_bemt_lite(
    inputs: SimulationInput,
    *,
    tip_speed_ratio: float,
    material_roughness_factor: float = 1.0,
    airfoil_efficiency_multiplier: float = 1.0,
    use_airfoil_correction: bool = True,
    use_reynolds_correction: bool = True,
    practical_cp_limit: float = PRACTICAL_CP_LIMIT,
    use_practical_cp_limit: bool = True,
    use_prandtl_loss: bool = True,
) -> BemtLiteResult:
    """Calculate simplified torque and power by summing blade sections.

    This intentionally stays lighter than full QBlade/BEMT. It uses each blade
    segment's radius, chord, twist, airfoil family, and relative wind speed, but
    does not solve induction factors iteratively.
    """

    sections = _bemt_sections(inputs)
    if len(sections) < 2:
        return BemtLiteResult(
            mechanical_power_w=0.0,
            torque_n_m=0.0,
            cp=0.0,
            section_count=0,
            mean_relative_wind_speed_m_s=inputs.wind_speed_m_s,
            mean_angle_of_attack_deg=0.0,
            mean_prandtl_loss_factor=1.0,
            mean_axial_induction_factor=0.0,
            mean_tangential_induction_factor=0.0,
            warnings=("BEMT-lite requires section-table blade geometry.",),
        )

    omega = angular_speed(tip_speed_ratio, inputs.wind_speed_m_s, inputs.rotor_radius_m)
    torque = 0.0
    relative_speed_sum = 0.0
    angle_sum = 0.0
    loss_sum = 0.0
    axial_induction_sum = 0.0
    tangential_induction_sum = 0.0
    section_count = 0
    warnings: list[str] = []

    for inner, outer in zip(sections, sections[1:], strict=False):
        segment_start = max(inner.position_m, inputs.hub_radius_m)
        segment_end = min(outer.position_m, inputs.rotor_radius_m)
        radial_width = segment_end - segment_start
        if radial_width <= 0.0:
            continue

        fraction = (
            0.0
            if outer.position_m == inner.position_m
            else (segment_start + radial_width / 2.0 - inner.position_m)
            / (outer.position_m - inner.position_m)
        )
        radius = segment_start + radial_width / 2.0
        chord = _interpolate(inner.chord_m, outer.chord_m, fraction)
        twist = _interpolate(inner.twist_angle_deg, outer.twist_angle_deg, fraction)
        airfoil_name = outer.airfoil_name if fraction >= 0.5 else inner.airfoil_name
        airfoil = get_section_airfoil(airfoil_name)

        local_solidity = inputs.blade_count * chord / (2.0 * pi * max(radius, 1e-6))
        axial_induction = 0.10
        tangential_induction = 0.0
        relative_speed = inputs.wind_speed_m_s
        angle_of_attack_deg = 0.0
        phi = radians(10.0)
        loss_factor = 1.0
        performance_warnings: tuple[str, ...] = ()
        cl = 0.0
        cd = 0.0

        for _ in range(35):
            axial_speed = inputs.wind_speed_m_s * (1.0 - axial_induction)
            tangential_speed = omega * radius * (1.0 + tangential_induction)
            relative_speed = sqrt(axial_speed**2 + tangential_speed**2)
            phi = atan2(max(axial_speed, 1e-6), max(tangential_speed, 1e-9))
            phi = _clamp(phi, radians(2.0), radians(88.0))
            inflow_angle_deg = degrees(phi)
            angle_of_attack_deg = inflow_angle_deg - (inputs.pitch_angle_deg + twist)
            reynolds_number = (
                inputs.air_density_kg_m3
                * relative_speed
                * chord
                / inputs.air_dynamic_viscosity_kg_m_s
            )
            performance = estimate_airfoil_performance(
                airfoil.family,
                angle_of_attack_deg=angle_of_attack_deg,
                reynolds_number=reynolds_number if use_reynolds_correction else 200_000.0,
            )
            performance_warnings = performance.warnings
            efficiency_factor = (
                performance.efficiency_factor * airfoil_efficiency_multiplier
                if use_airfoil_correction
                else 1.0
            )
            cl = performance.lift_coefficient * efficiency_factor
            cd = performance.drag_coefficient / max(efficiency_factor, 0.35)
            loss_factor = (
                _prandtl_loss_factor(
                    blade_count=inputs.blade_count,
                    radius_m=radius,
                    hub_radius_m=inputs.hub_radius_m,
                    rotor_radius_m=inputs.rotor_radius_m,
                    inflow_angle_rad=phi,
                )
                if use_prandtl_loss
                else 1.0
            )
            normal_force_coefficient = cl * cos(phi) + cd * sin(phi)
            tangential_force_coefficient = cl * sin(phi) - cd * cos(phi)

            if normal_force_coefficient <= 1e-6:
                new_axial_induction = 0.0
            else:
                axial_denominator = (
                    4.0
                    * loss_factor
                    * sin(phi) ** 2
                    / max(local_solidity * normal_force_coefficient, 1e-9)
                    + 1.0
                )
                new_axial_induction = 1.0 / max(axial_denominator, 1e-9)
            if abs(tangential_force_coefficient) <= 1e-6:
                new_tangential_induction = 0.0
            else:
                tangential_denominator = (
                    4.0
                    * loss_factor
                    * sin(phi)
                    * cos(phi)
                    / max(local_solidity * tangential_force_coefficient, 1e-9)
                    - 1.0
                )
                new_tangential_induction = 1.0 / max(tangential_denominator, 1e-9)

            new_axial_induction = _clamp(new_axial_induction, 0.0, 0.45)
            new_tangential_induction = _clamp(new_tangential_induction, -0.15, 0.45)
            relaxed_axial = 0.65 * axial_induction + 0.35 * new_axial_induction
            relaxed_tangential = 0.65 * tangential_induction + 0.35 * new_tangential_induction
            if (
                abs(relaxed_axial - axial_induction) < 1e-4
                and abs(relaxed_tangential - tangential_induction) < 1e-4
            ):
                axial_induction = relaxed_axial
                tangential_induction = relaxed_tangential
                break
            axial_induction = relaxed_axial
            tangential_induction = relaxed_tangential

        dynamic_pressure = 0.5 * inputs.air_density_kg_m3 * relative_speed**2
        lift = dynamic_pressure * chord * radial_width * cl
        drag = dynamic_pressure * chord * radial_width * cd
        tangential_force = lift * sin(phi) - drag * cos(phi)
        torque += max(0.0, tangential_force * loss_factor * radius * inputs.blade_count)

        relative_speed_sum += relative_speed
        angle_sum += angle_of_attack_deg
        loss_sum += loss_factor
        axial_induction_sum += axial_induction
        tangential_induction_sum += tangential_induction
        section_count += 1
        warnings.extend(performance_warnings)

    mechanical_power = torque * omega * material_roughness_factor
    area = rotor_swept_area(inputs.rotor_radius_m, inputs.hub_radius_m)
    wind_power = available_wind_power(inputs.air_density_kg_m3, area, inputs.wind_speed_m_s)
    cp = mechanical_power / wind_power if wind_power > 0.0 else 0.0
    cp_limit = min(BETZ_LIMIT - 1e-6, practical_cp_limit if use_practical_cp_limit else BETZ_LIMIT)
    if cp > cp_limit:
        scale = cp_limit / cp
        cp = cp_limit
        mechanical_power *= scale
        torque *= scale

    return BemtLiteResult(
        mechanical_power_w=mechanical_power,
        torque_n_m=torque,
        cp=cp,
        section_count=section_count,
        mean_relative_wind_speed_m_s=(
            relative_speed_sum / section_count if section_count else inputs.wind_speed_m_s
        ),
        mean_angle_of_attack_deg=angle_sum / section_count if section_count else 0.0,
        mean_prandtl_loss_factor=loss_sum / section_count if section_count else 1.0,
        mean_axial_induction_factor=axial_induction_sum / section_count if section_count else 0.0,
        mean_tangential_induction_factor=(
            tangential_induction_sum / section_count if section_count else 0.0
        ),
        warnings=tuple(dict.fromkeys(warnings)),
    )
