import csv
import io

from windlab.calibration import (
    ExperimentMeasurement,
    average_correction_factors,
    calibration_markdown_report,
    correction_factor,
    measurement_row,
    measurements_as_csv,
    measurements_as_validation_benchmark_csv,
    percent_error,
    summarize_measurement,
)
from windlab.models import SimulationInput


def test_percent_error_and_correction_factor_use_measured_values() -> None:
    assert percent_error(predicted=120.0, measured=100.0) == 20.0
    assert correction_factor(predicted=120.0, measured=100.0) == 0.8333333333333334


def test_measurement_summary_reports_error_and_factor() -> None:
    summary = summarize_measurement(
        ExperimentMeasurement(
            design_name="Prototype A",
            wind_speed_m_s=8.0,
            predicted_rpm=600.0,
            measured_rpm=500.0,
            predicted_power_mw=30.0,
            measured_power_mw=20.0,
        )
    )

    assert summary.rpm_error_percent == 20.0
    assert summary.power_error_percent == 50.0
    assert summary.rpm_correction_factor == 0.8333
    assert summary.power_correction_factor == 0.6667


def test_measurement_exports_include_correction_columns() -> None:
    measurement = ExperimentMeasurement(
        design_name="Prototype A",
        wind_speed_m_s=8.0,
        predicted_rpm=600.0,
        measured_rpm=500.0,
        predicted_power_mw=30.0,
        measured_power_mw=20.0,
        notes="First print",
    )

    row = measurement_row(measurement)
    csv_text = measurements_as_csv([measurement])
    report = calibration_markdown_report([measurement])

    assert row["RPM error (%)"] == 20.0
    assert "mW correction factor" in csv_text
    assert "Prototype A" in report
    assert "Average mW correction factor: 0.6667" in report


def test_average_correction_factors_across_measurements() -> None:
    measurements = [
        ExperimentMeasurement("A", 8.0, 100.0, 80.0, 10.0, 5.0),
        ExperimentMeasurement("B", 8.0, 200.0, 180.0, 20.0, 18.0),
    ]

    assert average_correction_factors(measurements) == (0.85, 0.7)


def test_validation_benchmark_csv_export_matches_validation_import_format() -> None:
    inputs = SimulationInput(
        wind_speed_m_s=3.6,
        rotor_radius_m=0.45,
        hub_radius_m=0.10,
        blade_count=3,
        blade_mass_kg=0.10,
        material="Plastic",
        surface_finish="Raw 3D print",
        trial_duration_s=60.0,
    )
    measurements = [
        ExperimentMeasurement(
            design_name="Prototype A",
            wind_speed_m_s=3.6,
            predicted_rpm=400.0,
            measured_rpm=420.0,
            predicted_power_mw=2.0,
            measured_power_mw=2.5,
            notes="first print",
        )
    ]

    csv_text = measurements_as_validation_benchmark_csv(
        measurements,
        inputs,
        use_competition_sections=True,
        tolerance_percent=10.0,
    )
    row = next(csv.DictReader(io.StringIO(csv_text)))

    assert row["case_id"] == "prototype_a"
    assert row["design_name"] == "Prototype A"
    assert row["wind_speed_m_s"] == "3.6"
    assert row["rotor_radius_m"] == "0.45"
    assert row["material"] == "Plastic"
    assert row["surface_finish"] == "Raw 3D print"
    assert row["use_competition_sections"] == "true"
    assert row["measured_rpm"] == "420.0"
    assert row["measured_power_mw"] == "2.5"
    assert row["tolerance_percent"] == "10.0"
