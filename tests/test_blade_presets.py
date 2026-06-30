from windlab.blade_presets import blade_preset_options, get_blade_preset


def test_five_presets_fit_one_meter_three_blade_rule() -> None:
    presets = blade_preset_options()

    assert len(presets) == 5
    for preset in presets:
        assert preset.rotor_radius_m == 0.50
        assert preset.blade_count == 3
        assert len(preset.sections) == 6
        assert preset.sections[-1].position_m <= 0.50
        assert preset.tradeoffs


def test_low_wind_preset_targets_classroom_tunnel() -> None:
    preset = get_blade_preset("Low Wind 3.6 m/s Classroom Tunnel")

    assert preset.wind_speed_m_s == 3.6
    assert preset.sections[2].airfoil_name == "S1223"
    assert "3.6 m/s" in preset.description


def test_preset_names_are_stable() -> None:
    names = [preset.name for preset in blade_preset_options()]

    assert names == [
        "Balanced Competition 50 cm",
        "High Starting Torque",
        "High RPM / Low Drag Tip",
        "Low Wind 3.6 m/s Classroom Tunnel",
        "Easy CAD / Easy Print",
    ]
