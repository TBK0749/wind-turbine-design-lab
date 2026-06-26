"""Blade geometry visualization for fabrication and review."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from windlab.models import SimulationInput


def render_blade_geometry(inputs: SimulationInput) -> None:
    """Render a planform preview plus chord and angle distributions."""

    if not inputs.blade_sections:
        st.caption("Switch to Section table mode to preview individual blade stations.")
        return

    sections = inputs.blade_sections
    positions_cm = [section.position_m * 100.0 for section in sections]
    chords_cm = [section.chord_m * 100.0 for section in sections]
    twists = [section.twist_angle_deg for section in sections]
    effective_angles = [twist + inputs.pitch_angle_deg for twist in twists]

    st.subheader("Blade build preview")
    preview, distributions = st.columns([1.2, 1.0])

    with preview:
        half_chords = [chord / 2.0 for chord in chords_cm]
        outline_x = positions_cm + list(reversed(positions_cm))
        outline_y = half_chords + [-value for value in reversed(half_chords)]
        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=outline_x,
                y=outline_y,
                fill="toself",
                name="Blade planform",
                line={"color": "#1f77b4"},
                fillcolor="rgba(31, 119, 180, 0.25)",
            )
        )
        for position, half_chord in zip(positions_cm, half_chords, strict=True):
            figure.add_shape(
                type="line",
                x0=position,
                x1=position,
                y0=-half_chord,
                y1=half_chord,
                line={"color": "#666", "dash": "dot"},
            )
        figure.update_layout(
            title="Top-view cutting shape",
            xaxis_title="Position from rotor centre (cm)",
            yaxis_title="Half chord (cm)",
            yaxis={"scaleanchor": "x", "scaleratio": 1},
            margin={"l": 20, "r": 20, "t": 55, "b": 20},
        )
        st.plotly_chart(figure, width="stretch")

    with distributions:
        figure = make_subplots(specs=[[{"secondary_y": True}]])
        figure.add_trace(
            go.Scatter(
                x=positions_cm,
                y=chords_cm,
                mode="lines+markers",
                name="Chord (cm)",
            ),
            secondary_y=False,
        )
        figure.add_trace(
            go.Scatter(
                x=positions_cm,
                y=effective_angles,
                mode="lines+markers",
                name="Twist + pitch (deg)",
            ),
            secondary_y=True,
        )
        figure.update_xaxes(title_text="Position (cm)")
        figure.update_yaxes(title_text="Chord (cm)", secondary_y=False)
        figure.update_yaxes(title_text="Effective angle (deg)", secondary_y=True)
        figure.update_layout(
            title="Geometry distribution",
            margin={"l": 20, "r": 20, "t": 55, "b": 20},
        )
        st.plotly_chart(figure, width="stretch")

    build_table = pd.DataFrame(
        {
            "Section": [
                "Root" if index == 0 else "Tip" if index == len(sections) - 1 else str(index + 1)
                for index in range(len(sections))
            ],
            "Position (cm)": positions_cm,
            "Chord (cm)": chords_cm,
            "Local twist (°)": twists,
            "Pitch + twist (°)": effective_angles,
            "Airfoil": [section.airfoil_name for section in sections],
            "Airfoil role / purpose": [section.airfoil_role for section in sections],
        }
    )
    st.dataframe(build_table, hide_index=True, width="stretch")
