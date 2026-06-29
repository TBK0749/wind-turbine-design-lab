from pathlib import Path

import pytest

from windlab.validation import BenchmarkTarget, compare_prediction_to_target
from windlab.validation import load_benchmark_cases


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
