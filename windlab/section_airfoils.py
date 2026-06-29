"""Section-level airfoil choices for blade geometry tables."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SectionAirfoil:
    """Metadata for an airfoil that can be assigned to one blade station."""

    name: str
    family: str
    role: str
    best_zone: str
    plain_language_summary: str
    thickness_percent: float | None = None
    camber_percent: float | None = None
    camber_position_percent: float | None = None
    camber_description: str = "Representative educational shape."
    recommended_reynolds_min: float = 30_000.0
    recommended_reynolds_max: float = 500_000.0
    confidence: str = "Estimated"
    source_note: str = "Educational approximation; not a measured field calibration."
    zone_warnings: tuple[str, ...] = ()


SECTION_AIRFOILS: dict[str, SectionAirfoil] = {
    "NACA 4418": SectionAirfoil(
        name="NACA 4418",
        family="High-lift airfoil",
        role=("Root strength and startup torque: thick 18% section for stiffness near the hub."),
        best_zone="Root",
        plain_language_summary="4% camber at 40% chord, 18% thick; strong root and startup torque.",
        thickness_percent=18.0,
        camber_percent=4.0,
        camber_position_percent=40.0,
    ),
    "NACA 4415": SectionAirfoil(
        name="NACA 4415",
        family="High-lift airfoil",
        role="Transition section: reduces thickness while keeping strong cambered lift.",
        best_zone="Root / Mid",
        plain_language_summary=(
            "4% camber at 40% chord, 15% thick; transition from root to lift zone."
        ),
        thickness_percent=15.0,
        camber_percent=4.0,
        camber_position_percent=40.0,
    ),
    "NACA 4412": SectionAirfoil(
        name="NACA 4412",
        family="High-lift airfoil",
        role="Primary lift section: cambered profile for strong classroom-scale lift.",
        best_zone="Mid",
        plain_language_summary="4% camber at 40% chord, 12% thick; main lift-producing section.",
        thickness_percent=12.0,
        camber_percent=4.0,
        camber_position_percent=40.0,
    ),
    "NACA 2415": SectionAirfoil(
        name="NACA 2415",
        family="Cambered plate",
        role="Durable mid-span cambered section with moderate thickness.",
        best_zone="Mid",
        plain_language_summary=(
            "2% camber at 40% chord, 15% thick; moderate lift with extra thickness."
        ),
        thickness_percent=15.0,
        camber_percent=2.0,
        camber_position_percent=40.0,
    ),
    "NACA 2412": SectionAirfoil(
        name="NACA 2412",
        family="Cambered plate",
        role="Fast outer-blade section: thinner cambered profile to reduce drag and Tip vortex.",
        best_zone="Tip",
        plain_language_summary=(
            "2% camber at 40% chord, 12% thick; good outer-blade low-drag option."
        ),
        thickness_percent=12.0,
        camber_percent=2.0,
        camber_position_percent=40.0,
    ),
    "NACA 0018": SectionAirfoil(
        name="NACA 0018",
        family="Symmetric airfoil",
        role="Thick symmetric root option for strength when camber is not desired.",
        best_zone="Root",
        plain_language_summary="0% camber, 18% thick; strong but needs pitch angle to make lift.",
        thickness_percent=18.0,
        camber_percent=0.0,
        camber_position_percent=0.0,
    ),
    "NACA 0015": SectionAirfoil(
        name="NACA 0015",
        family="Symmetric airfoil",
        role="Balanced symmetric transition option with moderate thickness.",
        best_zone="Root / Mid",
        plain_language_summary="0% camber, 15% thick; predictable symmetric transition section.",
        thickness_percent=15.0,
        camber_percent=0.0,
        camber_position_percent=0.0,
    ),
    "NACA 0012": SectionAirfoil(
        name="NACA 0012",
        family="Symmetric airfoil",
        role="Predictable symmetric outer section that needs positive pitch for lift.",
        best_zone="Tip",
        plain_language_summary=(
            "0% camber, 12% thick; low-camber outer section that relies on pitch."
        ),
        thickness_percent=12.0,
        camber_percent=0.0,
        camber_position_percent=0.0,
    ),
    "SG6040": SectionAirfoil(
        name="SG6040",
        family="High-lift airfoil",
        role="Small-wind root option: thicker SG-series section for startup torque and root strength.",
        best_zone="Root / Mid",
        plain_language_summary=(
            "Selig/Giguere small-wind airfoil; useful near the root where torque and stiffness matter."
        ),
        thickness_percent=16.0,
        camber_description="Cambered SG-series small-wind profile.",
        recommended_reynolds_min=80_000.0,
        recommended_reynolds_max=500_000.0,
        confidence="Medium",
        source_note="Giguere & Selig small horizontal-axis wind-turbine airfoil family.",
        zone_warnings=(
            "Near the tip, SG6040 may add unnecessary thickness and drag compared with thinner options.",
        ),
    ),
    "SG6042": SectionAirfoil(
        name="SG6042",
        family="High-lift airfoil",
        role="Small-wind transition option: balances low-Re lift with moderate drag.",
        best_zone="Root / Mid",
        plain_language_summary=(
            "SG-series small-wind transition airfoil; good bridge from strong root to lift-producing mid blade."
        ),
        thickness_percent=10.0,
        camber_description="Cambered low-Re small-wind profile.",
        recommended_reynolds_min=80_000.0,
        recommended_reynolds_max=500_000.0,
        confidence="Medium",
        source_note="Giguere & Selig small horizontal-axis wind-turbine airfoil family.",
    ),
    "SG6043": SectionAirfoil(
        name="SG6043",
        family="High-lift airfoil",
        role="Small-wind primary lift option: high lift/drag candidate for low-Re mid blade sections.",
        best_zone="Mid",
        plain_language_summary=(
            "SG-series small-wind airfoil; useful in the main lift region when Reynolds number is in range."
        ),
        thickness_percent=10.0,
        camber_percent=5.1,
        camber_position_percent=53.3,
        camber_description="Cambered low-Re high-lift profile.",
        recommended_reynolds_min=80_000.0,
        recommended_reynolds_max=500_000.0,
        confidence="Medium",
        source_note=(
            "Giguere & Selig small horizontal-axis wind-turbine airfoil family; "
            "UIUC coordinates list SG6043 geometry."
        ),
        zone_warnings=(
            "At the blade tip, SG6043 can be useful but may be more stall-sensitive than thinner tip choices.",
        ),
    ),
    "S1223": SectionAirfoil(
        name="S1223",
        family="High-lift airfoil",
        role="Very high-lift low-speed option; useful for experiments but sensitive to stall and drag.",
        best_zone="Mid",
        plain_language_summary=(
            "High-lift low-Re airfoil; strong lift for startup experiments, but not automatically best for high RPM."
        ),
        thickness_percent=12.1,
        camber_description="Very cambered high-lift low-Re profile.",
        recommended_reynolds_min=80_000.0,
        recommended_reynolds_max=500_000.0,
        confidence="Medium",
        source_note="Selig high-lift low-Reynolds airfoil literature and UIUC coordinate database.",
        zone_warnings=(
            "Near the tip, S1223 can create extra drag or stall if pitch/twist is too high.",
        ),
    ),
    "E387": SectionAirfoil(
        name="E387",
        family="Cambered plate",
        role="Low-Re reference option: efficient comparison airfoil when surface finish is reasonably smooth.",
        best_zone="Mid / Tip",
        plain_language_summary=(
            "Eppler low-Re reference airfoil; useful for comparing smoother low-drag designs."
        ),
        thickness_percent=9.1,
        camber_description="Moderately cambered low-Re profile.",
        recommended_reynolds_min=60_000.0,
        recommended_reynolds_max=460_000.0,
        confidence="Medium",
        source_note=(
            "NASA low-Reynolds experimental literature reports E387 tests from "
            "about Re 60,000 to 460,000."
        ),
        zone_warnings=(
            "At the root, E387 may be too thin for a stiff 3D-printed blade without reinforcement.",
        ),
    ),
    "Clark Y": SectionAirfoil(
        name="Clark Y",
        family="Cambered plate",
        role="Flat-bottom cambered section, easy to fabricate and align.",
        best_zone="Mid",
        plain_language_summary="Flat-bottom cambered airfoil; easy to build and align by hand.",
        thickness_percent=11.7,
        camber_description="Traditional flat-bottom cambered profile.",
        recommended_reynolds_min=80_000.0,
        recommended_reynolds_max=500_000.0,
        confidence="Estimated",
        source_note="Traditional classroom-friendly reference shape; modeled conservatively here.",
    ),
    "NREL S822": SectionAirfoil(
        name="NREL S822",
        family="High-lift airfoil",
        role="Thick wind-turbine reference section; useful for comparison but designed for larger rotors.",
        best_zone="Root / Mid",
        plain_language_summary=(
            "NREL thick wind-turbine airfoil for larger stall-regulated rotors; "
            "use cautiously on small classroom blades."
        ),
        thickness_percent=16.0,
        camber_description="Thick wind-turbine profile with roughness-insensitive design goals.",
        recommended_reynolds_min=200_000.0,
        recommended_reynolds_max=1_000_000.0,
        confidence="Medium",
        source_note="NREL S822/S823 report for 3-10 m stall-regulated horizontal-axis wind turbines.",
        zone_warnings=(
            "For a small classroom rotor, NREL S822 may operate below its intended Reynolds range.",
        ),
    ),
    "NREL S823": SectionAirfoil(
        name="NREL S823",
        family="High-lift airfoil",
        role="Thick wind-turbine reference section; strong comparison option for larger low-speed rotors.",
        best_zone="Root / Mid",
        plain_language_summary=(
            "NREL thick wind-turbine airfoil; educational comparison option, "
            "not a guaranteed best small-rotor choice."
        ),
        thickness_percent=21.0,
        camber_description="Very thick wind-turbine profile with roughness-insensitive design goals.",
        recommended_reynolds_min=200_000.0,
        recommended_reynolds_max=1_000_000.0,
        confidence="Medium",
        source_note="NREL S822/S823 report for 3-10 m stall-regulated horizontal-axis wind turbines.",
        zone_warnings=(
            "NREL S823 is very thick and can add drag or weight near the tip of a small classroom rotor.",
            "For a small classroom rotor, NREL S823 may operate below its intended Reynolds range.",
        ),
    ),
    "Flat plate": SectionAirfoil(
        name="Flat plate",
        family="Flat plate / Foam board",
        role="Simple build option with high drag but easy classroom fabrication.",
        best_zone="Prototype",
        plain_language_summary="Flat sheet; easiest to fabricate, but drag is high.",
    ),
}

SECTION_AIRFOIL_ALIASES: dict[str, str] = {
    "Selig S1223": "S1223",
}


def _canonical_airfoil_name(name: str) -> str:
    """Return the canonical catalog key for student or legacy airfoil names."""

    return SECTION_AIRFOIL_ALIASES.get(name, name)


def section_airfoil_options() -> list[str]:
    """Return airfoil names in student-facing order."""

    return list(SECTION_AIRFOILS)


def get_section_airfoil(name: str) -> SectionAirfoil:
    """Return a section airfoil or raise a friendly error."""

    canonical_name = _canonical_airfoil_name(name)
    try:
        return SECTION_AIRFOILS[canonical_name]
    except KeyError as exc:
        choices = ", ".join(SECTION_AIRFOILS)
        raise ValueError(f"Section airfoil must be one of: {choices}.") from exc


def station_airfoil_warnings(name: str, *, station_fraction: float) -> tuple[str, ...]:
    """Return non-blocking guidance for using an airfoil at a blade span station."""

    airfoil = get_section_airfoil(name)
    fraction = max(0.0, min(1.0, station_fraction))
    warnings = list(airfoil.zone_warnings)

    if (
        fraction < 0.20
        and airfoil.thickness_percent is not None
        and airfoil.thickness_percent < 10.0
    ):
        warnings.append(
            f"{airfoil.name} is thin for a root section; "
            "consider reinforcement or a thicker root airfoil."
        )
    if (
        fraction > 0.80
        and airfoil.thickness_percent is not None
        and airfoil.thickness_percent > 15.0
    ):
        warnings.append(
            f"{airfoil.name} is thick for a fast tip section; "
            "compare with thinner low-drag tip airfoils."
        )
    if fraction > 0.80 and airfoil.name == "S1223":
        warnings.append(
            "S1223 near the tip can produce useful lift, but drag and stall risk may limit RPM."
        )

    return tuple(dict.fromkeys(warnings))
