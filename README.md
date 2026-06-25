# Wind Turbine Design Lab

Wind Turbine Design Lab is a local-first educational simulator for students
and teachers. It helps users explore how wind conditions, rotor dimensions,
blade geometry, mass, and material affect estimated turbine performance.

> The results are simplified educational estimates. They are not certified
> engineering calculations and must not be used to approve a real turbine.

## MVP features

- Configure wind, rotor, blade geometry, mass, and material.
- Estimate RPM, torque, mechanical power, Cp, tip-speed ratio, and efficiency.
- Review a student-friendly design score and recommendations.
- Plot RPM, torque, and power across a wind-speed range.
- Download the current result as CSV or JSON.
- Run completely on the user's computer.

## Install

Install Python 3.12+, Git, and [uv](https://docs.astral.sh/uv/), then run:

```bash
git clone <repository-url>
cd wind-turbine-design-lab
uv sync
```

## Run

```bash
uv run streamlit run app/main.py
```

Streamlit normally opens `http://localhost:8501`.

## Quality checks

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Current physics scope

Version 0.1 uses wind power, swept area, an educational bounded Cp
approximation, and an estimated tip-speed ratio. See
`docs/physics_model.md` for assumptions and limitations.

## Roadmap

- v0.2.0: save and compare multiple designs
- v0.3.0: structured experiment log
- v0.4.0: improved Cp model
- v1.0.0: stable classroom release
- v2.x: Blade Element Momentum Theory (BEMT)
