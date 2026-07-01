"""Competition-oriented blade geometry presets for a one-metre rotor limit."""

from __future__ import annotations

from dataclasses import dataclass

from windlab.models import BladeSection, SimulationInput
from windlab.section_airfoils import get_section_airfoil


@dataclass(frozen=True, slots=True)
class BladePreset:
    """A student-facing blade table that can be loaded into the simulator."""

    name: str
    description: str
    tradeoffs: tuple[str, ...]
    sections: tuple[BladeSection, ...]
    wind_speed_m_s: float = 3.6
    rotor_radius_m: float = 0.50
    hub_radius_m: float = 0.10
    blade_count: int = 3


def _section(
    position_cm: float,
    chord_cm: float,
    twist_angle_deg: float,
    airfoil_name: str,
) -> BladeSection:
    """Create a blade section from classroom centimetre measurements."""

    airfoil = get_section_airfoil(airfoil_name)
    return BladeSection(
        position_m=position_cm / 100.0,
        chord_m=chord_cm / 100.0,
        twist_angle_deg=twist_angle_deg,
        airfoil_name=airfoil.name,
        airfoil_role=airfoil.role,
    )


_PRESETS: tuple[BladePreset, ...] = (
    BladePreset(
        name="Max Competition 45 cm",
        description=(
            "A 45 cm blade-length competition preset for a fixed 3.6 m/s classroom "
            "wind tunnel. It uses the best six-section result from the current "
            "educational model, with a strong NACA 4418 root and SG-series lift "
            "sections through the working span."
        ),
        tradeoffs=(
            "Recommended when the physical blade length must stay at or below 45 cm.",
            "Six sections make the Onshape rebuild faster while keeping the taper smooth.",
            "Slightly lower predicted mW than the 50 cm maximum-radius preset, but "
            "better matched to a 45 cm build limit.",
        ),
        sections=(
            _section(6.0, 11.00, 13.5, "NACA 4418"),
            _section(13.8, 9.51, 9.3, "SG6040"),
            _section(21.6, 8.00, 6.2, "SG6042"),
            _section(29.4, 6.47, 3.8, "SG6043"),
            _section(37.2, 4.89, 1.7, "SG6043"),
            _section(45.0, 3.20, 0.0, "SG6043"),
        ),
        rotor_radius_m=0.45,
    ),
    BladePreset(
        name="Max Competition 3.6 m/s",
        description=(
            "A 9-section competition-first preset tuned for a fixed 3.6 m/s classroom "
            "wind tunnel and a maximum 1 m rotor diameter. It keeps the root strong, "
            "uses smooth SG-series lift sections through most of the blade, and keeps "
            "the tip narrow enough for cleaner Onshape Lofting with 120 profile vertices."
        ),
        tradeoffs=(
            "Recommended starting point when the goal is maximum mW at 3.6 m/s.",
            "More aggressive than the low-wind classroom preset, so print quality "
            "and balance matter.",
            "Use this as the first serious competition candidate, then calibrate "
            "with real tunnel tests.",
        ),
        sections=(
            _section(6.0, 11.0, 18.0, "NACA 4418"),
            _section(10.0, 10.05, 14.7, "NACA 4418"),
            _section(15.7, 9.08, 11.7, "SG6040"),
            _section(21.4, 8.10, 8.9, "SG6042"),
            _section(27.1, 7.10, 6.4, "SG6043"),
            _section(32.9, 6.07, 4.1, "SG6043"),
            _section(38.6, 5.01, 2.2, "SG6043"),
            _section(44.3, 3.89, 0.8, "SG6043"),
            _section(50.0, 2.60, 0.0, "SG6043"),
        ),
    ),
    BladePreset(
        name="Balanced Competition 50 cm",
        description=(
            "A balanced three-blade starting point for a maximum 1 m rotor diameter. "
            "It uses eight smooth CAD stations, a thick root for strength, SG-series "
            "lift sections near mid-span, and a thinner low-drag tip."
        ),
        tradeoffs=(
            "Good first design for comparing changes one variable at a time.",
            "Not as aggressive for startup torque as the high-torque preset.",
            "Tip is slim enough for RPM without becoming extremely fragile.",
        ),
        sections=(
            _section(6.0, 9.0, 20.0, "NACA 4418"),
            _section(12.0, 8.2, 17.0, "NACA 4418"),
            _section(18.0, 7.2, 14.0, "SG6040"),
            _section(25.0, 6.0, 11.0, "SG6043"),
            _section(32.0, 4.8, 7.0, "SG6043"),
            _section(39.0, 3.6, 4.0, "NACA 2412"),
            _section(45.0, 2.6, 2.0, "NACA 2412"),
            _section(50.0, 1.8, 0.0, "E387"),
        ),
    ),
    BladePreset(
        name="High Starting Torque",
        description=(
            "A wider, higher-twist blade intended to start more easily in a low-speed "
            "classroom wind tunnel while keeping station-to-station Loft changes smooth."
        ),
        tradeoffs=(
            "Higher starting torque helps overcome generator cogging and bearing friction.",
            "Extra chord can increase drag after it reaches speed.",
            "Useful when the turbine struggles to self-start at 3.6 m/s.",
        ),
        sections=(
            _section(6.0, 10.5, 24.0, "NACA 4418"),
            _section(12.0, 9.7, 21.0, "NACA 4418"),
            _section(18.0, 8.7, 17.0, "SG6040"),
            _section(25.0, 7.3, 13.0, "SG6042"),
            _section(32.0, 5.8, 9.0, "SG6043"),
            _section(39.0, 4.4, 5.0, "SG6043"),
            _section(45.0, 3.0, 2.0, "NACA 2412"),
            _section(50.0, 2.0, 0.0, "E387"),
        ),
    ),
    BladePreset(
        name="High RPM / Low Drag Tip",
        description=(
            "A slimmer blade that gives up some starting torque to reduce drag near "
            "the fast-moving outer blade, with extra stations for cleaner CAD Lofting."
        ),
        tradeoffs=(
            "Can reach higher RPM when the generator load is not too heavy.",
            "May need a push-start or lower startup torque in the real rig.",
            "Good comparison design for testing how tip drag affects mW output.",
        ),
        sections=(
            _section(6.0, 8.0, 18.0, "NACA 4415"),
            _section(12.0, 7.3, 15.0, "NACA 4415"),
            _section(18.0, 6.4, 12.0, "SG6042"),
            _section(25.0, 5.2, 9.0, "SG6043"),
            _section(32.0, 4.1, 6.0, "NACA 2412"),
            _section(39.0, 3.0, 3.0, "NACA 2412"),
            _section(45.0, 2.2, 1.0, "E387"),
            _section(50.0, 1.5, 0.0, "E387"),
        ),
    ),
    BladePreset(
        name="Low Wind 3.6 m/s Classroom Tunnel",
        description=(
            "A low-wind design aimed specifically at a 3.6 m/s classroom wind tunnel. "
            "It uses eight smooth CAD stations and SG-series mid sections to make useful "
            "torque while staying easier to Loft than an aggressive high-lift profile."
        ),
        tradeoffs=(
            "Best first trial when the competition tunnel wind speed is fixed at 3.6 m/s.",
            "Smooth SG-series mid sections are easier to Loft than aggressive S1223 geometry.",
            "Prioritises useful torque over maximum no-load RPM.",
        ),
        sections=(
            _section(6.0, 9.5, 23.0, "NACA 4418"),
            _section(12.0, 8.7, 19.0, "NACA 4418"),
            _section(18.0, 7.6, 15.0, "SG6040"),
            _section(24.0, 6.5, 12.0, "SG6042"),
            _section(31.0, 5.3, 9.0, "SG6043"),
            _section(38.0, 4.1, 5.0, "SG6043"),
            _section(44.0, 2.8, 2.0, "SG6043"),
            _section(50.0, 1.9, 0.0, "NACA 2412"),
        ),
    ),
    BladePreset(
        name="Easy CAD / Easy Print",
        description=(
            "A practical build-first preset with easier airfoil families and moderate "
            "eight-station geometry for students who are new to CAD and 3D printing."
        ),
        tradeoffs=(
            "Easier to model, align, sand, and explain in an engineering notebook.",
            "Less optimised than the SG/S1223 low-wind presets.",
            "Good safe baseline when print quality or CAD time is the main constraint.",
        ),
        sections=(
            _section(6.0, 8.5, 18.0, "Clark Y"),
            _section(12.0, 7.7, 15.0, "Clark Y"),
            _section(18.0, 6.8, 12.0, "Clark Y"),
            _section(25.0, 5.6, 9.0, "NACA 2412"),
            _section(32.0, 4.5, 6.0, "NACA 2412"),
            _section(39.0, 3.4, 3.0, "NACA 2412"),
            _section(45.0, 2.5, 1.0, "E387"),
            _section(50.0, 1.8, 0.0, "E387"),
        ),
    ),
)


def blade_preset_options() -> tuple[BladePreset, ...]:
    """Return all student-facing one-metre competition presets."""

    return _PRESETS


def get_blade_preset(name: str) -> BladePreset:
    """Return a preset by stable display name."""

    for preset in _PRESETS:
        if preset.name == name:
            return preset
    choices = ", ".join(preset.name for preset in _PRESETS)
    raise ValueError(f"Blade preset must be one of: {choices}.")


def preset_to_simulation_input(preset: BladePreset) -> SimulationInput:
    """Convert a blade preset into a simulator input."""

    return SimulationInput(
        wind_speed_m_s=preset.wind_speed_m_s,
        rotor_radius_m=preset.rotor_radius_m,
        hub_radius_m=preset.hub_radius_m,
        blade_count=preset.blade_count,
        blade_sections=preset.sections,
        airfoil_type="High-lift airfoil",
    )
