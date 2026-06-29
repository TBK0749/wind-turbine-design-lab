"""Educational airfoil approximations for classroom wind-turbine design."""

from dataclasses import dataclass
from math import log10, radians


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


@dataclass(frozen=True)
class AirfoilPolarPoint:
    """One simplified polar sample for an airfoil at a Reynolds number and angle."""

    reynolds_number: float
    angle_of_attack_deg: float
    lift_coefficient: float
    drag_coefficient: float


@dataclass(frozen=True)
class AirfoilPolarEstimate:
    """Interpolated lift and drag coefficients from the simplified polar table."""

    airfoil_name: str
    lift_coefficient: float
    drag_coefficient: float


@dataclass(frozen=True)
class _PolarShape:
    """Parameters used to generate compact educational polar lookup tables."""

    zero_lift_angle_deg: float
    lift_slope_per_rad: float
    max_lift_coefficient: float
    base_drag_coefficient: float
    induced_drag_factor: float
    stall_angle_deg: float
    thickness_drag_factor: float
    low_re_lift_penalty: float
    low_re_drag_penalty: float


_POLAR_REYNOLDS_MODIFIERS: tuple[tuple[float, float, float, float], ...] = (
    # Reynolds number, lift factor, drag factor, max-lift factor.
    (10_000.0, 0.25, 3.20, 0.35),
    (25_000.0, 0.72, 1.85, 0.72),
    (50_000.0, 0.82, 1.45, 0.82),
    (100_000.0, 0.92, 1.18, 0.92),
    (200_000.0, 1.00, 1.00, 1.00),
    (500_000.0, 1.05, 0.88, 1.05),
)
_POLAR_ANGLE_POINTS: tuple[float, ...] = (-4.0, 0.0, 4.0, 8.0, 12.0, 16.0, 20.0)


_POLAR_SHAPES: dict[str, _PolarShape] = {
    "Flat plate": _PolarShape(0.0, 4.05, 0.86, 0.050, 0.060, 12.0, 1.18, 1.25, 1.30),
    "NACA 0012": _PolarShape(0.0, 5.35, 1.05, 0.018, 0.036, 13.0, 1.00, 0.90, 0.90),
    "NACA 0015": _PolarShape(0.0, 5.30, 1.03, 0.020, 0.038, 13.0, 1.08, 0.92, 0.94),
    "NACA 0018": _PolarShape(0.0, 5.20, 1.00, 0.023, 0.041, 12.5, 1.17, 0.95, 0.98),
    "NACA 2412": _PolarShape(-1.8, 5.20, 1.16, 0.017, 0.034, 14.0, 0.96, 0.76, 0.90),
    "NACA 2415": _PolarShape(-1.9, 5.15, 1.14, 0.019, 0.036, 14.0, 1.04, 0.78, 0.92),
    "NACA 4412": _PolarShape(-3.0, 5.35, 1.28, 0.018, 0.035, 15.0, 1.00, 0.65, 0.95),
    "NACA 4415": _PolarShape(-3.1, 5.30, 1.26, 0.021, 0.037, 14.5, 1.08, 0.68, 0.98),
    "NACA 4418": _PolarShape(-3.2, 5.20, 1.22, 0.024, 0.040, 14.0, 1.18, 0.72, 1.05),
    "Clark Y": _PolarShape(-2.2, 5.15, 1.15, 0.020, 0.036, 14.0, 1.02, 0.78, 0.80),
    "Selig S1223": _PolarShape(-5.0, 5.45, 1.55, 0.026, 0.045, 13.5, 1.12, 0.52, 0.88),
}

_AIRFOIL_POLAR_ALIASES: dict[str, str] = {
    "Flat plate / Foam board": "Flat plate",
    "Cambered plate": "NACA 2412",
    "Symmetric airfoil": "NACA 0012",
    "High-lift airfoil": "NACA 4412",
}


def _bounded_re_modifier(base_factor: float, penalty: float) -> float:
    """Apply an airfoil-specific low-Re sensitivity to a generic modifier."""

    if base_factor < 1.0:
        return max(0.45, 1.0 - (1.0 - base_factor) * penalty)
    return 1.0 + (base_factor - 1.0) * max(0.35, 1.0 / penalty)


def _polar_point_for_shape(
    shape: _PolarShape,
    *,
    reynolds_number: float,
    angle_of_attack_deg: float,
    lift_modifier: float,
    drag_modifier: float,
    max_lift_modifier: float,
) -> AirfoilPolarPoint:
    """Create one educational polar point from a compact section shape."""

    lift_factor = _bounded_re_modifier(lift_modifier, shape.low_re_lift_penalty)
    drag_factor = 1.0 + (drag_modifier - 1.0) * shape.low_re_drag_penalty
    max_lift_factor = _bounded_re_modifier(max_lift_modifier, shape.low_re_lift_penalty)
    effective_alpha_deg = angle_of_attack_deg - shape.zero_lift_angle_deg
    lift = shape.lift_slope_per_rad * radians(effective_alpha_deg) * lift_factor
    max_lift = shape.max_lift_coefficient * max_lift_factor
    lift = max(-max_lift, min(max_lift, lift))

    excess_angle = max(0.0, abs(angle_of_attack_deg) - shape.stall_angle_deg)
    if excess_angle:
        lift *= max(0.35, 1.0 - 0.08 * excess_angle)

    drag = (
        shape.base_drag_coefficient * drag_factor
        + shape.induced_drag_factor * lift**2
        + 0.0008 * abs(angle_of_attack_deg)
    ) * shape.thickness_drag_factor
    if excess_angle:
        drag *= 1.0 + 0.12 * excess_angle

    return AirfoilPolarPoint(
        reynolds_number=reynolds_number,
        angle_of_attack_deg=angle_of_attack_deg,
        lift_coefficient=round(lift, 4),
        drag_coefficient=round(drag, 5),
    )


def _build_polar_table(shape: _PolarShape) -> tuple[AirfoilPolarPoint, ...]:
    """Generate a compact polar lookup grid for one classroom airfoil."""

    points: list[AirfoilPolarPoint] = []
    for (
        reynolds_number,
        lift_modifier,
        drag_modifier,
        max_lift_modifier,
    ) in _POLAR_REYNOLDS_MODIFIERS:
        for angle in _POLAR_ANGLE_POINTS:
            points.append(
                _polar_point_for_shape(
                    shape,
                    reynolds_number=reynolds_number,
                    angle_of_attack_deg=angle,
                    lift_modifier=lift_modifier,
                    drag_modifier=drag_modifier,
                    max_lift_modifier=max_lift_modifier,
                )
            )
    return tuple(points)


AIRFOIL_POLAR_TABLES: dict[str, tuple[AirfoilPolarPoint, ...]] = {
    name: _build_polar_table(shape) for name, shape in _POLAR_SHAPES.items()
}


def _interpolate(x: float, x0: float, y0: float, x1: float, y1: float) -> float:
    """Linearly interpolate, clamping zero-width intervals."""

    if x1 == x0:
        return y0
    fraction = (x - x0) / (x1 - x0)
    return y0 + (y1 - y0) * fraction


def _interpolate_alpha(points: tuple[AirfoilPolarPoint, ...], angle: float) -> tuple[float, float]:
    """Interpolate lift and drag at one Reynolds-number row."""

    ordered = sorted(points, key=lambda point: point.angle_of_attack_deg)
    if angle <= ordered[0].angle_of_attack_deg:
        return ordered[0].lift_coefficient, ordered[0].drag_coefficient
    if angle >= ordered[-1].angle_of_attack_deg:
        return ordered[-1].lift_coefficient, ordered[-1].drag_coefficient

    for lower, upper in zip(ordered, ordered[1:], strict=False):
        if lower.angle_of_attack_deg <= angle <= upper.angle_of_attack_deg:
            lift = _interpolate(
                angle,
                lower.angle_of_attack_deg,
                lower.lift_coefficient,
                upper.angle_of_attack_deg,
                upper.lift_coefficient,
            )
            drag = _interpolate(
                angle,
                lower.angle_of_attack_deg,
                lower.drag_coefficient,
                upper.angle_of_attack_deg,
                upper.drag_coefficient,
            )
            return lift, drag

    return ordered[-1].lift_coefficient, ordered[-1].drag_coefficient


def _resolve_polar_name(airfoil_type: str, airfoil_name: str | None) -> str:
    """Resolve a family or section airfoil to the internal polar table name."""

    if airfoil_name is not None:
        if airfoil_name not in AIRFOIL_POLAR_TABLES:
            choices = ", ".join(AIRFOIL_POLAR_TABLES)
            raise ValueError(f"Airfoil polar must be one of: {choices}.")
        return airfoil_name
    return _AIRFOIL_POLAR_ALIASES[airfoil_type]


def lookup_airfoil_polar(
    airfoil_name: str,
    *,
    angle_of_attack_deg: float,
    reynolds_number: float,
) -> AirfoilPolarEstimate:
    """Interpolate a simplified CL/CD polar table by AoA and Reynolds number."""

    if airfoil_name not in AIRFOIL_POLAR_TABLES:
        choices = ", ".join(AIRFOIL_POLAR_TABLES)
        raise ValueError(f"Airfoil polar must be one of: {choices}.")

    table = AIRFOIL_POLAR_TABLES[airfoil_name]
    reynolds_rows = sorted({point.reynolds_number for point in table})
    lower_re = reynolds_rows[0]
    upper_re = reynolds_rows[-1]
    for index, row_re in enumerate(reynolds_rows):
        if reynolds_number <= row_re:
            upper_re = row_re
            lower_re = reynolds_rows[max(0, index - 1)]
            break

    lower_points = tuple(point for point in table if point.reynolds_number == lower_re)
    upper_points = tuple(point for point in table if point.reynolds_number == upper_re)
    lower_lift, lower_drag = _interpolate_alpha(lower_points, angle_of_attack_deg)
    upper_lift, upper_drag = _interpolate_alpha(upper_points, angle_of_attack_deg)

    safe_re = max(reynolds_number, reynolds_rows[0])
    if lower_re == upper_re:
        lift = lower_lift
        drag = lower_drag
    else:
        lift = _interpolate(
            log10(safe_re),
            log10(lower_re),
            lower_lift,
            log10(upper_re),
            upper_lift,
        )
        drag = _interpolate(
            log10(safe_re),
            log10(lower_re),
            lower_drag,
            log10(upper_re),
            upper_drag,
        )

    return AirfoilPolarEstimate(
        airfoil_name=airfoil_name,
        lift_coefficient=round(lift, 3),
        drag_coefficient=round(drag, 4),
    )


@dataclass(frozen=True)
class LowRePolarAdjustment:
    """Family-specific low-Reynolds correction inspired by simplified polar trends."""

    lift_factor: float
    drag_factor: float
    efficiency_factor: float
    warning: str | None = None


LOW_RE_POLAR_ADJUSTMENTS: dict[str, tuple[LowRePolarAdjustment, ...]] = {
    "Flat plate / Foam board": (
        LowRePolarAdjustment(
            0.62,
            2.05,
            0.58,
            "Very low Reynolds number: flat plates lose lift and create high drag.",
        ),
        LowRePolarAdjustment(
            0.72,
            1.70,
            0.68,
            "Low Reynolds number: flat plates may lose lift and see extra drag.",
        ),
        LowRePolarAdjustment(
            0.86,
            1.30,
            0.84,
            "Moderate-low Reynolds number: flat-plate performance is still penalized.",
        ),
    ),
    "Cambered plate": (
        LowRePolarAdjustment(
            0.78,
            1.55,
            0.78,
            "Very low Reynolds number: cambered sections keep some lift but add drag.",
        ),
        LowRePolarAdjustment(
            0.86,
            1.32,
            0.84,
            "Low Reynolds number: cambered sections are penalized but remain useful.",
        ),
        LowRePolarAdjustment(
            0.94,
            1.12,
            0.94,
            "Moderate-low Reynolds number: cambered-section performance is still penalized.",
        ),
    ),
    "Symmetric airfoil": (
        LowRePolarAdjustment(
            0.72,
            1.65,
            0.74,
            "Very low Reynolds number: symmetric airfoils need clean angle of attack.",
        ),
        LowRePolarAdjustment(
            0.82,
            1.38,
            0.82,
            "Low Reynolds number: symmetric airfoil performance is penalized.",
        ),
        LowRePolarAdjustment(
            0.92,
            1.14,
            0.92,
            "Moderate-low Reynolds number: symmetric-airfoil performance is still penalized.",
        ),
    ),
    "High-lift airfoil": (
        LowRePolarAdjustment(
            0.92,
            1.18,
            0.96,
            "Very low Reynolds number: high-lift polar uses apparent-speed correction.",
        ),
        LowRePolarAdjustment(
            0.78,
            1.45,
            0.82,
            "Low Reynolds number: high-lift airfoils keep useful lift but add drag.",
        ),
        LowRePolarAdjustment(
            0.88,
            1.25,
            0.91,
            "Moderate-low Reynolds number: high-lift airfoil performance is still penalized.",
        ),
        LowRePolarAdjustment(
            0.95,
            1.10,
            1.00,
            "Recovering Reynolds number: high-lift polar performance is improving.",
        ),
    ),
}


def _reynolds_adjustment(
    airfoil_type: str,
    reynolds_number: float,
) -> tuple[float, float, float, tuple[str, ...]]:
    """Return lift, drag, and efficiency multipliers for low-Reynolds operation."""

    if reynolds_number < 30_000.0:
        adjustment = LOW_RE_POLAR_ADJUSTMENTS[airfoil_type][0]
    elif (
        airfoil_type == "High-lift airfoil"
        and reynolds_number >= 50_000.0
        and reynolds_number < 80_000.0
    ):
        adjustment = LOW_RE_POLAR_ADJUSTMENTS[airfoil_type][3]
    elif reynolds_number < 80_000.0:
        adjustment = LOW_RE_POLAR_ADJUSTMENTS[airfoil_type][1]
    elif reynolds_number < 150_000.0:
        adjustment = LOW_RE_POLAR_ADJUSTMENTS[airfoil_type][2]
    elif reynolds_number > 500_000.0:
        return (1.03, 0.95, 1.03, ())
    else:
        return (1.0, 1.0, 1.0, ())

    warnings = (adjustment.warning,) if adjustment.warning else ()
    return (
        adjustment.lift_factor,
        adjustment.drag_factor,
        adjustment.efficiency_factor,
        warnings,
    )


def estimate_airfoil_performance(
    airfoil_type: str,
    *,
    airfoil_name: str | None = None,
    angle_of_attack_deg: float,
    reynolds_number: float,
) -> AirfoilPerformance:
    """Estimate educational lift/drag behavior for a selected airfoil."""

    if airfoil_type not in AIRFOIL_LIBRARY:
        raise ValueError(f"Airfoil must be one of: {', '.join(AIRFOIL_LIBRARY)}.")

    definition = AIRFOIL_LIBRARY[airfoil_type]
    excess_angle = max(0.0, abs(angle_of_attack_deg) - definition.stall_angle_deg)
    stall_risk = excess_angle > 0.0
    stall_factor = max(0.45, 1.0 - 0.06 * excess_angle)
    warnings: list[str] = []

    polar_name = _resolve_polar_name(airfoil_type, airfoil_name)
    polar = lookup_airfoil_polar(
        polar_name,
        angle_of_attack_deg=angle_of_attack_deg,
        reynolds_number=reynolds_number,
    )
    lift = polar.lift_coefficient
    drag = polar.drag_coefficient
    _, _, _, reynolds_warnings = _reynolds_adjustment(airfoil_type, reynolds_number)
    warnings.extend(reynolds_warnings)
    if stall_risk:
        warnings.append("High angle of attack: likely stall and extra drag.")

    lift_drag_ratio = abs(lift) / max(drag, 0.001)
    efficiency_factor = definition.efficiency_bias * (
        0.72 + min(lift_drag_ratio, 25.0) / 25.0 * 0.35
    )
    efficiency_factor *= stall_factor
    efficiency_factor = max(0.45, min(1.12, efficiency_factor))

    return AirfoilPerformance(
        lift_coefficient=round(lift, 3),
        drag_coefficient=round(drag, 4),
        lift_drag_ratio=round(lift_drag_ratio, 2),
        efficiency_factor=round(efficiency_factor, 3),
        stall_risk=stall_risk,
        warnings=tuple(warnings),
    )
