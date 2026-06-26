import pytest

from windlab.blade_geometry import competition_50cm_sections, summarize_blade_geometry
from windlab.models import SimulationInput


def test_competition_preset_has_expected_root_and_tip() -> None:
    sections = competition_50cm_sections()
    assert len(sections) == 6
    assert sections[0].position_m == pytest.approx(0.05)
    assert sections[0].chord_m == pytest.approx(0.085)
    assert sections[0].twist_angle_deg == pytest.approx(20.0)
    assert sections[0].airfoil_name == "NACA 4418"
    assert sections[-1].position_m == pytest.approx(0.45)
    assert sections[-1].chord_m == pytest.approx(0.018)
    assert sections[-1].twist_angle_deg == pytest.approx(0.0)
    assert sections[-1].airfoil_name == "NACA 2412"


def test_section_summary_uses_all_stations() -> None:
    inputs = SimulationInput(
        rotor_radius_m=0.5,
        hub_radius_m=0.05,
        blade_sections=competition_50cm_sections(),
    )
    summary = summarize_blade_geometry(inputs)
    assert summary.section_count == 6
    assert summary.root_chord_m == pytest.approx(0.085)
    assert summary.tip_chord_m == pytest.approx(0.018)
    assert 0.018 < summary.mean_chord_m < 0.085
    assert 0.0 < summary.representative_twist_deg < 20.0
    assert summary.representative_airfoil_name in {"NACA 4412", "NACA 2412"}
