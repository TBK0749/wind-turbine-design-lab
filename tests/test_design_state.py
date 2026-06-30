from windlab.blade_geometry import competition_50cm_sections
from windlab.design_state import (
    DEFAULT_DESIGN_NAME,
    default_design_input,
    design_input_from_dict,
    design_input_to_dict,
)
from windlab.models import SimulationInput


def test_design_input_round_trips_blade_sections() -> None:
    original = SimulationInput(
        wind_speed_m_s=3.6,
        rotor_radius_m=0.50,
        hub_radius_m=0.08,
        blade_count=3,
        blade_sections=competition_50cm_sections(),
        generator_volts_per_1000_rpm=2.0,
    )

    payload = design_input_to_dict(original)
    restored = design_input_from_dict(payload)

    assert restored.wind_speed_m_s == 3.6
    assert restored.rotor_radius_m == 0.50
    assert restored.hub_radius_m == 0.08
    assert restored.blade_count == 3
    assert restored.generator_volts_per_1000_rpm == 2.0
    assert restored.blade_sections[0].airfoil_name == "NACA 4418"
    assert restored.blade_sections[-1].airfoil_name == "NACA 2412"


def test_default_design_input_matches_competition_starting_point() -> None:
    default = default_design_input()

    assert DEFAULT_DESIGN_NAME == "Current design"
    assert default.rotor_radius_m == 0.45
    assert default.blade_count == 3
    assert len(default.blade_sections) == 6
