"""Airfoil profile preview charts."""

import plotly.graph_objects as go
import streamlit as st

from windlab.airfoil_geometry import airfoil_profile_points
from windlab.models import SimulationInput
from windlab.section_airfoils import get_section_airfoil


def render_airfoil_preview(inputs: SimulationInput) -> None:
    """Render student-facing 2D cross-section previews for selected airfoils."""

    st.subheader("Airfoil profile preview")
    if not inputs.blade_sections:
        st.caption("Switch to Section table mode to preview specific NACA station airfoils.")
        return

    unique_airfoils = list(dict.fromkeys(section.airfoil_name for section in inputs.blade_sections))
    tabs = st.tabs(unique_airfoils)
    for tab, airfoil_name in zip(tabs, unique_airfoils, strict=True):
        airfoil = get_section_airfoil(airfoil_name)
        points = airfoil_profile_points(airfoil_name)
        xs = [x for x, _ in points]
        ys = [y for _, y in points]
        with tab:
            figure = go.Figure()
            figure.add_trace(
                go.Scatter(
                    x=xs,
                    y=ys,
                    mode="lines",
                    fill="toself",
                    name=airfoil_name,
                    line={"color": "#1f77b4", "width": 2},
                    fillcolor="rgba(31, 119, 180, 0.18)",
                )
            )
            figure.add_shape(
                type="line",
                x0=0.0,
                x1=1.0,
                y0=0.0,
                y1=0.0,
                line={"color": "#888", "dash": "dot"},
            )
            figure.update_layout(
                title=f"{airfoil_name} normalized cross-section",
                xaxis_title="Chord position",
                yaxis_title="Thickness / camber",
                yaxis={"scaleanchor": "x", "scaleratio": 1},
                margin={"l": 20, "r": 20, "t": 55, "b": 20},
                height=320,
            )
            st.plotly_chart(figure, width="stretch")
            st.markdown(f"**Best zone:** {airfoil.best_zone}")
            st.write(airfoil.plain_language_summary)
