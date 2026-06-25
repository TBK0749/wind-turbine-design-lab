"""Utilities for working with blade geometry measured at radial stations."""

from dataclasses import dataclass

from windlab.models import BladeSection, SimulationInput


@dataclass(frozen=True, slots=True)
class BladeGeometrySummary:
    """Representative values used by the simplified pre-BEMT model."""

    root_chord_m: float
    tip_chord_m: float
    mean_chord_m: float
    representative_twist_deg: float
    section_count: int


def summarize_blade_geometry(inputs: SimulationInput) -> BladeGeometrySummary:
    """Summarize all blade stations using radial-area weighting.

    Stations farther from the hub receive more weight because they sweep more
    area and contribute more strongly to rotor speed and torque. This remains
    an educational approximation, not a Blade Element Momentum calculation.
    """

    if not inputs.blade_sections:
        return BladeGeometrySummary(
            root_chord_m=inputs.root_chord_m,
            tip_chord_m=inputs.tip_chord_m,
            mean_chord_m=(inputs.root_chord_m + inputs.tip_chord_m) / 2.0,
            representative_twist_deg=inputs.twist_angle_deg,
            section_count=2,
        )

    sections = inputs.blade_sections
    weighted_chord = 0.0
    weighted_twist = 0.0
    total_weight = 0.0

    for inner, outer in zip(sections, sections[1:], strict=False):
        radial_width = outer.position_m - inner.position_m
        midpoint_radius = (inner.position_m + outer.position_m) / 2.0
        weight = radial_width * midpoint_radius
        weighted_chord += weight * (inner.chord_m + outer.chord_m) / 2.0
        weighted_twist += weight * (inner.twist_angle_deg + outer.twist_angle_deg) / 2.0
        total_weight += weight

    return BladeGeometrySummary(
        root_chord_m=sections[0].chord_m,
        tip_chord_m=sections[-1].chord_m,
        mean_chord_m=weighted_chord / total_weight,
        representative_twist_deg=weighted_twist / total_weight,
        section_count=len(sections),
    )


def competition_50cm_sections() -> tuple[BladeSection, ...]:
    """Return the six-station geometry supplied for the competition blade."""

    values = (
        (0.05, 0.090, 20.0),
        (0.15, 0.075, 14.0),
        (0.25, 0.055, 9.0),
        (0.35, 0.040, 5.0),
        (0.45, 0.028, 2.0),
        (0.50, 0.020, 0.0),
    )
    return tuple(
        BladeSection(position_m=position, chord_m=chord, twist_angle_deg=twist)
        for position, chord, twist in values
    )
