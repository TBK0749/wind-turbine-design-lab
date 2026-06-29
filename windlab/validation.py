"""Paper benchmark validation utilities for the wind turbine simulator."""

from __future__ import annotations

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


def load_benchmark_cases(path: Path = Path("data/validation_benchmarks.json")) -> list[BenchmarkCase]:
    """Load benchmark cases from JSON."""

    raw_cases = json.loads(path.read_text())
    return [BenchmarkCase.model_validate(raw_case) for raw_case in raw_cases]


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
