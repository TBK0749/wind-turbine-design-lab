# Advanced Calibration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add hidden-by-default controls that let teachers manually tune uncertain constants and disable selected model corrections during testing.

**Architecture:** Keep the default student workflow unchanged. Add calibration fields directly to `SimulationInput`, apply them in `windlab.simulator` and `windlab.physics`, and expose them in a collapsed sidebar expander. Model toggles should visibly warn users when custom physics settings are active.

**Tech Stack:** Python, Pydantic, Streamlit, pytest, ruff.

---

### Task 1: Calibration model behavior

**Files:**
- Modify: `windlab/models.py`
- Modify: `windlab/physics.py`
- Modify: `windlab/simulator.py`
- Test: `tests/test_calibration.py`

- [ ] **Step 1: Write failing tests**

```python
from windlab.models import SimulationInput
from windlab.simulator import simulate


def test_custom_practical_cp_limit_caps_cp() -> None:
    result = simulate(
        SimulationInput(
            practical_cp_limit=0.20,
            use_practical_cp_limit=True,
            airfoil_efficiency_multiplier=1.0,
        )
    )

    assert result.cp <= 0.20


def test_disabling_airfoil_correction_changes_result() -> None:
    corrected = simulate(SimulationInput(airfoil_type="Flat plate / Foam board"))
    disabled = simulate(
        SimulationInput(
            airfoil_type="Flat plate / Foam board",
            use_airfoil_correction=False,
        )
    )

    assert disabled.airfoil_efficiency_factor == 1.0
    assert disabled.electrical_power_mw > corrected.electrical_power_mw


def test_startup_torque_can_stop_low_torque_design() -> None:
    result = simulate(
        SimulationInput(
            wind_speed_m_s=2.0,
            startup_torque_n_m=999.0,
            use_startup_torque_loss=True,
        )
    )

    assert result.rpm == 0.0
    assert result.electrical_power_mw == 0.0
    assert any("startup torque" in warning.lower() for warning in result.warnings)
```

- [ ] **Step 2: Run tests and verify they fail**

Run: `.venv/bin/pytest tests/test_calibration.py -q`
Expected: FAIL because the new fields do not exist yet.

- [ ] **Step 3: Implement minimal model fields and simulator behavior**

Add fields for viscosity, Cp limit, efficiency multiplier, friction loss, startup torque, and toggles. Apply the toggles only inside the simulation path so default results remain close to the current behavior.

- [ ] **Step 4: Run calibration tests**

Run: `.venv/bin/pytest tests/test_calibration.py -q`
Expected: PASS.

### Task 2: Streamlit controls and user warnings

**Files:**
- Modify: `app/components/input_panel.py`
- Modify: `app/main.py`
- Test: `tests/test_app.py`

- [ ] **Step 1: Write failing app tests**

```python
from streamlit.testing.v1 import AppTest


def test_advanced_calibration_controls_are_available() -> None:
    app = AppTest.from_file("app/main.py")
    app.run(timeout=10)

    assert any("Advanced calibration" in expander.label for expander in app.expander)
    assert any("Use airfoil correction" in checkbox.label for checkbox in app.checkbox)
    assert any("Startup/cogging torque" in number.label for number in app.number_input)
```

- [ ] **Step 2: Run test and verify it fails**

Run: `.venv/bin/pytest tests/test_app.py::test_advanced_calibration_controls_are_available -q`
Expected: FAIL because the controls are not rendered yet.

- [ ] **Step 3: Add collapsed advanced calibration expander**

Expose advanced controls in the sidebar, defaulting to current values and enabled corrections.

- [ ] **Step 4: Run app tests**

Run: `.venv/bin/pytest tests/test_app.py -q`
Expected: PASS.

### Task 3: Docs and verification

**Files:**
- Modify: `docs/physics_model.md`
- Modify: `app/components/learning_guide.py`
- Modify: `README.md`

- [ ] **Step 1: Document calibration controls**

Explain that defaults are educational, custom settings are for measured competition calibration, and disabled corrections change comparability.

- [ ] **Step 2: Run full verification**

Run:

```bash
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "feat: add advanced calibration controls"
```
