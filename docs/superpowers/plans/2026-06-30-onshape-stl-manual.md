# Onshape Beginner-to-STL Manual Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the Onshape workflow manual so a beginner can go from the downloaded Onshape package to a checked STL export.

**Architecture:** Keep the existing Markdown manual and PDF output as the source of truth for the long guide. Update the shorter `onshape_build_guide.md` generated inside each ZIP package so exported packages also explain hub, circular pattern, and STL export. Add documentation tests that lock the critical beginner workflow phrases.

**Tech Stack:** Markdown, ReportLab PDF generator, pytest documentation tests, ruff.

---

### Task 1: Lock beginner-to-STL documentation requirements

**Files:**
- Modify: `tests/test_project_docs.py`
- Modify: `tests/test_onshape_export.py`

- [ ] **Step 1: Add failing manual coverage test**

Add assertions that `docs/onshape_workflow_manual.md` mentions hub sketch setup, avoiding Mate connector sketches, circular pattern settings, diameter checks, and STL export.

- [ ] **Step 2: Add failing ZIP guide coverage test**

Add assertions that the generated `onshape_build_guide.md` mentions hub creation, 3-blade circular pattern, and STL export.

- [ ] **Step 3: Run focused tests and verify failure**

Run:

```bash
.venv/bin/pytest tests/test_project_docs.py::test_onshape_manual_covers_beginner_to_stl_workflow tests/test_onshape_export.py::test_onshape_package_build_guide_mentions_stl_workflow -q
```

Expected: fail until the manual and generated guide are expanded.

### Task 2: Expand the beginner manual and generated guide

**Files:**
- Modify: `docs/onshape_workflow_manual.md`
- Modify: `windlab/onshape_export.py`

- [ ] **Step 1: Rewrite the later manual workflow**

Expand the Onshape workflow after Loft to include: how `blade_planform.dxf` is used, what not to select for hub sketching, hub cylinder and shaft hole dimensions, union/merge guidance, circular pattern settings, final diameter check, STL export settings, and slicer checks.

- [ ] **Step 2: Expand the generated in-package guide**

Update `onshape_build_guide()` so exported ZIP packages include the short version of the same hub, pattern, and STL workflow.

- [ ] **Step 3: Run focused tests and verify pass**

Run:

```bash
.venv/bin/pytest tests/test_project_docs.py::test_onshape_manual_covers_beginner_to_stl_workflow tests/test_onshape_export.py::test_onshape_package_build_guide_mentions_stl_workflow -q
```

Expected: pass.

### Task 3: Regenerate and verify the PDF

**Files:**
- Modify: `output/pdf/Wind_Turbine_Design_Lab_Onshape_Workflow_Manual.pdf`

- [ ] **Step 1: Regenerate PDF**

Run:

```bash
.venv/bin/python scripts/generate_onshape_manual_pdf.py
```

- [ ] **Step 2: Render PDF pages**

Run:

```bash
rm -rf tmp/pdfs/onshape_manual
mkdir -p tmp/pdfs/onshape_manual
pdftoppm -png output/pdf/Wind_Turbine_Design_Lab_Onshape_Workflow_Manual.pdf tmp/pdfs/onshape_manual/page
```

- [ ] **Step 3: Inspect the rendered pages**

Open the rendered pages that contain hub, circular pattern, and STL export text. Confirm tables and paragraphs are readable with no clipping or overlap.

### Task 4: Full verification and publish

**Files:**
- All touched files

- [ ] **Step 1: Run full verification**

Run:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pytest -q
```

- [ ] **Step 2: Commit and push**

Commit with:

```bash
git commit -m "docs: expand Onshape STL workflow manual"
git push origin main
```
