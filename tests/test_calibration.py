from windlab.models import SimulationInput
from windlab.simulator import simulate


def test_custom_practical_cp_limit_caps_cp() -> None:
    result = simulate(
        SimulationInput(
            practical_cp_limit=0.20,
            use_practical_cp_limit=True,
            airfoil_efficiency_multiplier=1.0,
        )
    )

    assert result.cp <= 0.20


def test_disabling_airfoil_correction_changes_result() -> None:
    corrected = simulate(SimulationInput(airfoil_type="Flat plate / Foam board"))
    disabled = simulate(
        SimulationInput(
            airfoil_type="Flat plate / Foam board",
            use_airfoil_correction=False,
        )
    )

    assert disabled.airfoil_efficiency_factor == 1.0
    assert disabled.electrical_power_mw > corrected.electrical_power_mw


def test_startup_torque_can_stop_low_torque_design() -> None:
    result = simulate(
        SimulationInput(
            wind_speed_m_s=2.0,
            startup_torque_n_m=999.0,
            use_startup_torque_loss=True,
        )
    )

    assert result.rpm == 0.0
    assert result.electrical_power_mw == 0.0
    assert any("startup torque" in warning.lower() for warning in result.warnings)
