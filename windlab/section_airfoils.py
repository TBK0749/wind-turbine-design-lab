"""Section-level airfoil choices for blade geometry tables."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SectionAirfoil:
    """Metadata for an airfoil that can be assigned to one blade station."""

    name: str
    family: str
    role: str
    thickness_percent: float | None = None


SECTION_AIRFOILS: dict[str, SectionAirfoil] = {
    "NACA 4418": SectionAirfoil(
        name="NACA 4418",
        family="High-lift airfoil",
        role=("Root strength and startup torque: thick 18% section for stiffness near the hub."),
        thickness_percent=18.0,
    ),
    "NACA 4415": SectionAirfoil(
        name="NACA 4415",
        family="High-lift airfoil",
        role="Transition section: reduces thickness while keeping strong cambered lift.",
        thickness_percent=15.0,
    ),
    "NACA 4412": SectionAirfoil(
        name="NACA 4412",
        family="High-lift airfoil",
        role="Primary lift section: cambered profile for strong classroom-scale lift.",
        thickness_percent=12.0,
    ),
    "NACA 2415": SectionAirfoil(
        name="NACA 2415",
        family="Cambered plate",
        role="Durable mid-span cambered section with moderate thickness.",
        thickness_percent=15.0,
    ),
    "NACA 2412": SectionAirfoil(
        name="NACA 2412",
        family="Cambered plate",
        role="Fast outer-blade section: thinner cambered profile to reduce drag and Tip vortex.",
        thickness_percent=12.0,
    ),
    "NACA 0018": SectionAirfoil(
        name="NACA 0018",
        family="Symmetric airfoil",
        role="Thick symmetric root option for strength when camber is not desired.",
        thickness_percent=18.0,
    ),
    "NACA 0015": SectionAirfoil(
        name="NACA 0015",
        family="Symmetric airfoil",
        role="Balanced symmetric transition option with moderate thickness.",
        thickness_percent=15.0,
    ),
    "NACA 0012": SectionAirfoil(
        name="NACA 0012",
        family="Symmetric airfoil",
        role="Predictable symmetric outer section that needs positive pitch for lift.",
        thickness_percent=12.0,
    ),
    "Clark Y": SectionAirfoil(
        name="Clark Y",
        family="Cambered plate",
        role="Flat-bottom cambered section, easy to fabricate and align.",
    ),
    "Selig S1223": SectionAirfoil(
        name="Selig S1223",
        family="High-lift airfoil",
        role="Very high-lift low-speed option; useful for experiments but sensitive to stall.",
    ),
    "Flat plate": SectionAirfoil(
        name="Flat plate",
        family="Flat plate / Foam board",
        role="Simple build option with high drag but easy classroom fabrication.",
    ),
}


def section_airfoil_options() -> list[str]:
    """Return airfoil names in student-facing order."""

    return list(SECTION_AIRFOILS)


def get_section_airfoil(name: str) -> SectionAirfoil:
    """Return a section airfoil or raise a friendly error."""

    try:
        return SECTION_AIRFOILS[name]
    except KeyError as exc:
        choices = ", ".join(SECTION_AIRFOILS)
        raise ValueError(f"Section airfoil must be one of: {choices}.") from exc
