"""BEMT-lite section-force model for classroom wind-turbine comparisons."""

from dataclasses import dataclass
from math import atan2, cos, degrees, radians, sin, sqrt

from windlab.airfoils import estimate_airfoil_performance
from windlab.models import SimulationInput
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
    warnings: tuple[str, ...]


def _interpolate(start: float, end: float, fraction: float) -> float:
    """Linearly interpolate between two station values."""

    return start + (end - start) * fraction


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
) -> BemtLiteResult:
    """Calculate simplified torque and power by summing blade sections.

    This intentionally stays lighter than full QBlade/BEMT. It uses each blade
    segment's radius, chord, twist, airfoil family, and relative wind speed, but
    does not solve induction factors iteratively.
    """

    if not inputs.blade_sections:
        return BemtLiteResult(
            mechanical_power_w=0.0,
            torque_n_m=0.0,
            cp=0.0,
            section_count=0,
            mean_relative_wind_speed_m_s=inputs.wind_speed_m_s,
            mean_angle_of_attack_deg=0.0,
            warnings=("BEMT-lite requires section-table blade geometry.",),
        )

    omega = angular_speed(tip_speed_ratio, inputs.wind_speed_m_s, inputs.rotor_radius_m)
    torque = 0.0
    relative_speed_sum = 0.0
    angle_sum = 0.0
    section_count = 0
    warnings: list[str] = []

    for inner, outer in zip(inputs.blade_sections, inputs.blade_sections[1:], strict=False):
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

        tangential_speed = omega * radius
        relative_speed = sqrt(inputs.wind_speed_m_s**2 + tangential_speed**2)
        inflow_angle_deg = degrees(atan2(inputs.wind_speed_m_s, max(tangential_speed, 1e-9)))
        angle_of_attack_deg = inflow_angle_deg - (inputs.pitch_angle_deg + twist)
        reynolds_number = (
            inputs.air_density_kg_m3 * relative_speed * chord / inputs.air_dynamic_viscosity_kg_m_s
        )
        performance = estimate_airfoil_performance(
            airfoil.family,
            angle_of_attack_deg=angle_of_attack_deg,
            reynolds_number=reynolds_number if use_reynolds_correction else 200_000.0,
        )
        efficiency_factor = (
            performance.efficiency_factor * airfoil_efficiency_multiplier
            if use_airfoil_correction
            else 1.0
        )
        cl = performance.lift_coefficient * efficiency_factor
        cd = performance.drag_coefficient / max(efficiency_factor, 0.35)

        dynamic_pressure = 0.5 * inputs.air_density_kg_m3 * relative_speed**2
        lift = dynamic_pressure * chord * radial_width * cl
        drag = dynamic_pressure * chord * radial_width * cd
        phi = radians(inflow_angle_deg)
        tangential_force = lift * sin(phi) - drag * cos(phi)
        torque += max(0.0, tangential_force * radius * inputs.blade_count)

        relative_speed_sum += relative_speed
        angle_sum += angle_of_attack_deg
        section_count += 1
        warnings.extend(performance.warnings)

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
        warnings=tuple(dict.fromkeys(warnings)),
    )
