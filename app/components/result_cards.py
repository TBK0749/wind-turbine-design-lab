"""Headline result cards."""

import streamlit as st

from windlab.models import SimulationResult


def render_result_cards(result: SimulationResult) -> None:
    """Display the main calculated outputs."""

    first = st.columns(4)
    first[0].metric("RPM", f"{result.rpm:,.1f}")
    first[1].metric("Torque", f"{result.torque_n_m:,.2f} N·m")
    first[2].metric("Mechanical power", f"{result.mechanical_power_w:,.1f} W")
    first[3].metric("Design score", f"{result.design_score:.1f}/100")

    second = st.columns(4)
    second[0].metric("Cp", f"{result.cp:.3f}")
    second[1].metric("Tip-speed ratio", f"{result.tip_speed_ratio:.2f}")
    second[2].metric("Efficiency", f"{result.efficiency_percent:.1f}%")
    second[3].metric("Rotor area", f"{result.rotor_area_m2:.2f} m²")
