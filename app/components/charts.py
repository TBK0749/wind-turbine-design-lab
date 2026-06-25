"""Plotly charts for performance curves."""

import pandas as pd
import plotly.express as px
import streamlit as st


def render_performance_charts(rows: list[dict[str, float]]) -> None:
    """Render power, RPM, and torque against wind speed."""

    frame = pd.DataFrame(rows)
    tabs = st.tabs(["Power", "RPM", "Torque"])
    charts = (
        ("Power (W)", "Mechanical power"),
        ("RPM", "Rotor speed"),
        ("Torque (N·m)", "Torque"),
    )
    for tab, (column, title) in zip(tabs, charts, strict=True):
        with tab:
            figure = px.line(
                frame,
                x="Wind speed (m/s)",
                y=column,
                markers=True,
                title=f"{title} vs wind speed",
            )
            figure.update_layout(margin={"l": 20, "r": 20, "t": 55, "b": 20})
            st.plotly_chart(figure, width="stretch")
