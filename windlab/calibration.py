"""Measured experiment log and calibration helpers."""

import csv
import io
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExperimentMeasurement:
    """One measured wind-tunnel or competition trial."""

    design_name: str
    wind_speed_m_s: float
    predicted_rpm: float
    measured_rpm: float
    predicted_power_mw: float
    measured_power_mw: float
    notes: str = ""


@dataclass(frozen=True, slots=True)
class CalibrationSummary:
    """Calculated prediction error and simple future correction factors."""

    rpm_error_percent: float
    power_error_percent: float
    rpm_correction_factor: float
    power_correction_factor: float


def percent_error(predicted: float, measured: float) -> float:
    """Return signed percent error relative to measured value."""

    if measured == 0.0:
        return 0.0 if predicted == 0.0 else 100.0
    return (predicted - measured) / measured * 100.0


def correction_factor(predicted: float, measured: float) -> float:
    """Return measured / predicted correction factor for future calibration."""

    if predicted <= 0.0:
        return 0.0
    return measured / predicted


def summarize_measurement(measurement: ExperimentMeasurement) -> CalibrationSummary:
    """Calculate calibration values for one measured experiment."""

    return CalibrationSummary(
        rpm_error_percent=round(
            percent_error(measurement.predicted_rpm, measurement.measured_rpm),
            2,
        ),
        power_error_percent=round(
            percent_error(measurement.predicted_power_mw, measurement.measured_power_mw),
            2,
        ),
        rpm_correction_factor=round(
            correction_factor(measurement.predicted_rpm, measurement.measured_rpm),
            4,
        ),
        power_correction_factor=round(
            correction_factor(measurement.predicted_power_mw, measurement.measured_power_mw),
            4,
        ),
    )


def measurement_row(measurement: ExperimentMeasurement) -> dict[str, float | str]:
    """Return one flat export/display row."""

    summary = summarize_measurement(measurement)
    return {
        "Design": measurement.design_name,
        "Wind speed (m/s)": measurement.wind_speed_m_s,
        "Predicted RPM": measurement.predicted_rpm,
        "Measured RPM": measurement.measured_rpm,
        "RPM error (%)": summary.rpm_error_percent,
        "RPM correction factor": summary.rpm_correction_factor,
        "Predicted mW": measurement.predicted_power_mw,
        "Measured mW": measurement.measured_power_mw,
        "mW error (%)": summary.power_error_percent,
        "mW correction factor": summary.power_correction_factor,
        "Notes": measurement.notes,
    }


def average_correction_factors(
    measurements: list[ExperimentMeasurement],
) -> tuple[float, float]:
    """Return average RPM and mW correction factors for nonzero predictions."""

    summaries = [summarize_measurement(measurement) for measurement in measurements]
    rpm_values = [
        summary.rpm_correction_factor
        for summary in summaries
        if summary.rpm_correction_factor > 0.0
    ]
    power_values = [
        summary.power_correction_factor
        for summary in summaries
        if summary.power_correction_factor > 0.0
    ]
    rpm_average = sum(rpm_values) / len(rpm_values) if rpm_values else 0.0
    power_average = sum(power_values) / len(power_values) if power_values else 0.0
    return round(rpm_average, 4), round(power_average, 4)


def measurements_as_csv(measurements: list[ExperimentMeasurement]) -> str:
    """Export measured experiment rows as CSV."""

    rows = [measurement_row(measurement) for measurement in measurements]
    output = io.StringIO()
    empty_measurement = ExperimentMeasurement("", 0, 0, 0, 0, 0)
    fieldnames = list(rows[0]) if rows else list(measurement_row(empty_measurement))
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def calibration_markdown_report(measurements: list[ExperimentMeasurement]) -> str:
    """Export a readable calibration worksheet as Markdown."""

    rpm_factor, power_factor = average_correction_factors(measurements)
    lines = [
        "# Wind Turbine Calibration Worksheet",
        "",
        "This worksheet compares simulator predictions with measured prototype data.",
        "",
        "## Suggested correction factors",
        "",
        f"- Average RPM correction factor: {rpm_factor:.4f}",
        f"- Average mW correction factor: {power_factor:.4f}",
        "",
        "Use these as guidance only. Do not change the simulator constants until several "
        "repeatable physical tests show the same pattern.",
        "",
        "## Experiment log",
        "",
        "| Design | Wind (m/s) | Pred RPM | Meas RPM | RPM err % | "
        "Pred mW | Meas mW | mW err % | Notes |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for measurement in measurements:
        summary = summarize_measurement(measurement)
        lines.append(
            "| "
            f"{measurement.design_name} | "
            f"{measurement.wind_speed_m_s:.2f} | "
            f"{measurement.predicted_rpm:.2f} | "
            f"{measurement.measured_rpm:.2f} | "
            f"{summary.rpm_error_percent:.2f} | "
            f"{measurement.predicted_power_mw:.4f} | "
            f"{measurement.measured_power_mw:.4f} | "
            f"{summary.power_error_percent:.2f} | "
            f"{measurement.notes} |"
        )
    return "\n".join(lines) + "\n"
