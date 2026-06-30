from windlab.blade_presets import blade_preset_options, get_blade_preset, preset_to_simulation_input
from windlab.simulator import simulate


def test_five_presets_fit_one_meter_three_blade_rule() -> None:
    presets = blade_preset_options()

    assert len(presets) == 5
    for preset in presets:
        assert preset.rotor_radius_m == 0.50
        assert preset.blade_count == 3
        assert len(preset.sections) == 8
        assert preset.sections[-1].position_m <= 0.50
        assert preset.tradeoffs


def test_low_wind_preset_targets_classroom_tunnel() -> None:
    preset = get_blade_preset("Low Wind 3.6 m/s Classroom Tunnel")

    assert preset.wind_speed_m_s == 3.6
    assert preset.sections[3].airfoil_name == "SG6042"
    assert "3.6 m/s" in preset.description


def test_presets_are_smooth_enough_for_beginner_lofting() -> None:
    for preset in blade_preset_options():
        sections = preset.sections
        chords_cm = [section.chord_m * 100.0 for section in sections]
        twists = [section.twist_angle_deg for section in sections]
        airfoils = [section.airfoil_name for section in sections]

        assert all(left > right for left, right in zip(chords_cm, chords_cm[1:], strict=False))
        assert all(left >= right for left, right in zip(twists, twists[1:], strict=False))
        assert (
            max(left - right for left, right in zip(chords_cm, chords_cm[1:], strict=False)) <= 1.5
        )
        assert max(left - right for left, right in zip(twists, twists[1:], strict=False)) <= 4.0
        assert "S1223" not in airfoils


def test_low_wind_preset_is_best_simulated_competition_starting_point() -> None:
    powers_by_name = {
        preset.name: simulate(preset_to_simulation_input(preset)).electrical_power_mw
        for preset in blade_preset_options()
    }

    best_name = max(powers_by_name, key=powers_by_name.get)

    assert best_name == "Low Wind 3.6 m/s Classroom Tunnel"


def test_preset_names_are_stable() -> None:
    names = [preset.name for preset in blade_preset_options()]

    assert names == [
        "Balanced Competition 50 cm",
        "High Starting Torque",
        "High RPM / Low Drag Tip",
        "Low Wind 3.6 m/s Classroom Tunnel",
        "Easy CAD / Easy Print",
    ]
