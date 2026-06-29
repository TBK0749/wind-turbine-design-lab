"""Educational airfoil approximations for classroom wind-turbine design."""

from dataclasses import dataclass
from math import radians


@dataclass(frozen=True)
class AirfoilDefinition:
    """Tunable classroom constants for one airfoil family."""

    description: str
    lift_slope_per_rad: float
    zero_lift_angle_deg: float
    max_lift_coefficient: float
    base_drag_coefficient: float
    induced_drag_factor: float
    stall_angle_deg: float
    efficiency_bias: float


AIRFOIL_LIBRARY: dict[str, AirfoilDefinition] = {
    "Flat plate / Foam board": AirfoilDefinition(
        description="Simple flat sheet, easy to fabricate but draggy at higher angles.",
        lift_slope_per_rad=4.2,
        zero_lift_angle_deg=0.0,
        max_lift_coefficient=0.85,
        base_drag_coefficient=0.045,
        induced_drag_factor=0.055,
        stall_angle_deg=12.0,
        efficiency_bias=0.88,
    ),
    "Cambered plate": AirfoilDefinition(
        description="Lightly curved sheet that gives more lift at student-scale Reynolds numbers.",
        lift_slope_per_rad=4.8,
        zero_lift_angle_deg=-2.0,
        max_lift_coefficient=1.10,
        base_drag_coefficient=0.038,
        induced_drag_factor=0.045,
        stall_angle_deg=14.0,
        efficiency_bias=0.98,
    ),
    "Symmetric airfoil": AirfoilDefinition(
        description="Balanced airfoil such as NACA 0012; predictable but needs angle of attack.",
        lift_slope_per_rad=5.4,
        zero_lift_angle_deg=0.0,
        max_lift_coefficient=1.05,
        base_drag_coefficient=0.032,
        induced_drag_factor=0.038,
        stall_angle_deg=13.0,
        efficiency_bias=1.00,
    ),
    "High-lift airfoil": AirfoilDefinition(
        description=(
            "Cambered airfoil such as NACA 4412; strong low-speed lift but stalls if overpitched."
        ),
        lift_slope_per_rad=5.2,
        zero_lift_angle_deg=-3.0,
        max_lift_coefficient=1.25,
        base_drag_coefficient=0.034,
        induced_drag_factor=0.042,
        stall_angle_deg=15.0,
        efficiency_bias=1.06,
    ),
}


@dataclass(frozen=True)
class AirfoilPerformance:
    """Simplified aerodynamic result for one representative blade section."""

    lift_coefficient: float
    drag_coefficient: float
    lift_drag_ratio: float
    efficiency_factor: float
    stall_risk: bool
    warnings: tuple[str, ...] = ()


def _reynolds_adjustment(reynolds_number: float) -> tuple[float, float, float, tuple[str, ...]]:
    """Return lift, drag, and efficiency multipliers for low-Reynolds operation."""

    if reynolds_number < 30_000.0:
        return (
            0.65,
            1.90,
            0.62,
            ("Very low Reynolds number: expect reduced lift and much higher drag.",),
        )
    if reynolds_number < 80_000.0:
        return (
            0.78,
            1.45,
            0.78,
            ("Low Reynolds number: small blades may lose lift and see extra drag.",),
        )
    if reynolds_number < 150_000.0:
        return (
            0.90,
            1.20,
            0.90,
            ("Moderate-low Reynolds number: airfoil performance is still penalized.",),
        )
    if reynolds_number > 500_000.0:
        return (1.03, 0.95, 1.03, ())
    return (1.0, 1.0, 1.0, ())


def estimate_airfoil_performance(
    airfoil_type: str,
    *,
    angle_of_attack_deg: float,
    reynolds_number: float,
) -> AirfoilPerformance:
    """Estimate educational lift/drag behavior for a selected airfoil."""

    if airfoil_type not in AIRFOIL_LIBRARY:
        raise ValueError(f"Airfoil must be one of: {', '.join(AIRFOIL_LIBRARY)}.")

    definition = AIRFOIL_LIBRARY[airfoil_type]
    effective_alpha_deg = angle_of_attack_deg - definition.zero_lift_angle_deg
    lift = definition.lift_slope_per_rad * radians(effective_alpha_deg)
    lift = max(-definition.max_lift_coefficient, min(definition.max_lift_coefficient, lift))

    excess_angle = max(0.0, abs(angle_of_attack_deg) - definition.stall_angle_deg)
    stall_risk = excess_angle > 0.0
    stall_factor = max(0.45, 1.0 - 0.06 * excess_angle)
    if stall_risk:
        lift *= stall_factor

    lift_re_factor, drag_re_factor, efficiency_re_factor, reynolds_warnings = _reynolds_adjustment(
        reynolds_number
    )
    lift *= lift_re_factor
    warnings: list[str] = list(reynolds_warnings)

    drag = (
        definition.base_drag_coefficient
        + definition.induced_drag_factor * lift**2
        + 0.002 * abs(angle_of_attack_deg)
    ) * drag_re_factor
    if stall_risk:
        drag *= 1.0 + 0.10 * excess_angle
        warnings.append("High angle of attack: likely stall and extra drag.")

    lift_drag_ratio = abs(lift) / max(drag, 0.001)
    efficiency_factor = definition.efficiency_bias * (
        0.72 + min(lift_drag_ratio, 25.0) / 25.0 * 0.35
    )
    efficiency_factor *= efficiency_re_factor * stall_factor
    efficiency_factor = max(0.45, min(1.12, efficiency_factor))

    return AirfoilPerformance(
        lift_coefficient=round(lift, 3),
        drag_coefficient=round(drag, 4),
        lift_drag_ratio=round(lift_drag_ratio, 2),
        efficiency_factor=round(efficiency_factor, 3),
        stall_risk=stall_risk,
        warnings=tuple(warnings),
    )
