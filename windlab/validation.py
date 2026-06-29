"""Paper benchmark validation utilities for the wind turbine simulator."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from windlab.blade_geometry import competition_50cm_sections
from windlab.models import SimulationInput, SimulationResult
from windlab.simulator import simulate

BenchmarkRole = Literal["runnable", "range_check", "reference_only"]
BenchmarkConfidence = Literal["low", "medium", "high"]


class BenchmarkTarget(BaseModel):
    """Measured or reported target range from a paper."""

    metric: str
    min: float
    max: float
    unit: str


class BenchmarkCase(BaseModel):
    """One validation benchmark extracted from a paper or local experiment."""

    id: str
    paper: str
    source_detail: str
    role: BenchmarkRole
    confidence: BenchmarkConfidence
    notes: str
    inputs: dict[str, object] = Field(default_factory=dict)
    targets: list[BenchmarkTarget] = Field(default_factory=list)
    use_competition_sections: bool = False


class TargetComparison(BaseModel):
    """Comparison between one prediction and one target range."""

    metric: str
    predicted: float
    target_min: float
    target_max: float
    unit: str
    status: Literal["within_range", "below_range", "above_range"]
    error_percent: float


class BenchmarkRunResult(BaseModel):
    """Simulator output and target comparisons for one benchmark case."""

    case_id: str
    simulated: bool
    predictions: dict[str, float] = Field(default_factory=dict)
    comparisons: list[TargetComparison] = Field(default_factory=list)


def load_benchmark_cases(
    path: Path = Path("data/validation_benchmarks.json"),
    measured_path: Path | None = None,
) -> list[BenchmarkCase]:
    """Load benchmark cases from JSON."""

    raw_cases = json.loads(path.read_text())
    cases = [BenchmarkCase.model_validate(raw_case) for raw_case in raw_cases]
    measured_benchmark_path = measured_path or path.with_name("classroom_measured_benchmarks.csv")
    cases.extend(load_measured_classroom_benchmarks(measured_benchmark_path))
    return cases


def _csv_value(row: dict[str, str], key: str) -> str:
    """Return a trimmed CSV value, treating missing cells as blank."""

    return row.get(key, "").strip()


def _optional_float(row: dict[str, str], key: str, default: float | None = None) -> float | None:
    """Parse an optional float from a measured benchmark row."""

    value = _csv_value(row, key)
    if value == "":
        return default
    return float(value)


def _optional_int(row: dict[str, str], key: str, default: int | None = None) -> int | None:
    """Parse an optional integer from a measured benchmark row."""

    value = _csv_value(row, key)
    if value == "":
        return default
    return int(float(value))


def _optional_bool(row: dict[str, str], key: str, default: bool = False) -> bool:
    """Parse an optional boolean from a measured benchmark row."""

    value = _csv_value(row, key).lower()
    if value == "":
        return default
    return value in {"1", "true", "yes", "y", "on"}


def _case_slug(value: str) -> str:
    """Create a stable benchmark id suffix from a measured design name."""

    lowered = value.strip().lower()
    characters = [character if character.isalnum() else "_" for character in lowered]
    slug = "_".join(part for part in "".join(characters).split("_") if part)
    return slug or "classroom_trial"


def _target_from_measured_value(
    *,
    metric: str,
    measured_value: float,
    tolerance_percent: float,
    unit: str,
) -> BenchmarkTarget:
    """Create a validation target range from a measured value and tolerance."""

    tolerance = abs(tolerance_percent) / 100.0
    return BenchmarkTarget(
        metric=metric,
        min=measured_value * (1.0 - tolerance),
        max=measured_value * (1.0 + tolerance),
        unit=unit,
    )


def load_measured_classroom_benchmarks(
    path: Path = Path("data/classroom_measured_benchmarks.csv"),
) -> list[BenchmarkCase]:
    """Load measured classroom prototype CSV rows as runnable validation cases."""

    if not path.exists():
        return []

    cases: list[BenchmarkCase] = []
    with path.open(newline="") as csv_file:
        for index, row in enumerate(csv.DictReader(csv_file), start=1):
            if not any(value.strip() for value in row.values() if value):
                continue
            design_name = _csv_value(row, "design_name") or f"Measured trial {index}"
            case_id = _csv_value(row, "case_id") or design_name
            tolerance_percent = _optional_float(row, "tolerance_percent", 5.0) or 5.0
            measured_rpm = _optional_float(row, "measured_rpm", 0.0) or 0.0
            measured_power_mw = _optional_float(row, "measured_power_mw", 0.0) or 0.0

            inputs: dict[str, object] = {}
            for key in (
                "wind_speed_m_s",
                "air_density_kg_m3",
                "rotor_radius_m",
                "hub_radius_m",
                "blade_mass_kg",
                "trial_duration_s",
                "generator_volts_per_1000_rpm",
                "generator_internal_resistance_ohm",
                "load_resistance_ohm",
                "generator_efficiency_percent",
                "gear_ratio",
            ):
                value = _optional_float(row, key)
                if value is not None:
                    inputs[key] = value
            blade_count = _optional_int(row, "blade_count")
            if blade_count is not None:
                inputs["blade_count"] = blade_count
            for key in ("material", "surface_finish"):
                value = _csv_value(row, key)
                if value:
                    inputs[key] = value

            targets: list[BenchmarkTarget] = []
            if measured_rpm > 0.0:
                targets.append(
                    _target_from_measured_value(
                        metric="rpm",
                        measured_value=measured_rpm,
                        tolerance_percent=tolerance_percent,
                        unit="RPM",
                    )
                )
            if measured_power_mw > 0.0:
                targets.append(
                    _target_from_measured_value(
                        metric="electrical_power_mw",
                        measured_value=measured_power_mw,
                        tolerance_percent=tolerance_percent,
                        unit="mW",
                    )
                )

            cases.append(
                BenchmarkCase(
                    id=f"measured_{_case_slug(case_id)}",
                    paper="Measured classroom benchmark",
                    source_detail=f"{design_name} measured after 3D print / tunnel test.",
                    role="runnable",
                    confidence="high",
                    notes=_csv_value(row, "notes")
                    or "Local measured prototype row loaded from classroom CSV.",
                    inputs=inputs,
                    targets=targets,
                    use_competition_sections=_optional_bool(
                        row,
                        "use_competition_sections",
                        default=True,
                    ),
                )
            )
    return cases


def compare_prediction_to_target(predicted: float, target: BenchmarkTarget) -> TargetComparison:
    """Compare a predicted value with a measured target range."""

    if target.min <= predicted <= target.max:
        status: Literal["within_range", "below_range", "above_range"] = "within_range"
        error_percent = 0.0
    elif predicted < target.min:
        status = "below_range"
        error_percent = (predicted - target.min) / target.min * 100.0
    else:
        status = "above_range"
        error_percent = (predicted - target.max) / target.max * 100.0

    return TargetComparison(
        metric=target.metric,
        predicted=predicted,
        target_min=target.min,
        target_max=target.max,
        unit=target.unit,
        status=status,
        error_percent=error_percent,
    )


def _prediction_map_from_result(result: SimulationResult) -> dict[str, float]:
    """Map SimulationResult fields to validation metric names."""

    return {
        "cp": result.cp,
        "rpm": result.rpm,
        "mechanical_power_w": result.mechanical_power_w,
        "electrical_power_mw": result.electrical_power_mw,
        "electrical_power_w": result.electrical_power_mw / 1000.0,
        "torque_n_m": result.torque_n_m,
        "tip_speed_ratio": result.tip_speed_ratio,
        "generator_load_factor": result.generator_load_factor,
        "unloaded_generator_rpm": result.unloaded_generator_rpm,
        "airfoil_reynolds_number": result.airfoil_reynolds_number,
        "bemt_mean_prandtl_loss_factor": result.bemt_mean_prandtl_loss_factor,
    }


def run_benchmark_case(case: BenchmarkCase) -> BenchmarkRunResult:
    """Run one benchmark case if it has enough input data."""

    if case.role == "reference_only" or not case.inputs:
        return BenchmarkRunResult(case_id=case.id, simulated=False)

    input_data = dict(case.inputs)
    if case.use_competition_sections:
        input_data["blade_sections"] = competition_50cm_sections()
    inputs = SimulationInput.model_validate(input_data)
    simulation = simulate(inputs)
    predictions = _prediction_map_from_result(simulation)
    comparisons = [
        compare_prediction_to_target(predictions[target.metric], target)
        for target in case.targets
        if target.metric in predictions
    ]
    return BenchmarkRunResult(
        case_id=case.id,
        simulated=True,
        predictions=predictions,
        comparisons=comparisons,
    )


def _format_float(value: float) -> str:
    """Format validation numbers consistently."""

    if abs(value) >= 100.0:
        return f"{value:.1f}"
    if abs(value) >= 10.0:
        return f"{value:.2f}"
    return f"{value:.4f}"


def render_validation_report(cases: list[BenchmarkCase]) -> str:
    """Render the full model validation report as Markdown."""

    run_results = {case.id: run_benchmark_case(case) for case in cases}
    lines: list[str] = [
        "# Model Validation Report",
        "",
        (
            "This report compares the current educational simulator with benchmark values "
            "extracted from the supplied small-wind-turbine papers."
        ),
        "",
        (
            "The report separates strict comparisons from reference-only paper values. "
            "Reference-only rows are not used for calibration because geometry, load, "
            "or generator details are incomplete."
        ),
        "",
        "## Runnable and range-check comparisons",
        "",
        "| Case | Paper | Role | Confidence | Metric | Target | Predicted | Status | Error |",
        "|---|---|---|---|---|---:|---:|---|---:|",
    ]

    for case in cases:
        if case.role == "reference_only":
            continue
        result = run_results[case.id]
        if not case.targets:
            for metric in ("cp", "rpm", "mechanical_power_w", "electrical_power_mw"):
                prediction = result.predictions.get(metric)
                if prediction is None:
                    continue
                lines.append(
                    f"| `{case.id}` | {case.paper} | {case.role} | {case.confidence} | "
                    f"{metric} | - | {_format_float(prediction)} | recorded | - |"
                )
            continue
        for comparison in result.comparisons:
            target_range = (
                f"{_format_float(comparison.target_min)} to "
                f"{_format_float(comparison.target_max)} {comparison.unit}"
            )
            lines.append(
                f"| `{case.id}` | {case.paper} | {case.role} | {case.confidence} | "
                f"{comparison.metric} | {target_range} | "
                f"{_format_float(comparison.predicted)} | {comparison.status} | "
                f"{comparison.error_percent:.1f}% |"
            )

    lines.extend(
        [
            "",
            "## Reference-only paper results",
            "",
            "| Case | Paper | Role | Confidence | Paper value | Why reference-only |",
            "|---|---|---|---|---|---|",
        ]
    )
    for case in cases:
        if case.role != "reference_only":
            continue
        target_text = "; ".join(
            f"{target.metric}: {_format_float(target.min)} to "
            f"{_format_float(target.max)} {target.unit}"
            for target in case.targets
        )
        lines.append(
            f"| `{case.id}` | {case.paper} | {case.role} | {case.confidence} | "
            f"{target_text} | {case.notes} |"
        )

    lines.extend(
        [
            "",
            "## Calibration interpretation",
            "",
            (
                "- If the model is consistently below measured Cp for reliable runnable "
                "cases, inspect low-Reynolds polar corrections and practical Cp limits."
            ),
            (
                "- If the model is consistently above measured Cp, inspect Prandtl loss, "
                "surface finish, startup torque, and generator loading assumptions."
            ),
            (
                "- Do not calibrate against reference-only rows until the missing geometry "
                "and load details are added."
            ),
            "",
            "## Next validation data to collect",
            "",
            "- Actual classroom rotor geometry after slicing or printing.",
            "- Wind tunnel speed at the rotor plane.",
            "- Measured RPM, voltage, current, load resistance, and trial duration.",
            "- Blade mass, surface finish, and generator internal resistance.",
            (
                "- To add real classroom benchmarks, export "
                "`classroom_measured_benchmarks.csv` from the Calibration tab or copy "
                "`data/classroom_measured_benchmarks.example.csv`, place the filled file "
                "at `data/classroom_measured_benchmarks.csv`, then regenerate this report."
            ),
            "",
        ]
    )
    return "\n".join(lines)
