import json

from windlab.blade_geometry import competition_50cm_sections
from windlab.models import SimulationInput
from windlab.simulator import performance_curve, result_as_design_sheet, result_as_json, simulate


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
    assert result.airfoil_lift_drag_ratio > 0
    assert 0.45 <= result.airfoil_efficiency_factor <= 1.12


def test_power_increases_with_wind_speed() -> None:
    inputs = SimulationInput()
    rows = performance_curve(inputs, [4.0, 8.0])
    assert rows[1]["Power (W)"] > rows[0]["Power (W)"]
    assert rows[1]["Electrical power (mW)"] > rows[0]["Electrical power (mW)"]


def test_airfoil_choice_changes_competition_power() -> None:
    flat = simulate(SimulationInput(airfoil_type="Flat plate / Foam board"))
    high_lift = simulate(SimulationInput(airfoil_type="High-lift airfoil"))

    assert high_lift.airfoil_efficiency_factor > flat.airfoil_efficiency_factor
    assert high_lift.electrical_power_mw > flat.electrical_power_mw


def test_overpitched_airfoil_adds_stall_warning() -> None:
    result = simulate(
        SimulationInput(
            airfoil_type="High-lift airfoil",
            pitch_angle_deg=25.0,
            twist_angle_deg=25.0,
        )
    )

    assert result.airfoil_stall_risk
    assert any("stall" in warning.lower() for warning in result.warnings)


def test_json_export_contains_inputs_and_results() -> None:
    inputs = SimulationInput()
    payload = json.loads(result_as_json(inputs, simulate(inputs)))
    assert payload["inputs"]["blade_count"] == 3
    assert payload["inputs"]["airfoil_type"] == "Flat plate / Foam board"
    assert payload["results"]["mechanical_power_w"] > 0
    assert payload["results"]["airfoil_lift_drag_ratio"] > 0


def test_design_sheet_export_contains_build_table() -> None:
    inputs = SimulationInput(
        rotor_radius_m=0.45,
        hub_radius_m=0.10,
        blade_sections=competition_50cm_sections(),
    )
    sheet = result_as_design_sheet(inputs, simulate(inputs))

    assert "# Wind Turbine Design Sheet" in sheet
    assert "Competition power" in sheet
    assert "| Section | Position (cm) | Chord (cm) | Twist (deg) | Airfoil | Role |" in sheet
    assert "NACA 4418" in sheet
