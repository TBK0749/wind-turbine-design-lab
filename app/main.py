"""Streamlit entry point for Wind Turbine Design Lab."""

import sys
from pathlib import Path

import numpy as np
import streamlit as st
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.components.airfoil_help import render_airfoil_help  # noqa: E402
from app.components.airfoil_preview import render_airfoil_preview  # noqa: E402
from app.components.blade_geometry import render_blade_geometry  # noqa: E402
from app.components.calibration_lab import render_calibration_lab  # noqa: E402
from app.components.charts import render_performance_charts  # noqa: E402
from app.components.design_compare import render_design_comparison  # noqa: E402
from app.components.input_panel import render_input_panel  # noqa: E402
from app.components.learning_guide import (  # noqa: E402
    render_key_terms_glossary,
    render_quick_start_guide,
)
from app.components.result_cards import (  # noqa: E402
    render_airfoil_cards,
    render_competition_cards,
    render_result_cards,
)
from windlab.simulator import (  # noqa: E402
    performance_curve,
    result_as_csv,
    result_as_design_sheet,
    result_as_json,
    simulate,
)

st.set_page_config(page_title="Wind Turbine Design Lab", page_icon="🌬️", layout="wide")

st.title("🌬️ Wind Turbine Design Lab")
st.caption("Change one variable at a time, observe the model, and record what you learn.")
st.info(
    "Educational simulation only. Results are simplified estimates and are not suitable "
    "for certifying or constructing a real wind turbine.",
    icon="ℹ️",
)

design_tab, calibration_tab, guide_tab, glossary_tab = st.tabs(
    ["Design Lab", "Calibration", "Guide", "Glossary"]
)

with design_tab:
    try:
        simulation_input = render_input_panel()
        simulation_result = simulate(simulation_input)
    except (ValidationError, ValueError) as error:
        st.error(str(error))
        st.stop()

    render_result_cards(simulation_result)

    render_blade_geometry(simulation_input)
    render_airfoil_preview(simulation_input)
    render_airfoil_help()

    st.subheader("Airfoil result")
    render_airfoil_cards(simulation_result)
    st.caption(
        "Simplified lift/drag estimate for the selected blade cross-section. "
        "This guides classroom comparisons, not certified aerodynamic design."
    )

    st.subheader("Competition result")
    render_competition_cards(simulation_result)
    st.caption(
        "Estimated score at the external load. Electrical power (mW) = load voltage (V) "
        "× load current (mA)."
    )

    for warning in simulation_result.warnings:
        st.warning(warning)

    st.subheader("Performance across wind speeds")
    maximum_curve_speed = min(30.0, max(15.0, simulation_input.wind_speed_m_s * 1.5))
    curve_speeds = np.linspace(1.0, maximum_curve_speed, 20)
    render_performance_charts(performance_curve(simulation_input, curve_speeds))

    left, right = st.columns([2, 1])
    with left:
        st.subheader("Recommended next experiments")
        for recommendation in simulation_result.recommendations:
            st.write(f"- {recommendation}")
    with right:
        st.subheader("Export this run")
        st.download_button(
            "Download design sheet",
            result_as_design_sheet(simulation_input, simulation_result),
            file_name="wind_turbine_design_sheet.md",
            mime="text/markdown",
            width="stretch",
        )
        st.download_button(
            "Download CSV",
            result_as_csv(simulation_input, simulation_result),
            file_name="wind_turbine_result.csv",
            mime="text/csv",
            width="stretch",
        )
        st.download_button(
            "Download JSON",
            result_as_json(simulation_input, simulation_result),
            file_name="wind_turbine_result.json",
            mime="application/json",
            width="stretch",
        )
        st.caption("Download design sheet exports a printable Markdown build report.")

    render_design_comparison(simulation_input, simulation_result)

    with st.expander("Model details"):
        st.write(
            "Available wind power is calculated as ½ρAV³. Mechanical power is Cp times "
            "available power in simple geometry mode. In section-table mode, the default "
            "BEMT-lite model sums lift and drag forces along blade segments using local "
            "radius, chord, twist, airfoil family, relative wind speed, and bounded "
            "induction-factor estimates. RPM is estimated from tip-speed ratio, then "
            "adjusted by blade mass and trial-duration spin-up. "
            "Surface finish affects aerodynamic drag. "
            "Generator voltage scales with RPM; current is estimated from generator and "
            "load resistance. Electrical output cannot exceed the available mechanical "
            "power after generator efficiency. Cp, TSR, and airfoil values remain "
            "educational approximations, not a replacement for full QBlade/BEMT validation."
        )

with calibration_tab:
    render_calibration_lab(simulation_input, simulation_result)

with guide_tab:
    render_quick_start_guide()

with glossary_tab:
    render_key_terms_glossary()
