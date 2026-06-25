"""Sidebar controls for simulation inputs."""

import streamlit as st

from windlab.materials import MATERIALS
from windlab.models import SimulationInput


def render_input_panel() -> SimulationInput:
    """Render grouped controls and return validated inputs."""

    st.sidebar.header("Design inputs")
    with st.sidebar.expander("Wind", expanded=True):
        wind_speed = st.number_input("Wind speed (m/s)", 0.5, 40.0, 8.0, 0.5)
        air_density = st.number_input("Air density (kg/m³)", 0.5, 1.5, 1.225, 0.005)

    with st.sidebar.expander("Rotor", expanded=True):
        rotor_radius = st.number_input("Rotor radius (m)", 0.06, 100.0, 1.0, 0.05)
        hub_radius = st.number_input("Hub radius (m)", 0.0, 20.0, 0.1, 0.01)
        blade_count = st.slider("Number of blades", 1, 12, 3)

    with st.sidebar.expander("Blade geometry", expanded=True):
        root_chord = st.number_input("Root chord (m)", 0.01, 10.0, 0.18, 0.01)
        tip_chord = st.number_input("Tip chord (m)", 0.005, 10.0, 0.08, 0.005)
        pitch = st.slider("Pitch angle (°)", -10.0, 35.0, 4.0, 0.5)
        twist = st.slider("Twist angle (°)", 0.0, 45.0, 12.0, 0.5)

    with st.sidebar.expander("Blade physical", expanded=True):
        blade_mass = st.number_input("Mass per blade (kg)", 0.01, 10000.0, 1.0, 0.1)
        material = st.selectbox("Material", list(MATERIALS))

    return SimulationInput(
        wind_speed_m_s=wind_speed,
        air_density_kg_m3=air_density,
        rotor_radius_m=rotor_radius,
        hub_radius_m=hub_radius,
        blade_count=blade_count,
        root_chord_m=root_chord,
        tip_chord_m=tip_chord,
        pitch_angle_deg=pitch,
        twist_angle_deg=twist,
        blade_mass_kg=blade_mass,
        material=material,
    )
