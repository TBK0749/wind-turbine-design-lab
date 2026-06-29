import csv
from pathlib import Path

import pytest

from windlab.validation import (
    BenchmarkTarget,
    compare_prediction_to_target,
    load_benchmark_cases,
    load_measured_classroom_benchmarks,
    render_validation_report,
    run_benchmark_case,
)


def test_load_benchmark_cases_contains_supplied_papers() -> None:
    cases = load_benchmark_cases(Path("data/validation_benchmarks.json"))

    case_ids = {case.id for case in cases}
    assert "swept_final_cp_4ms" in case_ids
    assert "conf4_naca4412_power_10ms_range" in case_ids
    assert "riej_no_diffuser_cp_reference" in case_ids
    assert any("SWEPT" in case.paper for case in cases)


def test_measured_benchmark_template_has_required_columns() -> None:
    template = Path("data/classroom_measured_benchmarks.example.csv")

    with template.open(newline="") as csv_file:
        fieldnames = csv.DictReader(csv_file).fieldnames or []

    assert "design_name" in fieldnames
    assert "wind_speed_m_s" in fieldnames
    assert "measured_rpm" in fieldnames
    assert "measured_power_mw" in fieldnames
    assert "use_competition_sections" in fieldnames


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
    case = next(
        case for case in load_benchmark_cases() if case.id == "riej_no_diffuser_cp_reference"
    )

    result = run_benchmark_case(case)

    assert result.simulated is False
    assert result.predictions == {}
    assert result.comparisons == []


def test_runnable_case_produces_core_predictions() -> None:
    case = next(
        case for case in load_benchmark_cases() if case.id == "classroom_competition_baseline_3_6ms"
    )

    result = run_benchmark_case(case)

    assert result.simulated is True
    assert result.predictions["cp"] >= 0.0
    assert result.predictions["rpm"] >= 0.0
    assert result.predictions["mechanical_power_w"] >= 0.0
    assert result.predictions["electrical_power_mw"] >= 0.0


def test_render_validation_report_includes_core_sections() -> None:
    cases = load_benchmark_cases()
    report = render_validation_report(cases)

    assert "# Model Validation Report" in report
    assert "## Runnable and range-check comparisons" in report
    assert "## Reference-only paper results" in report
    assert "swept_final_cp_4ms" in report
    assert "reference_only" in report
    assert "classroom_measured_benchmarks.csv" in report


def test_polar_model_moves_key_paper_benchmarks_closer_to_targets() -> None:
    cases = {case.id: case for case in load_benchmark_cases()}

    swept = run_benchmark_case(cases["swept_final_cp_4ms"])
    conf4 = run_benchmark_case(cases["conf4_naca4412_power_10ms_range"])
    optimized = run_benchmark_case(cases["optimization_large_rotor_cp_5_5ms"])

    assert swept.predictions["cp"] > 0.21
    assert optimized.predictions["cp"] > 0.33
    assert conf4.comparisons[0].status == "within_range"


def test_load_measured_classroom_benchmarks_from_csv(tmp_path: Path) -> None:
    measured_csv = tmp_path / "classroom_measured_benchmarks.csv"
    measured_csv.write_text(
        "\n".join(
            [
                "case_id,design_name,wind_speed_m_s,air_density_kg_m3,rotor_radius_m,"
                "hub_radius_m,blade_count,blade_mass_kg,material,surface_finish,"
                "trial_duration_s,generator_volts_per_1000_rpm,"
                "generator_internal_resistance_ohm,load_resistance_ohm,"
                "generator_efficiency_percent,gear_ratio,use_competition_sections,"
                "measured_rpm,measured_power_mw,tolerance_percent,notes",
                "prototype_a,Prototype A,3.6,1.225,0.45,0.10,3,0.10,Plastic,"
                "Raw 3D print,60,1.5,20,100,70,1,true,420,2.5,10,"
                "first measured 3D print",
            ]
        )
    )

    cases = load_measured_classroom_benchmarks(measured_csv)

    assert len(cases) == 1
    case = cases[0]
    assert case.id == "measured_prototype_a"
    assert case.paper == "Measured classroom benchmark"
    assert case.use_competition_sections is True
    assert case.inputs["wind_speed_m_s"] == 3.6
    assert case.targets[0].metric == "rpm"
    assert case.targets[0].min == pytest.approx(378.0)
    assert case.targets[0].max == pytest.approx(462.0)
    assert case.targets[1].metric == "electrical_power_mw"
    assert case.targets[1].min == pytest.approx(2.25)
    assert case.targets[1].max == pytest.approx(2.75)


def test_load_benchmark_cases_appends_measured_classroom_csv(tmp_path: Path) -> None:
    benchmark_json = tmp_path / "validation_benchmarks.json"
    measured_csv = tmp_path / "classroom_measured_benchmarks.csv"
    benchmark_json.write_text("[]")
    measured_csv.write_text(
        "\n".join(
            [
                "design_name,wind_speed_m_s,rotor_radius_m,measured_rpm,measured_power_mw",
                "Prototype B,3.6,0.45,400,2.0",
            ]
        )
    )

    cases = load_benchmark_cases(benchmark_json, measured_path=measured_csv)

    assert [case.id for case in cases] == ["measured_prototype_b"]
    report = render_validation_report(cases)
    assert "Measured classroom benchmark" in report
    assert "electrical_power_mw" in report
