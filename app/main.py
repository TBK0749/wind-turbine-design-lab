"""Streamlit entry point for Wind Turbine Design Lab."""

import sys
from pathlib import Path

import numpy as np
import streamlit as st
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.components.charts import render_performance_charts  # noqa: E402
from app.components.input_panel import render_input_panel  # noqa: E402
from app.components.result_cards import render_result_cards  # noqa: E402
from windlab.simulator import (  # noqa: E402
    performance_curve,
    result_as_csv,
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

try:
    simulation_input = render_input_panel()
    simulation_result = simulate(simulation_input)
except (ValidationError, ValueError) as error:
    st.error(str(error))
    st.stop()

render_result_cards(simulation_result)

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

with st.expander("Model details"):
    st.write(
        "Available wind power is calculated as ½ρAV³. Mechanical power is Cp times "
        "available power. RPM is estimated from tip-speed ratio, and torque is power "
        "divided by angular speed. Cp and TSR are bounded educational approximations."
    )
