import json

from windlab.models import SimulationInput
from windlab.simulator import performance_curve, result_as_json, simulate


def test_default_simulation_produces_positive_bounded_results() -> None:
    result = simulate(SimulationInput())
    assert result.mechanical_power_w > 0
    assert result.rpm > 0
    assert result.torque_n_m > 0
    assert result.electrical_power_mw > 0
    assert result.load_voltage_v > 0
    assert result.load_current_ma > 0
    assert 0 < result.cp <= 0.5
    assert 0 <= result.design_score <= 100


def test_power_increases_with_wind_speed() -> None:
    inputs = SimulationInput()
    rows = performance_curve(inputs, [4.0, 8.0])
    assert rows[1]["Power (W)"] > rows[0]["Power (W)"]
    assert rows[1]["Electrical power (mW)"] > rows[0]["Electrical power (mW)"]


def test_json_export_contains_inputs_and_results() -> None:
    inputs = SimulationInput()
    payload = json.loads(result_as_json(inputs, simulate(inputs)))
    assert payload["inputs"]["blade_count"] == 3
    assert payload["results"]["mechanical_power_w"] > 0
