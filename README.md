# Wind Turbine Design Lab

Wind Turbine Design Lab is a local-first educational simulator for students
and teachers. It helps users explore how wind conditions, rotor dimensions,
blade geometry, mass, and material affect estimated turbine performance.

> The results are simplified educational estimates. They are not certified
> engineering calculations and must not be used to approve a real turbine.

## MVP features

- Configure wind, rotor, blade geometry, mass, and material.
- Design a blade with editable radial Position, Chord, Twist, and station Airfoil choices.
- Assign NACA-style airfoils per blade station and document each section's role.
- Blend root, mid-span, and tip airfoil effects so station changes affect the estimate.
- Preview the cutting outline and chord/twist distribution for fabrication.
- Choose a classroom airfoil family and review simplified lift/drag feedback.
- Apply low-Reynolds and Prandtl-style root/tip loss corrections in the
  section-table model.
- Estimate RPM, torque, mechanical power, Cp, tip-speed ratio, and efficiency.
- Review a student-friendly design score and recommendations.
- Plot RPM, torque, and power across a wind-speed range.
- Estimate competition voltage, current, electrical power in mW, and trial energy.
- Configure generator voltage constant, resistance, load, efficiency, gearing, and time.
- Read the built-in English guide and key-term glossary in the dashboard.
- Download the current result as CSV or JSON.
- Log measured prototype trials in the Phase 2 Calibration scaffold.
- Compare predicted vs measured RPM and mW, then export a calibration worksheet.
- Run completely on the user's computer.

## Local installation guide

This project is designed to run on each user's own computer. You do not need
cloud hosting, Streamlit Cloud, or any paid service for local classroom use.

### Beginner PDF manual

For first-time users who are not familiar with code, use the complete
[Windows and macOS installation manual](output/pdf/Wind_Turbine_Design_Lab_Local_Installation_Guide.pdf).
It includes step-by-step setup, first run, updates, and troubleshooting.

### 1. Install requirements

Install:

- Python 3.12 or newer
- Git, if you want to clone the repository
- [uv](https://docs.astral.sh/uv/), recommended for simple dependency setup

### 2. Get the project

Option A — clone with Git:

```bash
git clone https://github.com/TBK0749/wind-turbine-design-lab.git
cd wind-turbine-design-lab
```

Option B — Download as ZIP:

1. Open the GitHub repository page.
2. Click `Code`.
3. Click `Download ZIP`.
4. Unzip the file.
5. Open a terminal in the unzipped project folder.

### 3. Install dependencies

With uv:

```bash
uv sync
```

### 4. Run the app locally

```bash
uv run streamlit run app/main.py
```

Streamlit normally opens:

```text
http://localhost:8501
```

or:

```text
http://127.0.0.1:8501
```

### 5. Stop the app

Return to the terminal that is running Streamlit and press:

```text
Ctrl + C
```

## Updating to the latest version

If you originally installed the project with Git, you do not need to clone it
again. Stop the app, open a terminal in the project folder, and run:

```bash
git pull
uv sync
uv run streamlit run app/main.py
```

`git pull` downloads the latest project files, while `uv sync` installs or
updates any required dependencies.

If you downloaded the project as a ZIP file, `git pull` is not available.
Download the latest ZIP from GitHub and replace the old project folder, or use
the Git installation method next time for easier updates. Keep exported CSV,
JSON, and experiment files outside the project folder before replacing it.

### Common local issues

- If Streamlit asks for an email address, press `Enter` without typing anything.
- If port `8501` is busy, stop the old Streamlit terminal with `Ctrl + C`, then run again.
- If `git pull` reports local changes, save your exported work outside the
  project folder and avoid editing the project source files.
- Do not click Deploy. This project is meant to run locally unless your teacher
  explicitly asks you to publish it online.

## Quality checks

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Current physics scope

The simulator uses wind power, swept area, an estimated tip-speed ratio, and
two classroom model paths. Simple root/tip geometry uses an educational bounded
Cp approximation. Section-table geometry uses a BEMT-lite section-force model
that sums lift and drag along blade segments using local radius, chord, twist,
airfoil family, relative wind speed, low-Reynolds penalties, and optional
Prandtl-style root/tip loss. See `docs/physics_model.md` for assumptions and
limitations, and `docs/paper_model_notes.md` for the first paper-backed
reliability pass.

The current paper-validation status is tracked in
[`docs/model_validation_report.md`](docs/model_validation_report.md). The report
compares selected paper benchmarks with the simulator and clearly marks which
rows are runnable, broad range checks, or reference-only values.

The app also includes a collapsed **Advanced calibration** panel for teachers
and competition teams. It can tune uncertain constants such as air viscosity,
Cp limit, airfoil multiplier, mechanical loss, startup/cogging torque, and
generator capping. Leave these controls at their defaults for normal student
comparisons, and record any custom settings with measured test results.

The **Blade physical** panel supports custom material properties. Users can
override material density, roughness, and durability, then either enter blade
mass manually or estimate blade mass from material density, blade thickness,
and blade planform area. Blade mass affects rotor inertia and timed-run spin-up,
while surface finish affects aerodynamic drag.

The **Calibration** tab is a Phase 2 scaffold. It records measured prototype
RPM and mW, calculates prediction error and correction factors, and exports CSV
or Markdown worksheets. It does not automatically change the physics model until
real repeatable test data is available.

## Roadmap

- v0.2.0: measured-data calibration workflow
- v0.3.0: persistent experiment log files
- v0.4.0: calibration from repeated wind-tunnel test results
- v1.0.0: stable classroom release
- v2.x: full iterative Blade Element Momentum Theory (BEMT)
