import pytest

from windlab.generator import simulate_generator


def test_generator_obeys_ohms_law_at_load() -> None:
    result = simulate_generator(
        rotor_rpm=1000.0,
        mechanical_power_w=10.0,
        volts_per_1000_rpm=2.0,
        internal_resistance_ohm=100.0,
        load_resistance_ohm=100.0,
        efficiency_percent=80.0,
        gear_ratio=1.0,
        trial_duration_s=60.0,
    )
    assert result.open_circuit_voltage_v == pytest.approx(2.0)
    assert result.load_voltage_v == pytest.approx(1.0)
    assert result.load_current_ma == pytest.approx(10.0)
    assert result.electrical_power_mw == pytest.approx(10.0)
    assert result.electrical_energy_mj == pytest.approx(600.0)


def test_generator_output_is_capped_by_mechanical_power() -> None:
    result = simulate_generator(
        rotor_rpm=10000.0,
        mechanical_power_w=0.001,
        volts_per_1000_rpm=10.0,
        internal_resistance_ohm=0.0,
        load_resistance_ohm=1.0,
        efficiency_percent=50.0,
        gear_ratio=1.0,
        trial_duration_s=10.0,
    )
    assert result.electrical_power_mw == pytest.approx(0.5)
    assert result.electrical_energy_mj == pytest.approx(5.0)


def test_generator_load_feedback_reduces_operating_rpm_when_overloaded() -> None:
    result = simulate_generator(
        rotor_rpm=10000.0,
        mechanical_power_w=0.001,
        volts_per_1000_rpm=10.0,
        internal_resistance_ohm=0.0,
        load_resistance_ohm=1.0,
        efficiency_percent=50.0,
        gear_ratio=1.0,
        trial_duration_s=10.0,
        apply_load_feedback=True,
    )

    assert result.unloaded_generator_rpm == pytest.approx(10000.0)
    assert result.generator_rpm < 10.0
    assert result.generator_load_factor < 0.01
    assert result.electrical_power_mw == pytest.approx(0.5)


def test_generator_load_feedback_can_be_disabled_for_legacy_cap_behavior() -> None:
    result = simulate_generator(
        rotor_rpm=10000.0,
        mechanical_power_w=0.001,
        volts_per_1000_rpm=10.0,
        internal_resistance_ohm=0.0,
        load_resistance_ohm=1.0,
        efficiency_percent=50.0,
        gear_ratio=1.0,
        trial_duration_s=10.0,
        apply_load_feedback=False,
    )

    assert result.unloaded_generator_rpm == pytest.approx(10000.0)
    assert result.generator_rpm == pytest.approx(10000.0)
    assert result.generator_load_factor == pytest.approx(1.0)
    assert result.electrical_power_mw == pytest.approx(0.5)
