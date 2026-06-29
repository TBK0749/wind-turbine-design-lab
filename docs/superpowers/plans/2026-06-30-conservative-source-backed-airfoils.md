# Conservative Source-Backed Airfoils Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add conservative source-backed SG, S1223, E387, Clark Y, and NREL airfoil options that affect simulation results in a bounded, explainable way.

**Architecture:** Extend the existing section-airfoil catalog instead of replacing it. Keep the current compact educational polar generator, add conservative polar shapes for the new airfoils, and layer metadata/warnings around Reynolds range and blade-zone fit. Preserve the existing NACA workflow and validation guardrails.

**Tech Stack:** Python 3, Streamlit, Pydantic models, pytest, Ruff.

---

## File structure

- Modify: `windlab/section_airfoils.py`
  - Extend `SectionAirfoil` metadata.
  - Add canonical new airfoils and backward-compatible aliases.
  - Add blade-zone guidance helper.
- Modify: `windlab/airfoils.py`
  - Add compact polar shapes for SG6040, SG6042, SG6043, S1223, E387, Clark Y, NREL S822, and NREL S823.
  - Add polar-name aliasing for previous `Selig S1223` data.
  - Add conservative Reynolds-range warnings from the section-airfoil catalog.
- Modify: `app/components/airfoil_help.py`
  - Show confidence, Reynolds range, and source note in Airfoil Help.
- Modify: `app/components/result_cards.py`
  - Show representative-airfoil confidence/source context when the representative airfoil is catalog-backed.
- Modify: `app/components/learning_guide.py`
  - Explain non-NACA airfoil families, confidence, and why CL/CD is not fixed.
- Modify: `docs/physics_model.md`
  - Document conservative source-backed airfoil behavior and limitations.
- Modify: `docs/paper_model_notes.md`
  - Add a short note that the new airfoils are source-informed but not measured field calibration.
- Test: `tests/test_airfoil_catalog.py`
  - New focused tests for metadata, selectable names, polar availability, Reynolds warnings, and zone guidance.
- Modify: `tests/test_airfoils.py`
  - Add polar interpolation tests for SG/NREL/E387 choices.
- Modify: `tests/test_section_airfoils.py`
  - Add selection/order/backward-alias coverage.
- Modify: `tests/test_app.py`
  - Add visible UI coverage for confidence/Reynolds/source columns.

## External source notes to encode in metadata

Use short source notes only; do not claim raw measured polar import in this phase.

- SG6040 / SG6042 / SG6043: Giguere & Selig small horizontal-axis wind-turbine airfoil family; useful at low Reynolds numbers and small turbines.
- S1223: Selig high-lift low-Reynolds airfoil; useful for strong lift but sensitive to stall and drag.
- E387: Eppler low-Reynolds reference airfoil with experimental low-speed literature; useful for comparison.
- Clark Y: traditional flat-bottom cambered airfoil; easy to build and align in classrooms.
- NREL S822 / S823: NREL thick wind-turbine airfoils for larger 3-10 m stall-regulated rotors; include with warnings for very small classroom Reynolds numbers.

### Task 1: Add failing catalog and behavior tests

**Files:**
- Create: `tests/test_airfoil_catalog.py`
- Modify: `tests/test_airfoils.py`
- Modify: `tests/test_section_airfoils.py`
- Modify: `tests/test_app.py`

- [ ] **Step 1: Create focused catalog tests**

Create `tests/test_airfoil_catalog.py` with:

```python
import pytest

from windlab.airfoils import estimate_airfoil_performance, lookup_airfoil_polar
from windlab.section_airfoils import (
    get_section_airfoil,
    section_airfoil_options,
    station_airfoil_warnings,
)


REQUESTED_SOURCE_BACKED_AIRFOILS = (
    "SG6040",
    "SG6042",
    "SG6043",
    "S1223",
    "E387",
    "Clark Y",
    "NREL S822",
    "NREL S823",
)


@pytest.mark.parametrize("airfoil_name", REQUESTED_SOURCE_BACKED_AIRFOILS)
def test_source_backed_airfoils_are_selectable_with_metadata(airfoil_name: str) -> None:
    airfoil = get_section_airfoil(airfoil_name)

    assert airfoil.name == airfoil_name
    assert airfoil.family in {
        "Cambered plate",
        "Symmetric airfoil",
        "High-lift airfoil",
    }
    assert airfoil.best_zone
    assert airfoil.plain_language_summary
    assert airfoil.thickness_percent is not None
    assert airfoil.thickness_percent > 0.0
    assert airfoil.camber_description
    assert airfoil.recommended_reynolds_min > 0.0
    assert airfoil.recommended_reynolds_max > airfoil.recommended_reynolds_min
    assert airfoil.confidence in {"High", "Medium", "Estimated"}
    assert airfoil.source_note


def test_source_backed_airfoils_are_in_student_selector_order() -> None:
    options = section_airfoil_options()

    for airfoil_name in REQUESTED_SOURCE_BACKED_AIRFOILS:
        assert airfoil_name in options


def test_legacy_selig_s1223_name_still_resolves_to_canonical_s1223() -> None:
    airfoil = get_section_airfoil("Selig S1223")

    assert airfoil.name == "S1223"


@pytest.mark.parametrize("airfoil_name", REQUESTED_SOURCE_BACKED_AIRFOILS)
def test_source_backed_airfoils_have_polar_lookup(airfoil_name: str) -> None:
    polar = lookup_airfoil_polar(
        airfoil_name,
        angle_of_attack_deg=6.0,
        reynolds_number=150_000.0,
    )

    assert polar.airfoil_name == airfoil_name
    assert polar.lift_coefficient > 0.0
    assert polar.drag_coefficient > 0.0


def test_out_of_range_reynolds_warns_for_large_nrel_airfoil() -> None:
    result = estimate_airfoil_performance(
        "High-lift airfoil",
        airfoil_name="NREL S822",
        angle_of_attack_deg=6.0,
        reynolds_number=25_000.0,
    )

    assert any("recommended Reynolds range" in warning for warning in result.warnings)
    assert any("small classroom rotor" in warning for warning in result.warnings)


def test_tip_zone_guidance_warns_for_very_high_lift_airfoil_at_tip() -> None:
    warnings = station_airfoil_warnings("S1223", station_fraction=0.95)

    assert any("tip" in warning.lower() for warning in warnings)
    assert any("drag" in warning.lower() or "stall" in warning.lower() for warning in warnings)


def test_thin_low_re_root_guidance_warns_for_tip_airfoil_at_root() -> None:
    warnings = station_airfoil_warnings("E387", station_fraction=0.08)

    assert any("root" in warning.lower() for warning in warnings)
```

- [ ] **Step 2: Add airfoil behavior tests**

Append to `tests/test_airfoils.py`:

```python
def test_sg6043_is_bounded_but_better_than_flat_plate_at_low_re() -> None:
    sg6043 = estimate_airfoil_performance(
        "High-lift airfoil",
        airfoil_name="SG6043",
        angle_of_attack_deg=6.0,
        reynolds_number=150_000.0,
    )
    flat = estimate_airfoil_performance(
        "Flat plate / Foam board",
        airfoil_name="Flat plate",
        angle_of_attack_deg=6.0,
        reynolds_number=150_000.0,
    )

    assert sg6043.lift_drag_ratio > flat.lift_drag_ratio
    assert sg6043.efficiency_factor <= 1.12
    assert sg6043.drag_coefficient > 0.0


def test_nrel_airfoil_warning_does_not_create_unbounded_efficiency() -> None:
    nrel = estimate_airfoil_performance(
        "High-lift airfoil",
        airfoil_name="NREL S823",
        angle_of_attack_deg=6.0,
        reynolds_number=25_000.0,
    )

    assert nrel.efficiency_factor <= 1.12
    assert any("recommended Reynolds range" in warning for warning in nrel.warnings)
```

- [ ] **Step 3: Add section alias/order test**

Append to `tests/test_section_airfoils.py`:

```python
def test_source_backed_airfoil_names_are_student_facing() -> None:
    options = section_airfoil_options()

    assert "SG6040" in options
    assert "SG6042" in options
    assert "SG6043" in options
    assert "S1223" in options
    assert "Selig S1223" not in options
    assert "NREL S822" in options
    assert "NREL S823" in options
```

- [ ] **Step 4: Add app visibility test**

Append to `tests/test_app.py`:

```python
def test_airfoil_help_shows_source_backed_metadata() -> None:
    app_path = Path(__file__).parents[1] / "app" / "main.py"
    app = AppTest.from_file(str(app_path), default_timeout=15).run()

    assert not app.exception
    assert any("Confidence" in text.value for text in app.markdown)
    assert any("Reynolds range" in text.value for text in app.markdown)
    assert any("SG6043" in dataframe.value.to_string() for dataframe in app.dataframe)
```

- [ ] **Step 5: Run the new tests and confirm they fail for missing feature**

Run:

```bash
.venv/bin/pytest tests/test_airfoil_catalog.py tests/test_airfoils.py::test_sg6043_is_bounded_but_better_than_flat_plate_at_low_re tests/test_section_airfoils.py::test_source_backed_airfoil_names_are_student_facing -q
```

Expected: FAIL because `station_airfoil_warnings`, new metadata fields, and new polar names do not exist yet.

### Task 2: Extend the section-airfoil catalog

**Files:**
- Modify: `windlab/section_airfoils.py`
- Test: `tests/test_airfoil_catalog.py`
- Test: `tests/test_section_airfoils.py`

- [ ] **Step 1: Extend the dataclass**

Modify `SectionAirfoil` in `windlab/section_airfoils.py` to:

```python
@dataclass(frozen=True, slots=True)
class SectionAirfoil:
    """Metadata for an airfoil that can be assigned to one blade station."""

    name: str
    family: str
    role: str
    best_zone: str
    plain_language_summary: str
    thickness_percent: float | None = None
    camber_percent: float | None = None
    camber_position_percent: float | None = None
    camber_description: str = "Representative educational shape."
    recommended_reynolds_min: float = 30_000.0
    recommended_reynolds_max: float = 500_000.0
    confidence: str = "Estimated"
    source_note: str = "Educational approximation; not a measured field calibration."
    zone_warnings: tuple[str, ...] = ()
```

- [ ] **Step 2: Add canonical source-backed entries**

Add these entries to `SECTION_AIRFOILS` after the NACA entries and before `Flat plate`.
For `Clark Y`, replace the current partial `Clark Y` entry. For `S1223`, replace
the current partial `Selig S1223` entry with canonical `S1223` and keep
`Selig S1223` only as an alias.

```python
    "SG6040": SectionAirfoil(
        name="SG6040",
        family="High-lift airfoil",
        role="Small-wind root option: thicker SG-series section for startup torque and root strength.",
        best_zone="Root / Mid",
        plain_language_summary=(
            "Selig/Giguere small-wind airfoil; useful near the root where torque and stiffness matter."
        ),
        thickness_percent=16.0,
        camber_description="Cambered SG-series small-wind profile.",
        recommended_reynolds_min=80_000.0,
        recommended_reynolds_max=500_000.0,
        confidence="Medium",
        source_note="Giguere & Selig small horizontal-axis wind-turbine airfoil family.",
        zone_warnings=(
            "Near the tip, SG6040 may add unnecessary thickness and drag compared with thinner options.",
        ),
    ),
    "SG6042": SectionAirfoil(
        name="SG6042",
        family="High-lift airfoil",
        role="Small-wind transition option: balances low-Re lift with moderate drag.",
        best_zone="Root / Mid",
        plain_language_summary=(
            "SG-series small-wind transition airfoil; good bridge from strong root to lift-producing mid blade."
        ),
        thickness_percent=10.0,
        camber_description="Cambered low-Re small-wind profile.",
        recommended_reynolds_min=80_000.0,
        recommended_reynolds_max=500_000.0,
        confidence="Medium",
        source_note="Giguere & Selig small horizontal-axis wind-turbine airfoil family.",
    ),
    "SG6043": SectionAirfoil(
        name="SG6043",
        family="High-lift airfoil",
        role="Small-wind primary lift option: high lift/drag candidate for low-Re mid blade sections.",
        best_zone="Mid",
        plain_language_summary=(
            "SG-series small-wind airfoil; useful in the main lift region when Reynolds number is in range."
        ),
        thickness_percent=10.0,
        camber_percent=5.1,
        camber_position_percent=53.3,
        camber_description="Cambered low-Re high-lift profile.",
        recommended_reynolds_min=80_000.0,
        recommended_reynolds_max=500_000.0,
        confidence="Medium",
        source_note="Giguere & Selig small horizontal-axis wind-turbine airfoil family; UIUC coordinates list SG6043 geometry.",
        zone_warnings=(
            "At the blade tip, SG6043 can be useful but may be more stall-sensitive than thinner tip choices.",
        ),
    ),
    "S1223": SectionAirfoil(
        name="S1223",
        family="High-lift airfoil",
        role="Very high-lift low-speed option; useful for experiments but sensitive to stall and drag.",
        best_zone="Mid",
        plain_language_summary=(
            "High-lift low-Re airfoil; strong lift for startup experiments, but not automatically best for high RPM."
        ),
        thickness_percent=12.1,
        camber_description="Very cambered high-lift low-Re profile.",
        recommended_reynolds_min=80_000.0,
        recommended_reynolds_max=500_000.0,
        confidence="Medium",
        source_note="Selig high-lift low-Reynolds airfoil literature and UIUC coordinate database.",
        zone_warnings=(
            "Near the tip, S1223 can create extra drag or stall if pitch/twist is too high.",
        ),
    ),
    "E387": SectionAirfoil(
        name="E387",
        family="Cambered plate",
        role="Low-Re reference option: efficient comparison airfoil when surface finish is reasonably smooth.",
        best_zone="Mid / Tip",
        plain_language_summary=(
            "Eppler low-Re reference airfoil; useful for comparing smoother low-drag designs."
        ),
        thickness_percent=9.1,
        camber_description="Moderately cambered low-Re profile.",
        recommended_reynolds_min=60_000.0,
        recommended_reynolds_max=460_000.0,
        confidence="Medium",
        source_note="NASA low-Reynolds experimental literature reports E387 tests from about Re 60,000 to 460,000.",
        zone_warnings=(
            "At the root, E387 may be too thin for a stiff 3D-printed blade without reinforcement.",
        ),
    ),
    "Clark Y": SectionAirfoil(
        name="Clark Y",
        family="Cambered plate",
        role="Flat-bottom cambered section, easy to fabricate and align.",
        best_zone="Mid",
        plain_language_summary="Flat-bottom cambered airfoil; easy to build and align by hand.",
        thickness_percent=11.7,
        camber_description="Traditional flat-bottom cambered profile.",
        recommended_reynolds_min=80_000.0,
        recommended_reynolds_max=500_000.0,
        confidence="Estimated",
        source_note="Traditional classroom-friendly reference shape; modeled conservatively here.",
    ),
    "NREL S822": SectionAirfoil(
        name="NREL S822",
        family="High-lift airfoil",
        role="Thick wind-turbine reference section; useful for comparison but designed for larger rotors.",
        best_zone="Root / Mid",
        plain_language_summary=(
            "NREL thick wind-turbine airfoil for larger stall-regulated rotors; use cautiously on small classroom blades."
        ),
        thickness_percent=16.0,
        camber_description="Thick wind-turbine profile with roughness-insensitive design goals.",
        recommended_reynolds_min=200_000.0,
        recommended_reynolds_max=1_000_000.0,
        confidence="Medium",
        source_note="NREL S822/S823 report for 3-10 m stall-regulated horizontal-axis wind turbines.",
        zone_warnings=(
            "For a small classroom rotor, NREL S822 may operate below its intended Reynolds range.",
        ),
    ),
    "NREL S823": SectionAirfoil(
        name="NREL S823",
        family="High-lift airfoil",
        role="Thick wind-turbine reference section; strong comparison option for larger low-speed rotors.",
        best_zone="Root / Mid",
        plain_language_summary=(
            "NREL thick wind-turbine airfoil; educational comparison option, not a guaranteed best small-rotor choice."
        ),
        thickness_percent=21.0,
        camber_description="Very thick wind-turbine profile with roughness-insensitive design goals.",
        recommended_reynolds_min=200_000.0,
        recommended_reynolds_max=1_000_000.0,
        confidence="Medium",
        source_note="NREL S822/S823 report for 3-10 m stall-regulated horizontal-axis wind turbines.",
        zone_warnings=(
            "NREL S823 is very thick and can add drag or weight near the tip of a small classroom rotor.",
            "For a small classroom rotor, NREL S823 may operate below its intended Reynolds range.",
        ),
    ),
```

Keep the existing `Clark Y` and `Selig S1223` entries only long enough to migrate them; the canonical selector should show `Clark Y` and `S1223`, not `Selig S1223`.

- [ ] **Step 3: Add aliases and zone guidance helper**

Add below `SECTION_AIRFOILS`:

```python
SECTION_AIRFOIL_ALIASES: dict[str, str] = {
    "Selig S1223": "S1223",
}


def _canonical_airfoil_name(name: str) -> str:
    """Return the canonical catalog key for student or legacy airfoil names."""

    return SECTION_AIRFOIL_ALIASES.get(name, name)
```

Update `get_section_airfoil` to:

```python
def get_section_airfoil(name: str) -> SectionAirfoil:
    """Return a section airfoil or raise a friendly error."""

    canonical_name = _canonical_airfoil_name(name)
    try:
        return SECTION_AIRFOILS[canonical_name]
    except KeyError as exc:
        choices = ", ".join(SECTION_AIRFOILS)
        raise ValueError(f"Section airfoil must be one of: {choices}.") from exc
```

Add:

```python
def station_airfoil_warnings(name: str, *, station_fraction: float) -> tuple[str, ...]:
    """Return non-blocking guidance for using an airfoil at a blade span station."""

    airfoil = get_section_airfoil(name)
    fraction = max(0.0, min(1.0, station_fraction))
    warnings = list(airfoil.zone_warnings)

    if fraction < 0.20 and airfoil.thickness_percent is not None and airfoil.thickness_percent < 10.0:
        warnings.append(
            f"{airfoil.name} is thin for a root section; consider reinforcement or a thicker root airfoil."
        )
    if fraction > 0.80 and airfoil.thickness_percent is not None and airfoil.thickness_percent > 15.0:
        warnings.append(
            f"{airfoil.name} is thick for a fast tip section; compare with thinner low-drag tip airfoils."
        )
    if fraction > 0.80 and airfoil.name == "S1223":
        warnings.append(
            "S1223 near the tip can produce useful lift, but drag and stall risk may limit RPM."
        )

    return tuple(dict.fromkeys(warnings))
```

- [ ] **Step 4: Run catalog tests**

Run:

```bash
.venv/bin/pytest tests/test_airfoil_catalog.py::test_source_backed_airfoils_are_selectable_with_metadata tests/test_airfoil_catalog.py::test_legacy_selig_s1223_name_still_resolves_to_canonical_s1223 tests/test_section_airfoils.py::test_source_backed_airfoil_names_are_student_facing -q
```

Expected: PASS for catalog metadata tests; polar-related tests may still fail until Task 3.

- [ ] **Step 5: Commit catalog change**

Run:

```bash
git add windlab/section_airfoils.py tests/test_airfoil_catalog.py tests/test_section_airfoils.py
git commit -m "feat: add source-backed airfoil catalog metadata"
```

### Task 3: Add conservative polar shapes and Reynolds warnings

**Files:**
- Modify: `windlab/airfoils.py`
- Test: `tests/test_airfoil_catalog.py`
- Test: `tests/test_airfoils.py`

- [ ] **Step 1: Rename S1223 polar and add aliases**

In `_POLAR_SHAPES`, replace the `"Selig S1223"` key with `"S1223"`.

Add after `_AIRFOIL_POLAR_ALIASES`:

```python
_SECTION_POLAR_ALIASES: dict[str, str] = {
    "Selig S1223": "S1223",
}
```

Update `_resolve_polar_name`:

```python
def _resolve_polar_name(airfoil_type: str, airfoil_name: str | None) -> str:
    """Resolve a family or section airfoil to the internal polar table name."""

    if airfoil_name is not None:
        polar_name = _SECTION_POLAR_ALIASES.get(airfoil_name, airfoil_name)
        if polar_name not in AIRFOIL_POLAR_TABLES:
            choices = ", ".join(AIRFOIL_POLAR_TABLES)
            raise ValueError(f"Airfoil polar must be one of: {choices}.")
        return polar_name
    return _AIRFOIL_POLAR_ALIASES[airfoil_type]
```

- [ ] **Step 2: Add conservative polar shapes**

Add these `_POLAR_SHAPES` entries:

```python
    "SG6040": _PolarShape(-3.6, 5.25, 1.30, 0.023, 0.038, 14.0, 1.10, 0.68, 0.94),
    "SG6042": _PolarShape(-3.4, 5.35, 1.36, 0.020, 0.035, 14.5, 1.02, 0.60, 0.88),
    "SG6043": _PolarShape(-3.8, 5.40, 1.42, 0.019, 0.034, 15.0, 0.98, 0.56, 0.86),
    "S1223": _PolarShape(-5.0, 5.45, 1.55, 0.026, 0.045, 13.5, 1.12, 0.52, 0.88),
    "E387": _PolarShape(-2.1, 5.20, 1.18, 0.017, 0.032, 12.5, 0.96, 0.85, 0.88),
    "NREL S822": _PolarShape(-2.6, 5.15, 1.22, 0.023, 0.037, 13.0, 1.15, 0.86, 0.95),
    "NREL S823": _PolarShape(-2.8, 5.20, 1.25, 0.025, 0.039, 13.0, 1.20, 0.88, 0.98),
```

Keep `Clark Y` present with conservative parameters. If adjusting it, use:

```python
    "Clark Y": _PolarShape(-2.2, 5.15, 1.15, 0.020, 0.036, 14.0, 1.02, 0.78, 0.80),
```

- [ ] **Step 3: Add catalog-based Reynolds warnings**

Add helper in `windlab/airfoils.py`:

```python
def _catalog_reynolds_warnings(
    airfoil_name: str,
    reynolds_number: float,
) -> tuple[str, ...]:
    """Return warnings when a section airfoil is outside its recommended range."""

    try:
        from windlab.section_airfoils import get_section_airfoil

        airfoil = get_section_airfoil(airfoil_name)
    except ValueError:
        return ()

    warnings: list[str] = []
    if reynolds_number < airfoil.recommended_reynolds_min:
        warnings.append(
            f"{airfoil.name} is below its recommended Reynolds range "
            f"({airfoil.recommended_reynolds_min:,.0f}-{airfoil.recommended_reynolds_max:,.0f}); "
            "treat CL/CD as lower-confidence."
        )
    elif reynolds_number > airfoil.recommended_reynolds_max:
        warnings.append(
            f"{airfoil.name} is above its recommended Reynolds range "
            f"({airfoil.recommended_reynolds_min:,.0f}-{airfoil.recommended_reynolds_max:,.0f}); "
            "treat CL/CD as lower-confidence."
        )

    if airfoil.name.startswith("NREL S") and reynolds_number < 100_000.0:
        warnings.append(
            f"{airfoil.name} was designed for larger wind-turbine rotors; "
            "on a small classroom rotor, use it as a comparison, not a guaranteed best choice."
        )

    return tuple(warnings)
```

In `estimate_airfoil_performance`, after `_reynolds_adjustment(...)`, add:

```python
    warnings.extend(_catalog_reynolds_warnings(polar_name, reynolds_number))
```

- [ ] **Step 4: Run polar tests**

Run:

```bash
.venv/bin/pytest tests/test_airfoil_catalog.py tests/test_airfoils.py -q
```

Expected: PASS. If `test_sg6043_is_bounded_but_better_than_flat_plate_at_low_re` fails because the difference is too small, adjust only SG6043's conservative polar shape within the existing efficiency cap; do not raise `AirfoilPerformance.efficiency_factor` above the current 1.12 clamp.

- [ ] **Step 5: Commit polar change**

Run:

```bash
git add windlab/airfoils.py tests/test_airfoils.py tests/test_airfoil_catalog.py
git commit -m "feat: add conservative source-backed airfoil polars"
```

### Task 4: Surface confidence and source context in the UI

**Files:**
- Modify: `app/components/airfoil_help.py`
- Modify: `app/components/result_cards.py`
- Test: `tests/test_app.py`

- [ ] **Step 1: Extend Airfoil Help table**

In `app/components/airfoil_help.py`, update the explanatory markdown to include:

```markdown
**Confidence is not accuracy certification.** It tells you how much source context
the simulator has for the airfoil. Final mW accuracy still needs real rotor tests.
```

Add helper:

```python
def _reynolds_range(value_min: float, value_max: float) -> str:
    """Return a compact Reynolds range label."""

    return f"{value_min:,.0f}-{value_max:,.0f}"
```

Add columns to each row:

```python
                    "Reynolds range": _reynolds_range(
                        airfoil.recommended_reynolds_min,
                        airfoil.recommended_reynolds_max,
                    ),
                    "Confidence": airfoil.confidence,
                    "Source note": airfoil.source_note,
```

- [ ] **Step 2: Add representative-airfoil source context to result cards**

In `app/components/result_cards.py`, import:

```python
from windlab.section_airfoils import get_section_airfoil
```

Add helper:

```python
def _airfoil_context(name: str) -> str | None:
    """Return compact metadata for a catalog-backed airfoil."""

    try:
        airfoil = get_section_airfoil(name)
    except ValueError:
        return None
    return (
        f"{airfoil.confidence} confidence · "
        f"Re {airfoil.recommended_reynolds_min:,.0f}-{airfoil.recommended_reynolds_max:,.0f}"
    )
```

At the end of `render_airfoil_cards`, add:

```python
    context = _airfoil_context(result.representative_airfoil_name)
    if context:
        st.caption(f"Representative airfoil context: {context}")
```

- [ ] **Step 3: Run app test**

Run:

```bash
.venv/bin/pytest tests/test_app.py::test_airfoil_help_shows_source_backed_metadata -q
```

Expected: PASS.

- [ ] **Step 4: Commit UI change**

Run:

```bash
git add app/components/airfoil_help.py app/components/result_cards.py tests/test_app.py
git commit -m "feat: show airfoil confidence context"
```

### Task 5: Update student-facing documentation

**Files:**
- Modify: `app/components/learning_guide.py`
- Modify: `docs/physics_model.md`
- Modify: `docs/paper_model_notes.md`
- Test: `tests/test_project_docs.py`

- [ ] **Step 1: Update glossary terms**

In `app/components/learning_guide.py`, add terms after the existing `NACA 2412` entry:

```python
        (
            "SG6040 / SG6042 / SG6043",
            "Small-wind airfoils from the Selig/Giguere SG series. They are useful "
            "comparison choices for low-Reynolds classroom rotors, especially around "
            "the root and middle lift region.",
        ),
        (
            "S1223",
            "A very high-lift low-Reynolds airfoil. It can help startup experiments, "
            "but high lift also means stall and drag must be watched carefully.",
        ),
        (
            "E387",
            "A classic low-Reynolds reference airfoil. It is useful for comparing smoother, "
            "lower-drag sections but may need better fabrication quality than a flat plate.",
        ),
        (
            "NREL S822 / S823",
            "Thick wind-turbine airfoils designed for larger rotors. In this app they are "
            "educational comparison options and may be outside the best Reynolds range for "
            "small 3D-printed classroom blades.",
        ),
        (
            "Airfoil confidence",
            "A label showing how much source context the simulator has. It is not a promise "
            "that the predicted mW will match a real tunnel test.",
        ),
```

- [ ] **Step 2: Update physics documentation**

Append this subsection to `docs/physics_model.md` under the airfoil model discussion:

```markdown
### Conservative source-backed airfoils

The section-table selector includes additional non-NACA choices such as SG6040,
SG6042, SG6043, S1223, E387, Clark Y, NREL S822, and NREL S823. These entries
carry source notes, representative thickness, recommended Reynolds ranges, and
confidence labels. They use bounded compact polar shapes rather than raw imported
wind-tunnel polar files, so they should be used to compare trends, not certify
exact measured power.

If a selected airfoil operates outside its recommended Reynolds range, the
simulator reports a warning and treats the result as lower confidence. This is
especially important for NREL S822/S823, which are wind-turbine airfoils designed
for larger rotors than the classroom competition model.
```

- [ ] **Step 3: Update paper model notes**

Append this note to `docs/paper_model_notes.md`:

```markdown
### Source-backed airfoil expansion

The app includes conservative SG-series, S1223, E387, Clark Y, and NREL S822/S823
airfoil options. These entries are source-informed and bounded by the existing
educational model; they are not raw measured polar imports. Use them to reduce
bad design choices before fabrication, then calibrate with real 3D-print and
wind-tunnel measurements.
```

- [ ] **Step 4: Add documentation test**

Append to `tests/test_project_docs.py`:

```python
def test_physics_docs_describe_source_backed_airfoil_limits() -> None:
    physics_doc = Path("docs/physics_model.md").read_text()
    paper_notes = Path("docs/paper_model_notes.md").read_text()

    assert "Conservative source-backed airfoils" in physics_doc
    assert "SG6043" in physics_doc
    assert "not certify exact measured power" in physics_doc
    assert "Source-backed airfoil expansion" in paper_notes
    assert "not raw measured polar imports" in paper_notes
```

- [ ] **Step 5: Run documentation tests**

Run:

```bash
.venv/bin/pytest tests/test_project_docs.py tests/test_app.py::test_streamlit_app_renders_english_guide_and_glossary -q
```

Expected: PASS.

- [ ] **Step 6: Commit docs change**

Run:

```bash
git add app/components/learning_guide.py docs/physics_model.md docs/paper_model_notes.md tests/test_project_docs.py
git commit -m "docs: explain source-backed airfoil limits"
```

### Task 6: Full regression and final guardrail check

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run all tests**

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

Expected: all files already formatted.

- [ ] **Step 4: Regenerate validation report if benchmark outputs change**

Run:

```bash
.venv/bin/python scripts/generate_validation_report.py
```

Expected: `docs/model_validation_report.md` stays consistent with benchmark ranges. If the report changes only because wording or deterministic benchmark values changed within accepted ranges, commit the updated report. If any benchmark fails accepted ranges, tune conservative polar shapes downward/upward only within the existing bounded model and re-run tests.

- [ ] **Step 5: Inspect git diff**

Run:

```bash
git status --short
git diff --stat
```

Expected: only intended files changed.

- [ ] **Step 6: Final commit if validation report changed**

If Task 6 Step 4 changed `docs/model_validation_report.md`, run:

```bash
git add docs/model_validation_report.md
git commit -m "docs: refresh validation report for airfoil catalog"
```

If no validation report change occurred, skip this commit.

## Plan self-review checklist

- Spec coverage: source-backed catalog, conservative polar behavior, warnings, UI context, docs, and tests are covered.
- Scope check: no raw polar import, full QBlade, field calibration, or broad simulator rewrite is included.
- Type consistency: new metadata fields are defined on `SectionAirfoil`; tests and UI read the same field names.
- Guardrail check: efficiency remains capped by existing `AirfoilPerformance` clamp and validation benchmarks are re-run.
