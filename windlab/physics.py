"""Simplified, bounded equations for the version 0.1 educational model."""

from math import exp, pi

BETZ_LIMIT = 16.0 / 27.0
PRACTICAL_CP_LIMIT = 0.50
MIN_ANGULAR_SPEED_RAD_S = 0.05


def rotor_swept_area(rotor_radius_m: float, hub_radius_m: float = 0.0) -> float:
    """Calculate annular rotor swept area in square metres."""

    return pi * (rotor_radius_m**2 - hub_radius_m**2)


def available_wind_power(
    air_density_kg_m3: float,
    area_m2: float,
    wind_speed_m_s: float,
) -> float:
    """Calculate kinetic power passing through the rotor area."""

    return 0.5 * air_density_kg_m3 * area_m2 * wind_speed_m_s**3


def estimate_tip_speed_ratio(
    blade_count: int,
    pitch_angle_deg: float,
    twist_angle_deg: float,
) -> float:
    """Estimate TSR from broad educational design trends.

    Fewer blades generally favor higher rotational speed. Moderate pitch and
    twist are rewarded, while large deviations reduce the estimate.
    """

    blade_term = 7.2 * (3.0 / blade_count) ** 0.35
    pitch_factor = exp(-(((pitch_angle_deg - 4.0) / 13.0) ** 2))
    twist_factor = exp(-(((twist_angle_deg - 12.0) / 24.0) ** 2))
    return min(12.0, max(1.0, blade_term * (0.60 + 0.20 * pitch_factor + 0.20 * twist_factor)))


def estimate_cp(
    *,
    tip_speed_ratio: float,
    blade_count: int,
    root_chord_m: float,
    tip_chord_m: float,
    rotor_radius_m: float,
    pitch_angle_deg: float,
    twist_angle_deg: float,
    roughness_factor: float,
    mean_chord_m: float | None = None,
) -> float:
    """Estimate a stable Cp for classroom comparison.

    This is intentionally not BEMT. It combines smooth penalties around useful
    educational ranges and clamps the result below practical and Betz limits.
    """

    tsr_factor = exp(-(((tip_speed_ratio - 7.0) / 3.8) ** 2))
    pitch_factor = exp(-(((pitch_angle_deg - 4.0) / 12.0) ** 2))
    twist_factor = exp(-(((twist_angle_deg - 12.0) / 22.0) ** 2))
    representative_chord = mean_chord_m or (root_chord_m + tip_chord_m) / 2.0
    solidity = blade_count * representative_chord / (pi * rotor_radius_m)
    solidity_factor = exp(-(((solidity - 0.09) / 0.10) ** 2))

    cp = (
        0.10
        + 0.19 * tsr_factor
        + 0.06 * pitch_factor
        + 0.05 * twist_factor
        + 0.05 * solidity_factor
    ) * roughness_factor
    return min(cp, PRACTICAL_CP_LIMIT, BETZ_LIMIT - 1e-6)


def angular_speed(tip_speed_ratio: float, wind_speed_m_s: float, rotor_radius_m: float) -> float:
    """Convert tip-speed ratio to angular speed in radians per second."""

    return tip_speed_ratio * wind_speed_m_s / rotor_radius_m


def rpm_from_angular_speed(angular_speed_rad_s: float) -> float:
    """Convert angular speed to revolutions per minute."""

    return angular_speed_rad_s * 60.0 / (2.0 * pi)


def torque_from_power(power_w: float, angular_speed_rad_s: float) -> float:
    """Calculate torque while preventing unstable division near zero."""

    return power_w / max(angular_speed_rad_s, MIN_ANGULAR_SPEED_RAD_S)
