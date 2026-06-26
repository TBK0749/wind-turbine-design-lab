import pytest

from windlab.bemt import calculate_bemt_lite
from windlab.blade_geometry import competition_50cm_sections
from windlab.models import SimulationInput
from windlab.simulator import simulate


def test_bemt_lite_uses_relative_wind_speed_above_free_stream() -> None:
    inputs = SimulationInput(
        rotor_radius_m=0.45,
        hub_radius_m=0.10,
        blade_sections=competition_50cm_sections(),
    )

    result = calculate_bemt_lite(inputs, tip_speed_ratio=6.5)

    assert result.section_count > 0
    assert result.mean_relative_wind_speed_m_s > inputs.wind_speed_m_s
    assert result.mechanical_power_w > 0.0
    assert 0.0 < result.cp < 0.50


def test_bemt_lite_power_changes_with_twist_distribution() -> None:
    baseline = SimulationInput(
        rotor_radius_m=0.45,
        hub_radius_m=0.10,
        blade_sections=competition_50cm_sections(),
    )
    overpitched_sections = tuple(
        section.model_copy(update={"twist_angle_deg": section.twist_angle_deg + 18.0})
        for section in competition_50cm_sections()
    )
    overpitched = baseline.model_copy(update={"blade_sections": overpitched_sections})

    baseline_result = calculate_bemt_lite(baseline, tip_speed_ratio=6.5)
    overpitched_result = calculate_bemt_lite(overpitched, tip_speed_ratio=6.5)

    assert overpitched_result.mechanical_power_w < baseline_result.mechanical_power_w


def test_simulator_uses_bemt_lite_for_section_table_by_default() -> None:
    result = simulate(
        SimulationInput(
            rotor_radius_m=0.45,
            hub_radius_m=0.10,
            blade_sections=competition_50cm_sections(),
        )
    )

    assert result.model_mode == "BEMT-lite"
    assert result.bemt_section_count == pytest.approx(5)
    assert result.bemt_mean_relative_wind_speed_m_s > 8.0
