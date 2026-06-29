# Model Validation Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible Model Validation Report that compares the current simulator against benchmark values extracted from the supplied small-wind-turbine papers.

**Architecture:** Add a small validation layer outside the Streamlit UI. Benchmark cases live in `data/validation_benchmarks.json`, `windlab/validation.py` loads them, runs `simulate()`, computes range/error metrics, and renders a Markdown report to `docs/model_validation_report.md`. The first version separates runnable comparisons from low-confidence reference-only paper values so the model is not calibrated against incomplete geometry.

**Tech Stack:** Python 3.12, Pydantic models already in `windlab.models`, existing `windlab.simulator.simulate`, JSON benchmark data, Markdown report generation, pytest, ruff.

---

## File structure

- Create `data/validation_benchmarks.json`
  - Stores paper benchmark cases, target ranges, confidence level, source notes, and simulator inputs.
- Create `windlab/validation.py`
  - Defines benchmark dataclasses/Pydantic models.
  - Loads benchmark JSON.
  - Runs runnable cases through `simulate()`.
  - Computes percent error or in-range status.
  - Renders Markdown report tables.
- Create `scripts/generate_validation_report.py`
  - CLI entry point that writes `docs/model_validation_report.md`.
- Create `docs/model_validation_report.md`
  - Generated report committed to the repo for teachers and students.
- Create `tests/test_validation.py`
  - Unit tests for benchmark loading, metric calculation, runnable/reference-only behavior, and report rendering.
- Modify `README.md`
  - Link the validation report and explain that the simulator is paper-checked but not full QBlade.
- Modify `docs/physics_model.md`
  - Add a short validation status section pointing to the report.
- Modify `tests/test_project_docs.py`
  - Assert that README and physics docs link to the validation report.

---

## Benchmark case policy

The report must classify each paper value into one of these roles:

- `runnable`: enough geometry and test-condition data exists to run a model comparison.
- `range_check`: enough information exists for a broad sanity check, but geometry/load details are incomplete.
- `reference_only`: useful paper result, but not enough geometry/load detail to compute a fair error percentage.

Calibration decisions must only use `runnable` or high-confidence `range_check` cases. `reference_only` rows can guide discussion but must not be used to tune constants.

---

## Task 1: Add benchmark dataset

**Files:**
- Create: `data/validation_benchmarks.json`
- Test: `tests/test_validation.py`

- [ ] **Step 1: Write the failing test for benchmark loading**

Add this to `tests/test_validation.py`:

```python
from pathlib import Path

from windlab.validation import load_benchmark_cases


def test_load_benchmark_cases_contains_supplied_papers() -> None:
    cases = load_benchmark_cases(Path("data/validation_benchmarks.json"))

    case_ids = {case.id for case in cases}
    assert "swept_final_cp_4ms" in case_ids
    assert "conf4_naca4412_power_10ms_range" in case_ids
    assert "riej_no_diffuser_cp_reference" in case_ids
    assert any("SWEPT" in case.paper for case in cases)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/test_validation.py::test_load_benchmark_cases_contains_supplied_papers -q
```

Expected: FAIL because `windlab.validation` does not exist.

- [ ] **Step 3: Create the benchmark JSON**

Create `data/validation_benchmarks.json` with this exact starting dataset:

```json
[
  {
    "id": "swept_final_cp_4ms",
    "paper": "Small-scale Wind Energy Portable Turbine (SWEPT).pdf",
    "source_detail": "SWEPT final 40 cm rotor reports Cp around 0.31 to 0.34 near the 4.0 m/s design condition.",
    "role": "range_check",
    "confidence": "medium",
    "notes": "Rotor diameter and wind speed are known. Detailed chord/twist/polar data must be checked again before using this as a strict calibration target.",
    "inputs": {
      "wind_speed_m_s": 4.0,
      "air_density_kg_m3": 1.225,
      "rotor_radius_m": 0.20,
      "hub_radius_m": 0.03,
      "blade_count": 3,
      "root_chord_m": 0.045,
      "tip_chord_m": 0.012,
      "pitch_angle_deg": 2.0,
      "twist_angle_deg": 18.0,
      "airfoil_type": "High-lift airfoil",
      "blade_mass_kg": 0.05,
      "surface_finish": "Smooth molded",
      "use_bemt_lite_section_model": false
    },
    "targets": [
      {
        "metric": "cp",
        "min": 0.31,
        "max": 0.34,
        "unit": "dimensionless"
      }
    ]
  },
  {
    "id": "swept_electrical_power_reference",
    "paper": "Small-scale Wind Energy Portable Turbine (SWEPT).pdf",
    "source_detail": "SWEPT reports about 1 W electrical output at 4.0 m/s and about 2.2 W at 5.5 m/s.",
    "role": "reference_only",
    "confidence": "medium",
    "notes": "Electrical output depends on generator/load details that are not equivalent to the classroom generator model.",
    "inputs": {},
    "targets": [
      {
        "metric": "electrical_power_w",
        "min": 1.0,
        "max": 1.0,
        "unit": "W at 4.0 m/s"
      },
      {
        "metric": "electrical_power_w",
        "min": 2.2,
        "max": 2.2,
        "unit": "W at 5.5 m/s"
      }
    ]
  },
  {
    "id": "conf4_naca4412_power_10ms_range",
    "paper": "Conf4_Experimental Study of Small-Scale Wind Turbine Rotors_EEAE_2020.pdf",
    "source_detail": "3D printed ABS rotors using NACA 4412, about 524-620 mm diameter, tested at 10 m/s; reported rotor power ranges roughly 22 W to 48 W depending rotor configuration.",
    "role": "range_check",
    "confidence": "low",
    "notes": "This is a broad family check because exact tested pitch/geometry variants are not yet encoded one by one.",
    "inputs": {
      "wind_speed_m_s": 10.0,
      "air_density_kg_m3": 1.225,
      "rotor_radius_m": 0.31,
      "hub_radius_m": 0.05,
      "blade_count": 3,
      "root_chord_m": 0.08,
      "tip_chord_m": 0.04,
      "pitch_angle_deg": 5.0,
      "twist_angle_deg": 8.0,
      "airfoil_type": "High-lift airfoil",
      "blade_mass_kg": 0.18,
      "material": "Plastic",
      "surface_finish": "Raw 3D print",
      "use_bemt_lite_section_model": false
    },
    "targets": [
      {
        "metric": "mechanical_power_w",
        "min": 22.0,
        "max": 48.0,
        "unit": "W"
      }
    ]
  },
  {
    "id": "riej_no_diffuser_cp_reference",
    "paper": "riej.2022.364299.1341.pdf",
    "source_detail": "No-diffuser small rotor reported Cp around 0.09 at 3-4 m/s and up to about 0.22 at 7 m/s; diffuser cases were higher.",
    "role": "reference_only",
    "confidence": "medium",
    "notes": "Useful low-speed Cp range, but diffuser/no-diffuser geometry and test setup are not equivalent to the classroom rotor.",
    "inputs": {},
    "targets": [
      {
        "metric": "cp",
        "min": 0.09,
        "max": 0.22,
        "unit": "dimensionless"
      }
    ]
  },
  {
    "id": "optimization_large_rotor_cp_5_5ms",
    "paper": "Small_Wind_Turbine_Blade_Design_and_Optimization.pdf",
    "source_detail": "BEM/QBlade-style optimization example: 3 blades, 4 m diameter, hub about 0.2 m, design TSR 6.5, Cp about 0.445 at 5.5 m/s.",
    "role": "range_check",
    "confidence": "medium",
    "notes": "Larger and cleaner than the classroom rotor. This checks whether the simulator can reach a plausible higher Cp when scale and surface assumptions improve.",
    "inputs": {
      "wind_speed_m_s": 5.5,
      "air_density_kg_m3": 1.225,
      "rotor_radius_m": 2.0,
      "hub_radius_m": 0.10,
      "blade_count": 3,
      "root_chord_m": 0.22,
      "tip_chord_m": 0.06,
      "pitch_angle_deg": 2.0,
      "twist_angle_deg": 14.0,
      "airfoil_type": "High-lift airfoil",
      "blade_mass_kg": 1.2,
      "surface_finish": "Smooth molded",
      "practical_cp_limit": 0.50,
      "use_bemt_lite_section_model": false
    },
    "targets": [
      {
        "metric": "cp",
        "min": 0.42,
        "max": 0.47,
        "unit": "dimensionless"
      }
    ]
  },
  {
    "id": "classroom_competition_baseline_3_6ms",
    "paper": "Internal classroom target",
    "source_detail": "Competition wind tunnel target is 3.6 m/s. This row records the current model prediction for the default classroom blade and is not a paper validation case.",
    "role": "runnable",
    "confidence": "high",
    "notes": "Use this as the local project baseline. Add measured tunnel data here after the first prototype test.",
    "inputs": {
      "wind_speed_m_s": 3.6,
      "air_density_kg_m3": 1.225,
      "rotor_radius_m": 0.45,
      "hub_radius_m": 0.10,
      "blade_count": 3,
      "blade_mass_kg": 0.10,
      "material": "Plastic",
      "surface_finish": "Raw 3D print",
      "trial_duration_s": 60.0
    },
    "use_competition_sections": true,
    "targets": []
  }
]
```

- [ ] **Step 4: Create the minimal validation loader**

Create `windlab/validation.py`:

```python
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


def load_benchmark_cases(path: Path = Path("data/validation_benchmarks.json")) -> list[BenchmarkCase]:
    """Load benchmark cases from JSON."""

    raw_cases = json.loads(path.read_text())
    return [BenchmarkCase.model_validate(raw_case) for raw_case in raw_cases]
```

- [ ] **Step 5: Run the benchmark-loading test**

Run:

```bash
.venv/bin/pytest tests/test_validation.py::test_load_benchmark_cases_contains_supplied_papers -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add data/validation_benchmarks.json windlab/validation.py tests/test_validation.py
git commit -m "feat: add paper validation benchmark dataset"
```

---

## Task 2: Add validation metric calculation

**Files:**
- Modify: `windlab/validation.py`
- Modify: `tests/test_validation.py`

- [ ] **Step 1: Write failing tests for range comparison**

Append to `tests/test_validation.py`:

```python
import pytest

from windlab.validation import BenchmarkTarget, compare_prediction_to_target


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
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/pytest tests/test_validation.py::test_compare_prediction_inside_target_range tests/test_validation.py::test_compare_prediction_outside_target_range_uses_nearest_bound -q
```

Expected: FAIL because `compare_prediction_to_target` is not implemented.

- [ ] **Step 3: Implement comparison objects**

Add to `windlab/validation.py`:

```python
class TargetComparison(BaseModel):
    """Comparison between one prediction and one target range."""

    metric: str
    predicted: float
    target_min: float
    target_max: float
    unit: str
    status: Literal["within_range", "below_range", "above_range"]
    error_percent: float


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
```

- [ ] **Step 4: Run tests**

Run:

```bash
.venv/bin/pytest tests/test_validation.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add windlab/validation.py tests/test_validation.py
git commit -m "feat: compare model predictions to benchmark ranges"
```

---

## Task 3: Run simulator against runnable benchmark cases

**Files:**
- Modify: `windlab/validation.py`
- Modify: `tests/test_validation.py`

- [ ] **Step 1: Write failing tests for running benchmark cases**

Append to `tests/test_validation.py`:

```python
from windlab.validation import run_benchmark_case


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
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/pytest tests/test_validation.py::test_reference_only_case_is_not_simulated tests/test_validation.py::test_runnable_case_produces_core_predictions -q
```

Expected: FAIL because `run_benchmark_case` is not implemented.

- [ ] **Step 3: Implement benchmark execution**

Modify `windlab/validation.py`:

```python
from windlab.blade_geometry import competition_50cm_sections
from windlab.models import SimulationInput
from windlab.simulator import simulate
```

Add:

```python
class BenchmarkRunResult(BaseModel):
    """Simulator output and target comparisons for one benchmark case."""

    case_id: str
    simulated: bool
    predictions: dict[str, float] = Field(default_factory=dict)
    comparisons: list[TargetComparison] = Field(default_factory=list)


def _prediction_map_from_result(result) -> dict[str, float]:
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
```

- [ ] **Step 4: Run tests**

Run:

```bash
.venv/bin/pytest tests/test_validation.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add windlab/validation.py tests/test_validation.py
git commit -m "feat: run model validation benchmark cases"
```

---

## Task 4: Render Markdown Model Validation Report

**Files:**
- Modify: `windlab/validation.py`
- Create: `scripts/generate_validation_report.py`
- Create: `docs/model_validation_report.md`
- Modify: `tests/test_validation.py`

- [ ] **Step 1: Write failing test for report rendering**

Append to `tests/test_validation.py`:

```python
from windlab.validation import render_validation_report


def test_render_validation_report_includes_core_sections() -> None:
    cases = load_benchmark_cases()
    report = render_validation_report(cases)

    assert "# Model Validation Report" in report
    assert "## Runnable and range-check comparisons" in report
    assert "## Reference-only paper results" in report
    assert "swept_final_cp_4ms" in report
    assert "reference_only" in report
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
.venv/bin/pytest tests/test_validation.py::test_render_validation_report_includes_core_sections -q
```

Expected: FAIL because `render_validation_report` is not implemented.

- [ ] **Step 3: Implement Markdown rendering**

Add to `windlab/validation.py`:

```python
def _format_float(value: float) -> str:
    """Format validation numbers consistently."""

    if abs(value) >= 100:
        return f"{value:.1f}"
    if abs(value) >= 10:
        return f"{value:.2f}"
    return f"{value:.4f}"


def render_validation_report(cases: list[BenchmarkCase]) -> str:
    """Render the full model validation report as Markdown."""

    run_results = {case.id: run_benchmark_case(case) for case in cases}
    lines: list[str] = [
        "# Model Validation Report",
        "",
        "This report compares the current educational simulator with benchmark values extracted from the supplied small-wind-turbine papers.",
        "",
        "The report separates strict comparisons from reference-only paper values. Reference-only rows are not used for calibration because geometry, load, or generator details are incomplete.",
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
            lines.append(
                f"| `{case.id}` | {case.paper} | {case.role} | {case.confidence} | prediction only | - | - | recorded | - |"
            )
            continue
        for comparison in result.comparisons:
            target_range = (
                f"{_format_float(comparison.target_min)} to "
                f"{_format_float(comparison.target_max)} {comparison.unit}"
            )
            lines.append(
                f"| `{case.id}` | {case.paper} | {case.role} | {case.confidence} | "
                f"{comparison.metric} | {target_range} | {_format_float(comparison.predicted)} | "
                f"{comparison.status} | {comparison.error_percent:.1f}% |"
            )

    lines.extend(
        [
            "",
            "## Reference-only paper results",
            "",
            "| Case | Paper | Confidence | Paper value | Why reference-only |",
            "|---|---|---|---|---|",
        ]
    )
    for case in cases:
        if case.role != "reference_only":
            continue
        target_text = "; ".join(
            f"{target.metric}: {_format_float(target.min)} to {_format_float(target.max)} {target.unit}"
            for target in case.targets
        )
        lines.append(
            f"| `{case.id}` | {case.paper} | {case.confidence} | {target_text} | {case.notes} |"
        )

    lines.extend(
        [
            "",
            "## Calibration interpretation",
            "",
            "- If the model is consistently below measured Cp for reliable runnable cases, inspect low-Reynolds penalties and practical Cp limits.",
            "- If the model is consistently above measured Cp, inspect Prandtl loss, surface finish, startup torque, and generator loading assumptions.",
            "- Do not calibrate against reference-only rows until the missing geometry and load details are added.",
            "",
            "## Next validation data to collect",
            "",
            "- Actual classroom rotor geometry after slicing or printing.",
            "- Wind tunnel speed at the rotor plane.",
            "- Measured RPM, voltage, current, load resistance, and trial duration.",
            "- Blade mass, surface finish, and generator internal resistance.",
            "",
        ]
    )
    return "\n".join(lines)
```

- [ ] **Step 4: Create report generation script**

Create `scripts/generate_validation_report.py`:

```python
"""Generate the Markdown model validation report."""

from pathlib import Path

from windlab.validation import load_benchmark_cases, render_validation_report


def main() -> None:
    """Generate docs/model_validation_report.md from benchmark data."""

    cases = load_benchmark_cases(Path("data/validation_benchmarks.json"))
    report = render_validation_report(cases)
    Path("docs/model_validation_report.md").write_text(report)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Generate the report**

Run:

```bash
.venv/bin/python scripts/generate_validation_report.py
```

Expected: creates `docs/model_validation_report.md`.

- [ ] **Step 6: Run tests**

Run:

```bash
.venv/bin/pytest tests/test_validation.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add windlab/validation.py scripts/generate_validation_report.py docs/model_validation_report.md tests/test_validation.py
git commit -m "feat: generate model validation report"
```

---

## Task 5: Add documentation links and guard tests

**Files:**
- Modify: `README.md`
- Modify: `docs/physics_model.md`
- Modify: `tests/test_project_docs.py`

- [ ] **Step 1: Write failing doc tests**

Append to `tests/test_project_docs.py`:

```python
def test_docs_link_to_model_validation_report() -> None:
    readme = Path("README.md").read_text()
    physics_doc = Path("docs/physics_model.md").read_text()
    validation_report = Path("docs/model_validation_report.md")

    assert "docs/model_validation_report.md" in readme
    assert "docs/model_validation_report.md" in physics_doc
    assert validation_report.exists()
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
.venv/bin/pytest tests/test_project_docs.py::test_docs_link_to_model_validation_report -q
```

Expected: FAIL until docs are updated.

- [ ] **Step 3: Update README**

Add this paragraph under `## Current physics scope` in `README.md`:

```markdown
The current paper-validation status is tracked in
[`docs/model_validation_report.md`](docs/model_validation_report.md). The report
compares selected paper benchmarks with the simulator and clearly marks which
rows are runnable, broad range checks, or reference-only values.
```

- [ ] **Step 4: Update physics model documentation**

Add this section near the end of `docs/physics_model.md`:

```markdown
## Validation status

The simulator is checked against selected values from the supplied small-wind
turbine papers in `docs/model_validation_report.md`. Rows marked `runnable` or
`range_check` can be used for model-error discussion. Rows marked
`reference_only` document useful paper results but are not used for calibration
until matching geometry and generator/load details are available.
```

- [ ] **Step 5: Run doc test**

Run:

```bash
.venv/bin/pytest tests/test_project_docs.py::test_docs_link_to_model_validation_report -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add README.md docs/physics_model.md tests/test_project_docs.py
git commit -m "docs: link model validation report"
```

---

## Task 6: Full verification and final report regeneration

**Files:**
- Regenerate: `docs/model_validation_report.md`
- No new code files.

- [ ] **Step 1: Regenerate the report from the benchmark dataset**

Run:

```bash
.venv/bin/python scripts/generate_validation_report.py
```

Expected: `docs/model_validation_report.md` updates deterministically.

- [ ] **Step 2: Run all tests**

Run:

```bash
.venv/bin/pytest -q
```

Expected: all tests pass.

- [ ] **Step 3: Run lint**

Run:

```bash
.venv/bin/ruff check .
```

Expected: `All checks passed!`

- [ ] **Step 4: Run format check**

Run:

```bash
.venv/bin/ruff format --check .
```

Expected: all files already formatted.

- [ ] **Step 5: Inspect final status**

Run:

```bash
git status --short
```

Expected: only intended validation/report/docs files are modified.

- [ ] **Step 6: Final commit**

If Task 6 changed the generated report after previous commits:

```bash
git add docs/model_validation_report.md
git commit -m "docs: refresh model validation report"
```

If Task 6 did not change files, do not create an empty commit.

---

## Self-review checklist

- Spec coverage:
  - Validation table per paper: covered by `data/validation_benchmarks.json` and `docs/model_validation_report.md`.
  - Predicted vs measured/range values: covered by `compare_prediction_to_target` and report tables.
  - Calibration status: covered by report interpretation section.
  - Full BEMT and airfoil polar data: explicitly not implemented in this report; documented as next model-improvement candidates after validation results show which error dominates.
- Placeholder scan:
  - No placeholder markers or unspecified implementation steps are used.
  - Low-confidence rows are explicitly labeled and excluded from strict calibration.
- Type consistency:
  - `BenchmarkCase`, `BenchmarkTarget`, `TargetComparison`, and `BenchmarkRunResult` are defined before later tasks use them.
  - Metric names in JSON match `_prediction_map_from_result`.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-29-model-validation-report.md`.

Two execution options:

1. **Subagent-Driven (recommended)** - dispatch a fresh subagent per task, review between tasks, faster iteration.
2. **Inline Execution** - execute tasks in this session using executing-plans, with checkpoints after each task.
