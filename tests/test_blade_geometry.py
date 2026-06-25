import pytest

from windlab.blade_geometry import competition_50cm_sections, summarize_blade_geometry
from windlab.models import SimulationInput


def test_competition_preset_has_expected_root_and_tip() -> None:
    sections = competition_50cm_sections()
    assert len(sections) == 6
    assert sections[0].position_m == pytest.approx(0.05)
    assert sections[0].chord_m == pytest.approx(0.09)
    assert sections[0].twist_angle_deg == pytest.approx(20.0)
    assert sections[-1].position_m == pytest.approx(0.50)
    assert sections[-1].chord_m == pytest.approx(0.02)
    assert sections[-1].twist_angle_deg == pytest.approx(0.0)


def test_section_summary_uses_all_stations() -> None:
    inputs = SimulationInput(
        rotor_radius_m=0.5,
        hub_radius_m=0.05,
        blade_sections=competition_50cm_sections(),
    )
    summary = summarize_blade_geometry(inputs)
    assert summary.section_count == 6
    assert summary.root_chord_m == pytest.approx(0.09)
    assert summary.tip_chord_m == pytest.approx(0.02)
    assert 0.02 < summary.mean_chord_m < 0.09
    assert 0.0 < summary.representative_twist_deg < 20.0
