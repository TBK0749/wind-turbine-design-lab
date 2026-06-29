import pytest

from windlab.airfoils import estimate_airfoil_performance, lookup_airfoil_polar
from windlab import section_airfoils
from windlab.section_airfoils import (
    get_section_airfoil,
    section_airfoil_options,
)


REQUESTED_SOURCE_BACKED_AIRFOILS = (
    "SG6040",
    "SG6042",
    "SG6043",
    "S1223",
    "E387",
    "Clark Y",
    "NREL S822",
    "NREL S823",
)


@pytest.mark.parametrize("airfoil_name", REQUESTED_SOURCE_BACKED_AIRFOILS)
def test_source_backed_airfoils_are_selectable_with_metadata(airfoil_name: str) -> None:
    airfoil = get_section_airfoil(airfoil_name)

    assert airfoil.name == airfoil_name
    assert airfoil.family in {
        "Cambered plate",
        "Symmetric airfoil",
        "High-lift airfoil",
    }
    assert airfoil.best_zone
    assert airfoil.plain_language_summary
    assert airfoil.thickness_percent is not None
    assert airfoil.thickness_percent > 0.0
    assert airfoil.camber_description
    assert airfoil.recommended_reynolds_min > 0.0
    assert airfoil.recommended_reynolds_max > airfoil.recommended_reynolds_min
    assert airfoil.confidence in {"High", "Medium", "Estimated"}
    assert airfoil.source_note


def test_source_backed_airfoils_are_in_student_selector_order() -> None:
    options = section_airfoil_options()

    for airfoil_name in REQUESTED_SOURCE_BACKED_AIRFOILS:
        assert airfoil_name in options


def test_legacy_selig_s1223_name_still_resolves_to_canonical_s1223() -> None:
    airfoil = get_section_airfoil("Selig S1223")

    assert airfoil.name == "S1223"


@pytest.mark.parametrize("airfoil_name", REQUESTED_SOURCE_BACKED_AIRFOILS)
def test_source_backed_airfoils_have_polar_lookup(airfoil_name: str) -> None:
    polar = lookup_airfoil_polar(
        airfoil_name,
        angle_of_attack_deg=6.0,
        reynolds_number=150_000.0,
    )

    assert polar.airfoil_name == airfoil_name
    assert polar.lift_coefficient > 0.0
    assert polar.drag_coefficient > 0.0


def test_out_of_range_reynolds_warns_for_large_nrel_airfoil() -> None:
    result = estimate_airfoil_performance(
        "High-lift airfoil",
        airfoil_name="NREL S822",
        angle_of_attack_deg=6.0,
        reynolds_number=25_000.0,
    )

    assert any("recommended Reynolds range" in warning for warning in result.warnings)
    assert any("small classroom rotor" in warning for warning in result.warnings)


def test_tip_zone_guidance_warns_for_very_high_lift_airfoil_at_tip() -> None:
    warnings = section_airfoils.station_airfoil_warnings("S1223", station_fraction=0.95)

    assert any("tip" in warning.lower() for warning in warnings)
    assert any("drag" in warning.lower() or "stall" in warning.lower() for warning in warnings)


def test_thin_low_re_root_guidance_warns_for_tip_airfoil_at_root() -> None:
    warnings = section_airfoils.station_airfoil_warnings("E387", station_fraction=0.08)

    assert any("root" in warning.lower() for warning in warnings)
