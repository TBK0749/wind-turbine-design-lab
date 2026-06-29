"""Paper benchmark validation utilities for the wind turbine simulator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


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
