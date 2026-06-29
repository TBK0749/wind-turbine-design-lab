from pathlib import Path

import pytest

from windlab.validation import BenchmarkTarget, compare_prediction_to_target
from windlab.validation import load_benchmark_cases
from windlab.validation import run_benchmark_case


def test_load_benchmark_cases_contains_supplied_papers() -> None:
    cases = load_benchmark_cases(Path("data/validation_benchmarks.json"))

    case_ids = {case.id for case in cases}
    assert "swept_final_cp_4ms" in case_ids
    assert "conf4_naca4412_power_10ms_range" in case_ids
    assert "riej_no_diffuser_cp_reference" in case_ids
    assert any("SWEPT" in case.paper for case in cases)


def test_compare_prediction_inside_target_range() -> None:
    target = BenchmarkTarget(metric="cp", min=0.31, max=0.34, unit="dimensionless")

    comparison = compare_prediction_to_target(0.325, target)

    assert comparison.status == "within_range"
    assert comparison.error_percent == pytest.approx(0.0)


def test_compare_prediction_outside_target_range_uses_nearest_bound() -> None:
    target = BenchmarkTarget(metric="cp", min=0.31, max=0.34, unit="dimensionless")

    comparison = compare_prediction_to_target(0.20, target)

    assert comparison.status == "below_range"
    assert comparison.error_percent == pytest.approx(-35.4838709677)


def test_reference_only_case_is_not_simulated() -> None:
    case = next(case for case in load_benchmark_cases() if case.id == "riej_no_diffuser_cp_reference")

    result = run_benchmark_case(case)

    assert result.simulated is False
    assert result.predictions == {}
    assert result.comparisons == []


def test_runnable_case_produces_core_predictions() -> None:
    case = next(
        case
        for case in load_benchmark_cases()
        if case.id == "classroom_competition_baseline_3_6ms"
    )

    result = run_benchmark_case(case)

    assert result.simulated is True
    assert result.predictions["cp"] >= 0.0
    assert result.predictions["rpm"] >= 0.0
    assert result.predictions["mechanical_power_w"] >= 0.0
    assert result.predictions["electrical_power_mw"] >= 0.0
