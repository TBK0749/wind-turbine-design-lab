# Local Workspace and Onshape Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local persistence, undo/redo, named design storage, 1 m rotor presets, and an Onshape-ready ZIP export package.

**Architecture:** Keep aerodynamic calculations unchanged. Add focused domain modules for design serialization, SQLite storage, presets, and Onshape export, then wire them into Streamlit via a compact workspace component and export button. Use local `user_data/` only; no network, login, or shared database.

**Tech Stack:** Python 3.12 stdlib (`sqlite3`, `json`, `zipfile`, `csv`, `io`, `datetime`, `pathlib`), Streamlit, pandas, Pydantic, pytest, Ruff.

---

## File structure

- Create: `windlab/design_state.py`
  - Convert `SimulationInput` to/from JSON-safe dictionaries.
  - Provide default competition design input.
- Create: `windlab/design_store.py`
  - SQLite local design store.
  - Autosave, named save/load/list behavior.
- Create: `windlab/blade_presets.py`
  - Five 3-blade, 1 m diameter starting presets.
- Create: `windlab/onshape_export.py`
  - Generate CSV/DXF/JSON/Markdown files and package them into a ZIP.
- Create: `app/components/design_workspace.py`
  - Render Undo/Redo/Reset/Save/Load/Preset workspace controls.
- Modify: `app/components/input_panel.py`
  - Read defaults from `st.session_state["active_design"]`.
  - Use stable widget keys.
  - Allow preset/load/reset to update the table and sidebar defaults.
- Modify: `app/main.py`
  - Initialize local workspace.
  - Autosave current design.
  - Add Onshape package download button.
- Modify: `.gitignore`
  - Ignore `user_data/`.
- Modify: `app/components/learning_guide.py`
  - Explain local save/restore and Onshape package workflow.
- Modify: `README.md`
  - Mention local database and Onshape package export.
- Test: `tests/test_design_state.py`
- Test: `tests/test_design_store.py`
- Test: `tests/test_blade_presets.py`
- Test: `tests/test_onshape_export.py`
- Modify: `tests/test_app.py`
- Modify: `tests/test_project_docs.py`

## Task 1: Design serialization and default state

**Files:**
- Create: `tests/test_design_state.py`
- Create: `windlab/design_state.py`

- [ ] **Step 1: Write failing serialization tests**

Create `tests/test_design_state.py`:

```python
from windlab.blade_geometry import competition_50cm_sections
from windlab.design_state import (
    DEFAULT_DESIGN_NAME,
    default_design_input,
    design_input_from_dict,
    design_input_to_dict,
)
from windlab.models import SimulationInput


def test_design_input_round_trips_blade_sections() -> None:
    original = SimulationInput(
        wind_speed_m_s=3.6,
        rotor_radius_m=0.50,
        hub_radius_m=0.08,
        blade_count=3,
        blade_sections=competition_50cm_sections(),
        generator_volts_per_1000_rpm=2.0,
    )

    payload = design_input_to_dict(original)
    restored = design_input_from_dict(payload)

    assert restored.wind_speed_m_s == 3.6
    assert restored.rotor_radius_m == 0.50
    assert restored.hub_radius_m == 0.08
    assert restored.blade_count == 3
    assert restored.generator_volts_per_1000_rpm == 2.0
    assert restored.blade_sections[0].airfoil_name == "NACA 4418"
    assert restored.blade_sections[-1].airfoil_name == "NACA 2412"


def test_default_design_input_matches_competition_starting_point() -> None:
    default = default_design_input()

    assert DEFAULT_DESIGN_NAME == "Current design"
    assert default.rotor_radius_m == 0.45
    assert default.blade_count == 3
    assert len(default.blade_sections) == 6
```

- [ ] **Step 2: Run test and confirm failure**

Run:

```bash
.venv/bin/pytest tests/test_design_state.py -q
```

Expected: FAIL because `windlab.design_state` does not exist.

- [ ] **Step 3: Implement design state module**

Create `windlab/design_state.py`:

```python
"""Serialization helpers for local design persistence."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from windlab.blade_geometry import competition_50cm_sections
from windlab.models import SimulationInput

DEFAULT_DESIGN_NAME = "Current design"
DESIGN_SCHEMA_VERSION = 1


def default_design_input() -> SimulationInput:
    """Return the default competition-oriented design."""

    return SimulationInput(
        wind_speed_m_s=3.6,
        rotor_radius_m=0.45,
        hub_radius_m=0.10,
        blade_count=3,
        blade_sections=competition_50cm_sections(),
    )


def design_input_to_dict(inputs: SimulationInput) -> dict[str, Any]:
    """Return a JSON-safe dictionary for a simulation input."""

    payload = inputs.model_dump(mode="json")
    payload["schema_version"] = DESIGN_SCHEMA_VERSION
    return deepcopy(payload)


def design_input_from_dict(payload: dict[str, Any]) -> SimulationInput:
    """Build a SimulationInput from a JSON-safe dictionary."""

    clean_payload = dict(payload)
    clean_payload.pop("schema_version", None)
    return SimulationInput.model_validate(clean_payload)
```

- [ ] **Step 4: Run serialization tests**

Run:

```bash
.venv/bin/pytest tests/test_design_state.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add windlab/design_state.py tests/test_design_state.py
git commit -m "feat: add design state serialization"
```

## Task 2: SQLite local design store

**Files:**
- Create: `tests/test_design_store.py`
- Create: `windlab/design_store.py`
- Modify: `.gitignore`

- [ ] **Step 1: Write failing store tests**

Create `tests/test_design_store.py`:

```python
from pathlib import Path

from windlab.design_state import default_design_input
from windlab.design_store import DesignStore


def test_design_store_saves_and_loads_named_design(tmp_path: Path) -> None:
    store = DesignStore(tmp_path / "windlab.sqlite")
    inputs = default_design_input().model_copy(update={"wind_speed_m_s": 3.6})

    store.save_named_design("Team A v1", inputs)
    names = store.list_design_names()
    loaded = store.load_named_design("Team A v1")

    assert names == ["Team A v1"]
    assert loaded is not None
    assert loaded.wind_speed_m_s == 3.6
    assert loaded.blade_sections[0].airfoil_name == "NACA 4418"


def test_design_store_autosaves_current_design(tmp_path: Path) -> None:
    store = DesignStore(tmp_path / "windlab.sqlite")
    inputs = default_design_input().model_copy(update={"rotor_radius_m": 0.50})

    store.autosave_current(inputs)
    loaded = store.load_current_design()

    assert loaded is not None
    assert loaded.rotor_radius_m == 0.50


def test_design_store_creates_parent_directory(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "windlab.sqlite"

    store = DesignStore(db_path)
    store.autosave_current(default_design_input())

    assert db_path.exists()
```

- [ ] **Step 2: Run store test and confirm failure**

Run:

```bash
.venv/bin/pytest tests/test_design_store.py -q
```

Expected: FAIL because `windlab.design_store` does not exist.

- [ ] **Step 3: Implement store**

Create `windlab/design_store.py`:

```python
"""Local SQLite design storage for each installed copy of the app."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from windlab.design_state import design_input_from_dict, design_input_to_dict
from windlab.models import SimulationInput

DEFAULT_USER_DATA_DIR = Path("user_data")
DEFAULT_DATABASE_PATH = DEFAULT_USER_DATA_DIR / "windlab.sqlite"


class DesignStore:
    """Small SQLite store for autosaved and named designs."""

    def __init__(self, database_path: Path = DEFAULT_DATABASE_PATH) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS designs (
                    name TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    is_current INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def _save(self, name: str, inputs: SimulationInput, *, is_current: bool) -> None:
        payload_json = json.dumps(design_input_to_dict(inputs), sort_keys=True)
        now = self._now()
        with self._connect() as connection:
            if is_current:
                connection.execute("UPDATE designs SET is_current = 0 WHERE is_current = 1")
            connection.execute(
                """
                INSERT INTO designs (name, payload_json, is_current, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    is_current = excluded.is_current,
                    updated_at = excluded.updated_at
                """,
                (name, payload_json, 1 if is_current else 0, now, now),
            )
            connection.commit()

    def autosave_current(self, inputs: SimulationInput) -> None:
        """Save the current working design."""

        self._save("__current__", inputs, is_current=True)

    def load_current_design(self) -> SimulationInput | None:
        """Load the current autosaved design if available."""

        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM designs WHERE is_current = 1 LIMIT 1"
            ).fetchone()
        if row is None:
            return None
        return design_input_from_dict(json.loads(row[0]))

    def save_named_design(self, name: str, inputs: SimulationInput) -> None:
        """Save a named design."""

        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Design name cannot be blank.")
        self._save(clean_name, inputs, is_current=False)

    def load_named_design(self, name: str) -> SimulationInput | None:
        """Load a named design."""

        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM designs WHERE name = ? AND is_current = 0",
                (name,),
            ).fetchone()
        if row is None:
            return None
        return design_input_from_dict(json.loads(row[0]))

    def list_design_names(self) -> list[str]:
        """Return saved design names in display order."""

        with self._connect() as connection:
            rows = connection.execute(
                "SELECT name FROM designs WHERE is_current = 0 ORDER BY updated_at DESC, name"
            ).fetchall()
        return [row[0] for row in rows]
```

- [ ] **Step 4: Ignore local database folder**

Append to `.gitignore`:

```text
user_data/
```

- [ ] **Step 5: Run store tests**

Run:

```bash
.venv/bin/pytest tests/test_design_store.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add .gitignore windlab/design_store.py tests/test_design_store.py
git commit -m "feat: add local design database"
```

## Task 3: Five competition blade presets

**Files:**
- Create: `tests/test_blade_presets.py`
- Create: `windlab/blade_presets.py`

- [ ] **Step 1: Write failing preset tests**

Create `tests/test_blade_presets.py`:

```python
from windlab.blade_presets import blade_preset_options, get_blade_preset


def test_five_presets_fit_one_meter_three_blade_rule() -> None:
    presets = blade_preset_options()

    assert len(presets) == 5
    for preset in presets:
        assert preset.rotor_radius_m == 0.50
        assert preset.blade_count == 3
        assert len(preset.sections) == 6
        assert preset.sections[-1].position_m <= 0.50
        assert preset.tradeoffs


def test_low_wind_preset_targets_classroom_tunnel() -> None:
    preset = get_blade_preset("Low Wind 3.6 m/s Classroom Tunnel")

    assert preset.wind_speed_m_s == 3.6
    assert preset.sections[2].airfoil_name == "S1223"
    assert "3.6 m/s" in preset.description


def test_preset_names_are_stable() -> None:
    names = [preset.name for preset in blade_preset_options()]

    assert names == [
        "Balanced Competition 50 cm",
        "High Starting Torque",
        "High RPM / Low Drag Tip",
        "Low Wind 3.6 m/s Classroom Tunnel",
        "Easy CAD / Easy Print",
    ]
```

- [ ] **Step 2: Run preset test and confirm failure**

Run:

```bash
.venv/bin/pytest tests/test_blade_presets.py -q
```

Expected: FAIL because `windlab.blade_presets` does not exist.

- [ ] **Step 3: Implement presets**

Create `windlab/blade_presets.py` with dataclass `BladePreset`, helper `_section`, five preset definitions from the approved spec, `blade_preset_options()`, `get_blade_preset(name)`, and `preset_to_simulation_input(preset)`.

Implementation requirements:

- every preset uses `rotor_radius_m=0.50`;
- every preset uses `blade_count=3`;
- low wind preset uses `wind_speed_m_s=3.6`;
- each `BladeSection` role should come from `get_section_airfoil(airfoil).role`.

- [ ] **Step 4: Run preset tests**

Run:

```bash
.venv/bin/pytest tests/test_blade_presets.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add windlab/blade_presets.py tests/test_blade_presets.py
git commit -m "feat: add one meter blade presets"
```

## Task 4: Onshape export package

**Files:**
- Create: `tests/test_onshape_export.py`
- Create: `windlab/onshape_export.py`

- [ ] **Step 1: Write failing Onshape package tests**

Create `tests/test_onshape_export.py`:

```python
import json
import zipfile
from io import BytesIO

from windlab.blade_presets import get_blade_preset, preset_to_simulation_input
from windlab.onshape_export import (
    build_onshape_package,
    blade_geometry_csv,
    blade_planform_dxf,
    section_profiles_dxf,
)


def test_onshape_package_contains_expected_files() -> None:
    inputs = preset_to_simulation_input(get_blade_preset("Balanced Competition 50 cm"))

    package = build_onshape_package(inputs, design_name="Balanced Competition 50 cm")
    with zipfile.ZipFile(BytesIO(package)) as archive:
        names = set(archive.namelist())
        metadata = json.loads(archive.read("design_metadata.json"))

    assert names == {
        "blade_geometry.csv",
        "airfoil_sections.csv",
        "blade_planform.dxf",
        "section_profiles.dxf",
        "design_metadata.json",
        "onshape_build_guide.md",
    }
    assert metadata["design_name"] == "Balanced Competition 50 cm"
    assert metadata["rotor_radius_m"] == 0.5


def test_blade_geometry_csv_contains_sections_and_airfoils() -> None:
    inputs = preset_to_simulation_input(get_blade_preset("High RPM / Low Drag Tip"))

    csv_text = blade_geometry_csv(inputs)

    assert "section,position_m,chord_m,twist_deg,airfoil" in csv_text
    assert "SG6042" in csv_text
    assert "E387" in csv_text


def test_dxf_exports_have_basic_sections() -> None:
    inputs = preset_to_simulation_input(get_blade_preset("Easy CAD / Easy Print"))

    planform = blade_planform_dxf(inputs)
    profiles = section_profiles_dxf(inputs)

    assert "SECTION" in planform
    assert "ENTITIES" in planform
    assert "LWPOLYLINE" in planform
    assert "SECTION" in profiles
    assert "ENTITIES" in profiles
    assert "Clark Y" in profiles
```

- [ ] **Step 2: Run Onshape test and confirm failure**

Run:

```bash
.venv/bin/pytest tests/test_onshape_export.py -q
```

Expected: FAIL because `windlab.onshape_export` does not exist.

- [ ] **Step 3: Implement Onshape export**

Create `windlab/onshape_export.py`.

Required functions:

- `blade_geometry_csv(inputs: SimulationInput) -> str`
- `airfoil_sections_csv(inputs: SimulationInput) -> str`
- `blade_planform_dxf(inputs: SimulationInput) -> str`
- `section_profiles_dxf(inputs: SimulationInput) -> str`
- `onshape_build_guide(inputs: SimulationInput, design_name: str) -> str`
- `build_onshape_package(inputs: SimulationInput, design_name: str = "wind_turbine_design") -> bytes`

Implementation constraints:

- use only stdlib plus existing `windlab.airfoil_geometry.airfoil_profile_points`;
- generate simple ASCII DXF with `SECTION`, `ENTITIES`, `LWPOLYLINE`, and `EOF`;
- planform DXF should draw leading/trailing edge outline in centimetres;
- profiles DXF should place each airfoil profile offset vertically by station index and include a nearby text label;
- ZIP filenames must match the test exactly.

- [ ] **Step 4: Run Onshape tests**

Run:

```bash
.venv/bin/pytest tests/test_onshape_export.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add windlab/onshape_export.py tests/test_onshape_export.py
git commit -m "feat: add onshape export package"
```

## Task 5: Streamlit workspace controls and input defaults

**Files:**
- Create: `app/components/design_workspace.py`
- Modify: `app/components/input_panel.py`
- Modify: `app/main.py`
- Modify: `tests/test_app.py`

- [ ] **Step 1: Add app tests for visible controls**

Append to `tests/test_app.py`:

```python
def test_design_workspace_controls_and_onshape_export_render() -> None:
    app_path = Path(__file__).parents[1] / "app" / "main.py"
    app = AppTest.from_file(str(app_path), default_timeout=15).run()

    assert not app.exception
    assert any(section.value == "Design workspace" for section in app.subheader)
    assert any(button.label == "Undo last change" for button in app.button)
    assert any(button.label == "Redo" for button in app.button)
    assert any(button.label == "Reset to default" for button in app.button)
    assert any(button.label == "Save design" for button in app.button)
    assert any(button.label == "Load design" for button in app.button)
    assert any(button.label == "Load preset" for button in app.button)
    assert any("Download Onshape package" in button.label for button in app.download_button)
```

- [ ] **Step 2: Run app test and confirm failure**

Run:

```bash
.venv/bin/pytest tests/test_app.py::test_design_workspace_controls_and_onshape_export_render -q
```

Expected: FAIL because controls do not exist.

- [ ] **Step 3: Implement workspace component**

Create `app/components/design_workspace.py`.

Required behavior:

- initialize `st.session_state["active_design"]`;
- initialize undo/redo stacks;
- create `DesignStore`;
- load current autosaved design on first render;
- render buttons and controls;
- set `st.session_state["active_design"]` when undo/redo/load/preset/reset happens;
- save named design through `DesignStore`;
- autosave should be called from `app/main.py` after a valid `SimulationInput` exists.

- [ ] **Step 4: Modify input panel to read active defaults**

Modify `render_input_panel()` to:

- read `active_design = st.session_state.get("active_design")`;
- use active design values as widget defaults;
- set stable keys for widgets;
- if `active_design.blade_sections` exists, use it to build the section editor frame instead of `_competition_section_frame()`.

- [ ] **Step 5: Modify main app**

In `app/main.py`:

- import `build_onshape_package`;
- import `render_design_workspace`;
- call `render_design_workspace()` near the top of `with design_tab:`;
- after `simulation_input = render_input_panel()`, write it back to `st.session_state["active_design"]`;
- autosave through store if available;
- add `Download Onshape package` button in the export column.

- [ ] **Step 6: Run app tests**

Run:

```bash
.venv/bin/pytest tests/test_app.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

Run:

```bash
git add app/components/design_workspace.py app/components/input_panel.py app/main.py tests/test_app.py
git commit -m "feat: add local design workspace controls"
```

## Task 6: Documentation

**Files:**
- Modify: `app/components/learning_guide.py`
- Modify: `README.md`
- Modify: `tests/test_project_docs.py`

- [ ] **Step 1: Add documentation tests**

Append to `tests/test_project_docs.py`:

```python
def test_docs_describe_local_workspace_and_onshape_export() -> None:
    readme = Path("README.md").read_text()

    assert "Local design workspace" in readme
    assert "user_data/windlab.sqlite" in readme
    assert "Download Onshape package" in readme
    assert "not a print-ready STL" in readme
```

- [ ] **Step 2: Run doc test and confirm failure**

Run:

```bash
.venv/bin/pytest tests/test_project_docs.py::test_docs_describe_local_workspace_and_onshape_export -q
```

Expected: FAIL because docs do not describe this yet.

- [ ] **Step 3: Update README**

Add section:

```markdown
## Local design workspace

The app stores local saved designs in `user_data/windlab.sqlite`. This database
belongs to the local computer and is ignored by Git. Use the Design workspace
panel to undo/redo, restore after refresh, save named designs, load presets, and
reset to defaults.

## Onshape package export

Use **Download Onshape package** to export a ZIP containing CSV, DXF, JSON, and
a Markdown guide for building the blade in Onshape. This is not a print-ready
STL; it is a CAD starter package so students can inspect, edit, loft, and prepare
their own printable model.
```

- [ ] **Step 4: Update Guide text**

Add Guide text explaining:

- refresh restores last autosave;
- `Command+Z` is replaced by Undo/Redo buttons;
- presets are starting points;
- Onshape export is a CAD starter package, not STL.

- [ ] **Step 5: Run doc tests**

Run:

```bash
.venv/bin/pytest tests/test_project_docs.py tests/test_app.py::test_streamlit_app_renders_english_guide_and_glossary -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add README.md app/components/learning_guide.py tests/test_project_docs.py
git commit -m "docs: explain local workspace and onshape export"
```

## Task 7: Full verification and integration

**Files:**
- Verify all changes.

- [ ] **Step 1: Run full tests**

Run:

```bash
.venv/bin/pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Run lint**

Run:

```bash
.venv/bin/ruff check .
```

Expected: no errors.

- [ ] **Step 3: Run format check**

Run:

```bash
.venv/bin/ruff format --check .
```

Expected: all files formatted.

- [ ] **Step 4: Inspect git status**

Run:

```bash
git status --short --branch
git log --oneline -10
```

Expected: clean feature branch with all commits present.

- [ ] **Step 5: Push or merge after user approval**

Ask whether to merge to `main` and push. If approved:

```bash
git switch main
git merge --ff-only codex/local-workspace-onshape
.venv/bin/pytest -q
git push origin main
```

Expected: GitHub `main` includes the feature.

## Plan self-review checklist

- Spec coverage: local database, autosave, restore, undo/redo, named save/load, presets, Onshape package, docs, and tests are covered.
- Scope control: no STL generation, no cloud database, no login, no Onshape API dependency.
- Type consistency: persistence uses `SimulationInput`; presets use `BladeSection`; Onshape export consumes `SimulationInput`.
- Safety: `user_data/` is git-ignored and database failures must degrade gracefully in UI.
