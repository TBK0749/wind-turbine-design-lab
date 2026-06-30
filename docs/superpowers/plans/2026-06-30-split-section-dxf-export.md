# Split Section DXF Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Onshape package easier for beginners by exporting one DXF file per blade section in addition to the combined profile overview.

**Architecture:** Keep the existing combined `section_profiles.dxf` for overview/debugging. Add focused helpers in `windlab/onshape_export.py` that generate a sanitized filename and a single scaled, centered, pre-twisted airfoil DXF for each blade station. Update the ZIP package, in-package build guide, project manual, and PDF manual to teach the new easier workflow.

**Tech Stack:** Python standard library, existing DXF string writer, ReportLab PDF generator, pytest, ruff.

---

### Task 1: Individual section DXF exports

**Files:**
- Modify: `tests/test_onshape_export.py`
- Modify: `windlab/onshape_export.py`

- [x] **Step 1: Write failing tests**

Add tests that expect `section_profile_filename`, `section_profile_dxf`, and ZIP files under `section_profiles/`.

- [x] **Step 2: Run tests to verify failure**

Run: `.venv/bin/pytest tests/test_onshape_export.py -q`

Expected: FAIL because the new helpers and ZIP entries do not exist yet.

- [x] **Step 3: Implement minimal exporter changes**

Add filename sanitization, one-section DXF generation, `individual_section_profile_dxfs`, and write each file into the ZIP under `section_profiles/`.

- [x] **Step 4: Run tests to verify pass**

Run: `.venv/bin/pytest tests/test_onshape_export.py -q`

Expected: PASS.

### Task 2: Manual and PDF update

**Files:**
- Modify: `docs/onshape_workflow_manual.md`
- Modify: `scripts/generate_onshape_manual_pdf.py` only if formatting support is needed
- Modify: `output/pdf/Wind_Turbine_Design_Lab_Onshape_Workflow_Manual.pdf`
- Modify: `tests/test_project_docs.py`

- [x] **Step 1: Add failing docs assertions**

Assert the manual mentions `section_profiles/section_01_root_NACA4418.dxf` and the easier no-delete workflow.

- [x] **Step 2: Run docs test to verify failure**

Run: `.venv/bin/pytest tests/test_project_docs.py::test_onshape_manual_explains_split_section_profiles -q`

Expected: FAIL until manual text is updated.

- [x] **Step 3: Update manual and regenerate PDF**

Rewrite the profile placement section to use individual DXF files first, keeping the combined file as overview/reference only.

- [x] **Step 4: Verify docs and PDF**

Run:

```bash
.venv/bin/python scripts/generate_onshape_manual_pdf.py
.venv/bin/pytest tests/test_project_docs.py -q
```

Expected: PASS.

### Task 3: Full verification and integration

**Files:**
- All touched files

- [x] **Step 1: Run full verification**

Run:

```bash
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

Expected: all pass.

- [ ] **Step 2: Merge and push**

Commit the feature, fast-forward merge to `main`, run verification on `main`, then push to GitHub.
