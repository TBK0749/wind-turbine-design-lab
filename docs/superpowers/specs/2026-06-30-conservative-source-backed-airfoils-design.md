# Conservative Source-Backed Airfoils Design

## Goal

Add non-NACA and wind-turbine-oriented airfoil choices to the Wind Turbine Design Lab without making the simulator overconfident or numerically unstable. The feature must help teachers and students compare airfoil choices before 3D printing while clearly communicating that final calibration still requires measured wind-tunnel or competition data.

## Context

The project already supports section-level airfoil choices, simplified polar lookup/interpolation, BEMT-lite calculations, airfoil previews, validation reports, and measured benchmark import/export. Current polar values are generated from compact educational parameters inside `windlab/airfoils.py`; they are useful for directionally reasonable classroom estimates, but they are not yet raw external polar tables from UIUC, NREL, QBlade, XFOIL, or wind-tunnel measurements.

The next feature should therefore be conservative: add better airfoil metadata, controlled polar shapes, warnings, and tests, but avoid claiming field validation before real 3D-print / wind-tunnel measurements exist.

## Airfoils in scope

The first source-backed library expansion will include:

- SG6040
- SG6042
- SG6043
- S1223
- E387
- Clark Y
- NREL S822
- NREL S823

Existing NACA and flat-plate options remain available. `Clark Y` and `S1223` already exist in a partial form; this work upgrades them into the same conservative metadata model as the new choices.

## Non-goals

This phase will not:

- implement full QBlade;
- implement full iterative engineering-grade BEMT with measured polar files;
- guarantee real-world mW accuracy before measured classroom data exists;
- import raw third-party polar tables automatically;
- tune the model to a specific 3D print or wind tunnel;
- remove the existing educational NACA workflow.

## Recommended approach

Use a conservative, source-backed airfoil database layered on top of the current model.

Each airfoil will have:

- display name;
- family used by existing model code;
- thickness percentage when known or representative;
- camber description when useful for students;
- recommended blade zone: root, root/mid, mid, mid/tip, tip, or prototype;
- practical Reynolds number range for classroom interpretation;
- confidence level: high, medium, or estimated;
- source note describing why the airfoil is included;
- plain-English student explanation;
- misuse warnings for poor root/mid/tip placement or out-of-range Reynolds operation.

Polar behavior remains bounded. Where the project has no raw measured polar table, the new airfoil will use compact polar-shape parameters rather than pretending to have exact measured CL/CD curves. The UI and result warnings must expose this uncertainty.

## Data model

Introduce a focused airfoil catalog concept that can serve both the simulator and the UI. It should not be a large refactor. The likely shape is a dataclass with fields similar to:

```python
@dataclass(frozen=True, slots=True)
class AirfoilCatalogEntry:
    name: str
    family: str
    role: str
    best_zone: str
    plain_language_summary: str
    thickness_percent: float | None
    camber_description: str
    recommended_reynolds_min: float
    recommended_reynolds_max: float
    confidence: str
    source_note: str
    zone_warnings: tuple[str, ...]
```

The catalog can initially live beside `windlab/section_airfoils.py` or inside it if that keeps the change small. If the implementation becomes crowded, split catalog metadata into a new `windlab/airfoil_catalog.py` while keeping `section_airfoils.py` as the student-facing selection API.

## Simulator behavior

Changing a section airfoil must continue to affect:

- lift coefficient;
- drag coefficient;
- lift/drag ratio;
- efficiency factor;
- stall risk;
- Cp;
- RPM;
- mechanical power;
- electrical mW.

However, the new profiles must not push results outside practical bounds. The current practical Cp cap, BEMT-lite damping, generator power cap, and validation benchmark checks remain guardrails.

For out-of-range use, the simulator should add warnings such as:

- selected airfoil is outside its recommended Reynolds range;
- selected airfoil is unusually thin for a root section;
- selected airfoil is draggy or high-lift and may stall near the tip;
- NREL utility-scale airfoil may not match very small classroom Reynolds numbers.

These warnings should inform students without blocking experimentation.

## UI behavior

The Blade Geometry Table remains the main place to choose section airfoils. New airfoils should appear in the existing Airfoil selector column.

The UI should show enough context to prevent blind selection:

- role / purpose remains visible in the table;
- Airfoil Help or Guide explains why different families exist;
- result cards or captions show representative airfoil, CL, CD, CL/CD, stall risk, Reynolds number, and confidence;
- warnings are displayed when students choose an airfoil outside its intended range or blade zone.

The feature should not make the sidebar more confusing. In section-table mode, the global simple airfoil selector should stay hidden or clearly marked as overridden.

## Documentation behavior

Update student-facing English documentation to explain:

- Airfoil is the blade cross-section shape;
- CL, CD, and CL/CD are not fixed constants;
- CL/CD depends on Reynolds number and angle of attack;
- thickness affects strength and drag;
- root/mid/tip sections have different jobs;
- model values are estimates and must be calibrated with real tests before claiming field accuracy.

Documentation must avoid saying the project is fully validated by these new airfoils.

## Testing strategy

Add or update tests so the feature cannot silently degrade model reliability:

- all new airfoils are selectable in section-table mode;
- catalog metadata is complete for every airfoil;
- polar lookup supports each new airfoil name;
- out-of-range Reynolds use produces a warning;
- root/mid/tip misuse produces a warning or guidance message;
- switching between at least two airfoils changes CL/CD and electrical mW in a plausible direction;
- existing validation benchmarks remain within their accepted ranges;
- existing installation, guide, and app tests still pass.

The implementation should run:

```bash
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

## Success criteria

The phase is successful when:

- the requested SG, S1223, E387, Clark Y, and NREL options appear in the Blade Geometry Table;
- each option has student-readable metadata and confidence/source notes;
- changing an airfoil changes the simulation in a bounded, explainable way;
- warnings appear for risky or out-of-range use;
- paper validation benchmarks do not regress;
- docs explain that real wind-tunnel calibration is still required.

## Risks and mitigations

The main risk is false precision. Students may treat new CL/CD values as exact measured truth. Mitigation: show confidence and warning text wherever the new airfoils affect results.

The second risk is benchmark drift. New polar shapes could accidentally improve one scenario while breaking paper validation. Mitigation: keep practical Cp guardrails, add benchmark regression tests, and do not tune to unrealistic mW gains.

The third risk is UI overload. Too many airfoils can confuse beginners. Mitigation: keep role text short, group explanations in Guide/Glossary, and preserve the default competition preset.

## Implementation boundary

This design authorizes planning for the conservative airfoil expansion. It does not authorize broad simulator rewrites, raw external polar import, or calibration against real classroom measurements. Those remain future phases after this controlled library expansion is reviewed and tested.
