"""Measured experiment log and calibration helpers."""

import csv
import io
import json
from dataclasses import dataclass

from windlab.models import SimulationInput


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


VALIDATION_BENCHMARK_FIELDNAMES = [
    "case_id",
    "design_name",
    "wind_speed_m_s",
    "air_density_kg_m3",
    "rotor_radius_m",
    "hub_radius_m",
    "blade_count",
    "blade_mass_kg",
    "material",
    "surface_finish",
    "trial_duration_s",
    "generator_volts_per_1000_rpm",
    "generator_internal_resistance_ohm",
    "load_resistance_ohm",
    "generator_efficiency_percent",
    "gear_ratio",
    "use_competition_sections",
    "blade_sections_json",
    "measured_rpm",
    "measured_power_mw",
    "tolerance_percent",
    "notes",
]


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


def _slug(value: str) -> str:
    """Create a stable CSV case id from a design name."""

    lowered = value.strip().lower()
    characters = [character if character.isalnum() else "_" for character in lowered]
    return "_".join(part for part in "".join(characters).split("_") if part) or "prototype"


def measurements_as_validation_benchmark_csv(
    measurements: list[ExperimentMeasurement],
    inputs: SimulationInput,
    *,
    use_competition_sections: bool | None = None,
    tolerance_percent: float = 10.0,
) -> str:
    """Export measurements in the format loaded by model validation reports."""

    should_use_competition_sections = (
        False if use_competition_sections is None else use_competition_sections
    )
    blade_sections_json = (
        json.dumps(
            [section.model_dump() for section in inputs.blade_sections],
            ensure_ascii=False,
        )
        if inputs.blade_sections
        else ""
    )
    rows = [
        {
            "case_id": _slug(measurement.design_name),
            "design_name": measurement.design_name,
            "wind_speed_m_s": measurement.wind_speed_m_s,
            "air_density_kg_m3": inputs.air_density_kg_m3,
            "rotor_radius_m": inputs.rotor_radius_m,
            "hub_radius_m": inputs.hub_radius_m,
            "blade_count": inputs.blade_count,
            "blade_mass_kg": inputs.blade_mass_kg,
            "material": inputs.material,
            "surface_finish": inputs.surface_finish,
            "trial_duration_s": inputs.trial_duration_s,
            "generator_volts_per_1000_rpm": inputs.generator_volts_per_1000_rpm,
            "generator_internal_resistance_ohm": inputs.generator_internal_resistance_ohm,
            "load_resistance_ohm": inputs.load_resistance_ohm,
            "generator_efficiency_percent": inputs.generator_efficiency_percent,
            "gear_ratio": inputs.gear_ratio,
            "use_competition_sections": ("true" if should_use_competition_sections else "false"),
            "blade_sections_json": blade_sections_json,
            "measured_rpm": measurement.measured_rpm,
            "measured_power_mw": measurement.measured_power_mw,
            "tolerance_percent": tolerance_percent,
            "notes": measurement.notes,
        }
        for measurement in measurements
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=VALIDATION_BENCHMARK_FIELDNAMES)
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
