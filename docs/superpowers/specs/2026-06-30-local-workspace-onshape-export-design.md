# Local Workspace and Onshape Export Design

## Goal

Improve classroom usability by preserving student work across refreshes, adding app-level undo/redo, creating a local database for each cloned installation, providing 1 m-diameter competition blade presets, and exporting an Onshape-ready design package.

## Problem

The current Streamlit app treats most inputs as literal widget defaults. This causes three practical problems:

- Browser `Command+Z` / `Ctrl+Z` cannot reliably undo Streamlit widgets or `st.data_editor` table changes.
- Refreshing the page resets design inputs to defaults.
- Students and teachers who install the repo locally do not have a local design database.

The app also exports CSV/JSON/Markdown result files, but it does not export geometry that can be taken into Onshape for CAD modeling.

## Scope

This phase adds:

- `user_data/` as a local, git-ignored data folder;
- SQLite-backed local design storage at `user_data/windlab.sqlite`;
- autosave of the current design;
- restore of the last autosaved design after refresh;
- app-level Undo and Redo buttons;
- Save / Load named designs;
- Reset to default competition design;
- five 3-blade blade-geometry presets for maximum rotor diameter 1 m;
- Onshape package ZIP export with CSV, DXF, JSON, and Markdown guide files;
- English Guide/Glossary documentation for the new workflow.

## Non-goals

This phase will not:

- create a print-ready STL;
- create a full CAD model automatically in Onshape;
- require a cloud database, login, or shared server;
- synchronize designs between different computers;
- guarantee any preset is competition-winning before real testing;
- replace calibration against measured 3D-print / wind-tunnel data.

## Local database behavior

Each cloned copy of the project stores design data locally in:

```text
user_data/windlab.sqlite
```

The folder must be listed in `.gitignore` so students do not accidentally commit private local designs.

The database stores:

- current autosaved design;
- named saved designs;
- serialized `SimulationInput` data;
- blade section table;
- app schema version;
- created/updated timestamps.

If the database file does not exist, the app creates it automatically. If database access fails, the app continues to work with session-state-only behavior and shows a warning instead of crashing.

## Undo / Redo behavior

Browser undo is not reliable for Streamlit inputs, so the app provides explicit controls:

```text
Undo last change
Redo
Reset to default
Save design
Load design
```

The MVP history model tracks snapshots of complete design inputs. It does not need to detect individual field-level edits. A snapshot is pushed when the rendered input state changes. Undo moves to the previous snapshot; Redo moves forward. History can live in `st.session_state` and does not need to persist across app restarts.

Refresh persistence is handled by the autosaved current design in SQLite.

## Preset design library

The app adds a preset selector for 3-blade competition rotors with maximum diameter 1 m. The preset rotor radius is 0.50 m and blade count is 3.

Presets are starting points, not guaranteed winners. Each preset includes:

- name;
- short description;
- design intent;
- trade-off labels;
- blade section table;
- recommended use case.

### Preset 1: Balanced Competition 50 cm

General starting point balancing torque, RPM, and printability.

| Section | Position cm | Chord cm | Twist deg | Airfoil |
|---|---:|---:|---:|---|
| 1 (Root) | 6 | 9.0 | 20 | NACA 4418 |
| 2 | 14 | 7.5 | 15 | SG6040 |
| 3 | 24 | 5.8 | 10 | SG6043 |
| 4 | 34 | 4.2 | 6 | SG6043 |
| 5 | 43 | 3.0 | 2 | NACA 2412 |
| 6 (Tip) | 50 | 1.8 | 0 | E387 |

### Preset 2: High Starting Torque

For generators with higher cogging/startup torque. May trade away peak RPM.

| Section | Position cm | Chord cm | Twist deg | Airfoil |
|---|---:|---:|---:|---|
| 1 (Root) | 6 | 10.5 | 24 | NACA 4418 |
| 2 | 14 | 9.0 | 18 | SG6040 |
| 3 | 24 | 7.0 | 12 | S1223 |
| 4 | 34 | 5.0 | 7 | SG6043 |
| 5 | 43 | 3.4 | 3 | NACA 2412 |
| 6 (Tip) | 50 | 2.0 | 0 | E387 |

### Preset 3: High RPM / Low Drag Tip

For testing high-speed designs with lighter, lower-drag outer sections.

| Section | Position cm | Chord cm | Twist deg | Airfoil |
|---|---:|---:|---:|---|
| 1 (Root) | 6 | 8.0 | 18 | NACA 4415 |
| 2 | 14 | 6.8 | 13 | SG6042 |
| 3 | 24 | 5.0 | 8 | SG6043 |
| 4 | 34 | 3.6 | 4 | NACA 2412 |
| 5 | 43 | 2.5 | 1 | E387 |
| 6 (Tip) | 50 | 1.5 | 0 | E387 |

### Preset 4: Low Wind 3.6 m/s Classroom Tunnel

For the known classroom tunnel target around 3.6 m/s. Emphasizes mid-span lift.

| Section | Position cm | Chord cm | Twist deg | Airfoil |
|---|---:|---:|---:|---|
| 1 (Root) | 6 | 9.5 | 23 | NACA 4418 |
| 2 | 14 | 8.2 | 17 | SG6040 |
| 3 | 24 | 6.5 | 12 | S1223 |
| 4 | 34 | 4.8 | 7 | SG6043 |
| 5 | 43 | 3.2 | 3 | SG6043 |
| 6 (Tip) | 50 | 1.9 | 0 | NACA 2412 |

### Preset 5: Easy CAD / Easy Print

For students who need a less aggressive first Onshape model.

| Section | Position cm | Chord cm | Twist deg | Airfoil |
|---|---:|---:|---:|---|
| 1 (Root) | 6 | 8.5 | 18 | Clark Y |
| 2 | 14 | 7.2 | 14 | Clark Y |
| 3 | 24 | 5.8 | 9 | NACA 2412 |
| 4 | 34 | 4.4 | 5 | NACA 2412 |
| 5 | 43 | 3.0 | 2 | E387 |
| 6 (Tip) | 50 | 1.8 | 0 | E387 |

## Onshape package behavior

The app adds a button:

```text
Download Onshape package
```

The generated ZIP contains:

```text
blade_geometry.csv
airfoil_sections.csv
blade_planform.dxf
section_profiles.dxf
design_metadata.json
onshape_build_guide.md
```

The DXF files are 2D helper geometry, not a completed 3D part. The guide explains how to import the DXF/CSV into Onshape, create planes at station positions, sketch/import profiles, rotate by twist, and loft the blade.

## Architecture

Add focused modules under `windlab/`:

- `windlab/design_state.py` for serializing/deserializing `SimulationInput`;
- `windlab/design_store.py` for SQLite storage;
- `windlab/blade_presets.py` for the five starter designs;
- `windlab/onshape_export.py` for CSV/DXF/ZIP generation.

Add focused Streamlit components:

- `app/components/design_workspace.py` for save/load/undo/redo/reset/preset controls;
- integrate the workspace controls around `render_input_panel`.

The implementation should avoid broad refactoring of the simulator. Persistence/export features should consume `SimulationInput` and should not change aerodynamic calculations.

## UI design

Add a compact workspace section near the top of the Design Lab:

```text
Design workspace
[Undo] [Redo] [Reset]
Design name: __________ [Save design]
Load saved design: [dropdown] [Load]
Blade preset: [dropdown] [Load preset]
```

Keep export buttons in the current export section and add:

```text
Download Onshape package
```

If a user loads a preset, the app should update the section table and simulation inputs on the next rerun. The UI should explain that presets are starting points.

## Testing strategy

Tests should cover:

- design serialization round trip;
- SQLite store create/save/load/autosave behavior using a temporary database;
- preset count and diameter/radius constraints;
- preset section table validity;
- Onshape package ZIP contains all expected files;
- generated CSV contains section and airfoil data;
- generated DXF text contains basic valid DXF section markers;
- Streamlit app renders workspace controls and Onshape download button;
- existing simulator tests still pass.

## Success criteria

The phase is complete when:

- refreshing the app can restore the last autosaved design;
- students can explicitly save and load named designs locally;
- undo/redo controls exist and work for complete design snapshots;
- all five 1 m diameter / 3-blade presets are selectable;
- Onshape package ZIP is downloadable from the app;
- docs explain how to use the local workspace and Onshape package;
- tests, lint, and formatting pass.

## Risks and mitigations

The main risk is trying to make Streamlit behave like a full browser editor. Mitigation: use explicit app-level Undo/Redo rather than relying on browser `Command+Z`.

The second risk is overbuilding the database. Mitigation: use local SQLite only, no accounts and no networking.

The third risk is students mistaking Onshape package export for a finished print file. Mitigation: label it clearly as an Onshape design package, not STL, and include step-by-step guide text.

The fourth risk is preset overconfidence. Mitigation: label all presets as starting points and include test/calibration reminders.
