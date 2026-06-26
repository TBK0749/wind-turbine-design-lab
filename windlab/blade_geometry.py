"""Utilities for working with blade geometry measured at radial stations."""

from dataclasses import dataclass

from windlab.models import BladeSection, SimulationInput
from windlab.section_airfoils import get_section_airfoil


@dataclass(frozen=True, slots=True)
class BladeGeometrySummary:
    """Representative values used by the simplified pre-BEMT model."""

    root_chord_m: float
    tip_chord_m: float
    mean_chord_m: float
    representative_twist_deg: float
    section_count: int
    representative_airfoil_name: str
    representative_airfoil_family: str


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
            representative_airfoil_name=inputs.airfoil_type,
            representative_airfoil_family=inputs.airfoil_type,
        )

    sections = inputs.blade_sections
    weighted_chord = 0.0
    weighted_twist = 0.0
    total_weight = 0.0
    representative_airfoil_name = sections[0].airfoil_name
    representative_airfoil_weight = -1.0

    for inner, outer in zip(sections, sections[1:], strict=False):
        segment_start = max(inner.position_m, inputs.hub_radius_m)
        segment_end = min(outer.position_m, inputs.rotor_radius_m)
        radial_width = segment_end - segment_start
        if radial_width <= 0.0:
            continue
        midpoint_radius = (segment_start + segment_end) / 2.0
        weight = radial_width * midpoint_radius
        mean_chord = (inner.chord_m + outer.chord_m) / 2.0
        weighted_chord += weight * mean_chord
        weighted_twist += weight * (inner.twist_angle_deg + outer.twist_angle_deg) / 2.0
        total_weight += weight
        airfoil_weight = weight * mean_chord
        if airfoil_weight > representative_airfoil_weight:
            representative_airfoil_name = outer.airfoil_name
            representative_airfoil_weight = airfoil_weight

    if total_weight <= 0.0:
        representative_airfoil = get_section_airfoil(representative_airfoil_name)
        return BladeGeometrySummary(
            root_chord_m=sections[0].chord_m,
            tip_chord_m=sections[-1].chord_m,
            mean_chord_m=(sections[0].chord_m + sections[-1].chord_m) / 2.0,
            representative_twist_deg=(sections[0].twist_angle_deg + sections[-1].twist_angle_deg)
            / 2.0,
            section_count=len(sections),
            representative_airfoil_name=representative_airfoil.name,
            representative_airfoil_family=representative_airfoil.family,
        )

    representative_airfoil = get_section_airfoil(representative_airfoil_name)

    return BladeGeometrySummary(
        root_chord_m=sections[0].chord_m,
        tip_chord_m=sections[-1].chord_m,
        mean_chord_m=weighted_chord / total_weight,
        representative_twist_deg=weighted_twist / total_weight,
        section_count=len(sections),
        representative_airfoil_name=representative_airfoil.name,
        representative_airfoil_family=representative_airfoil.family,
    )


def estimate_blade_planform_area(inputs: SimulationInput) -> float:
    """Estimate one blade's top-view area in square metres."""

    if not inputs.blade_sections:
        span = inputs.rotor_radius_m - inputs.hub_radius_m
        mean_chord = (inputs.root_chord_m + inputs.tip_chord_m) / 2.0
        return span * mean_chord

    sections = inputs.blade_sections
    area = 0.0
    for inner, outer in zip(sections, sections[1:], strict=False):
        segment_start = max(inner.position_m, inputs.hub_radius_m)
        segment_end = min(outer.position_m, inputs.rotor_radius_m)
        radial_width = segment_end - segment_start
        if radial_width <= 0.0:
            continue
        mean_chord = (inner.chord_m + outer.chord_m) / 2.0
        area += radial_width * mean_chord
    return area


def competition_50cm_sections() -> tuple[BladeSection, ...]:
    """Return the six-station geometry supplied for the competition blade."""

    values = (
        (
            0.05,
            0.085,
            20.0,
            "NACA 4418",
            "Root strength and startup torque: thick 18% section for stiffness near the hub.",
        ),
        (
            0.13,
            0.072,
            14.0,
            "NACA 4415",
            "Transition bridge: gradually reduces thickness for smoother airflow.",
        ),
        (
            0.21,
            0.056,
            9.0,
            "NACA 4412",
            "Primary Lift section: cambered profile extracts the main useful lift.",
        ),
        (
            0.29,
            0.042,
            5.0,
            "NACA 4412",
            "Primary Lift support: keeps torque delivery smooth toward the drive system.",
        ),
        (
            0.37,
            0.030,
            2.0,
            "NACA 2412",
            "Fast outer blade: thinner cambered section reduces drag at higher tip speed.",
        ),
        (
            0.45,
            0.018,
            0.0,
            "NACA 2412",
            "Tip vortex control: thin tip section cuts drag and reduces Tip vortex loss.",
        ),
    )
    return tuple(
        BladeSection(
            position_m=position,
            chord_m=chord,
            twist_angle_deg=twist,
            airfoil_name=airfoil,
            airfoil_role=role,
        )
        for position, chord, twist, airfoil, role in values
    )
