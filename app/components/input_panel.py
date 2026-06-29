"""Sidebar controls for simulation inputs."""

import pandas as pd
import streamlit as st

from windlab.airfoils import AIRFOIL_LIBRARY
from windlab.blade_geometry import competition_50cm_sections
from windlab.materials import MATERIALS, SURFACE_FINISHES
from windlab.models import BladeSection, SimulationInput
from windlab.section_airfoils import get_section_airfoil, section_airfoil_options


def _competition_section_frame() -> pd.DataFrame:
    """Build an editable centimetre-based table for the supplied blade."""

    sections = competition_50cm_sections()
    labels = ["1 (Root)", "2", "3", "4", "5", "6 (Tip)"]
    return pd.DataFrame(
        {
            "Section": labels,
            "Position (cm)": [section.position_m * 100.0 for section in sections],
            "Chord (cm)": [section.chord_m * 100.0 for section in sections],
            "Twist (deg)": [section.twist_angle_deg for section in sections],
            "Airfoil": [section.airfoil_name for section in sections],
            "Airfoil role / purpose": [section.airfoil_role for section in sections],
        }
    )


def _sections_from_frame(frame: pd.DataFrame) -> tuple[BladeSection, ...]:
    """Convert complete editable rows from centimetres to SI units."""

    sections: list[BladeSection] = []
    for _, row in frame.iterrows():
        values = (
            row.get("Position (cm)"),
            row.get("Chord (cm)"),
            row.get("Twist (deg)"),
            row.get("Airfoil"),
        )
        if any(pd.isna(value) for value in values):
            continue
        airfoil_name = str(values[3])
        role = row.get("Airfoil role / purpose")
        airfoil_role = (
            get_section_airfoil(airfoil_name).role
            if pd.isna(role) or not str(role).strip()
            else str(role)
        )
        sections.append(
            BladeSection(
                position_m=float(values[0]) / 100.0,
                chord_m=float(values[1]) / 100.0,
                twist_angle_deg=float(values[2]),
                airfoil_name=airfoil_name,
                airfoil_role=airfoil_role,
            )
        )
    return tuple(sorted(sections, key=lambda section: section.position_m))


def render_input_panel() -> SimulationInput:
    """Render grouped controls and return validated inputs."""

    st.sidebar.header("Design inputs")
    with st.sidebar.expander("Wind", expanded=True):
        wind_speed = st.number_input("Wind speed (m/s)", 0.5, 40.0, 8.0, 0.5)
        air_density = st.number_input("Air density (kg/m³)", 0.5, 1.5, 1.225, 0.005)

    with st.sidebar.expander("Rotor", expanded=True):
        rotor_radius = st.number_input("Blade length / rotor radius (m)", 0.06, 100.0, 0.45, 0.05)
        hub_radius = st.number_input("Hub radius (m)", 0.0, 20.0, 0.10, 0.01)
        blade_count = st.slider("Number of blades", 1, 12, 3)

    geometry_mode = st.sidebar.radio(
        "Blade geometry input",
        ["Section table", "Simple root/tip"],
        help="Use the section table when the blade is measured at several positions.",
    )

    pitch = st.sidebar.slider(
        "Whole-blade pitch angle (°)",
        -10.0,
        35.0,
        0.0,
        0.5,
        help="Pitch rotates the whole blade. Local twist is entered separately per section.",
    )

    blade_sections: tuple[BladeSection, ...] = ()
    if geometry_mode == "Section table":
        st.subheader("Blade geometry table")
        st.caption(
            "Enter the measurements used to build one blade. Position and chord are in "
            "centimetres; the simulator converts them to metres."
        )
        section_frame = st.data_editor(
            _competition_section_frame(),
            key="blade_section_editor",
            hide_index=True,
            num_rows="dynamic",
            width="stretch",
            column_config={
                "Section": st.column_config.TextColumn("Section", disabled=True),
                "Position (cm)": st.column_config.NumberColumn(
                    "Position (cm)", min_value=0.1, step=1.0, format="%.1f"
                ),
                "Chord (cm)": st.column_config.NumberColumn(
                    "Chord (cm)", min_value=0.1, step=0.1, format="%.1f"
                ),
                "Twist (deg)": st.column_config.NumberColumn(
                    "Twist (deg)", min_value=-20.0, max_value=60.0, step=1.0, format="%.1f"
                ),
                "Airfoil": st.column_config.SelectboxColumn(
                    "Airfoil",
                    options=section_airfoil_options(),
                    help="Airfoil assigned to this blade station.",
                    required=True,
                ),
                "Airfoil role / purpose": st.column_config.TextColumn(
                    "Airfoil role / purpose",
                    help="Why this airfoil is used at this blade station.",
                    width="large",
                ),
            },
        )
        st.markdown(
            "**Airfoil preset:** NACA 4418 → NACA 4415 → NACA 4412 → "
            "NACA 4412 → NACA 2412 → NACA 2412. "
            "Use thicker root sections for strength and thinner tip sections to reduce drag."
        )
        blade_sections = _sections_from_frame(section_frame)
        root_chord = blade_sections[0].chord_m if blade_sections else 0.09
        tip_chord = blade_sections[-1].chord_m if blade_sections else 0.02
        twist = blade_sections[0].twist_angle_deg if blade_sections else 20.0
    else:
        st.subheader("Simple blade geometry")
        root_chord = st.number_input("Root chord (m)", 0.01, 10.0, 0.18, 0.01)
        tip_chord = st.number_input("Tip chord (m)", 0.005, 10.0, 0.08, 0.005)
        twist = st.slider("Twist angle (°)", 0.0, 45.0, 12.0, 0.5)

    if geometry_mode == "Section table":
        airfoil_type = "High-lift airfoil"
        st.sidebar.markdown(
            "**Section table airfoils override the simple airfoil selector.** "
            "Change Airfoil values directly in the blade geometry table."
        )
        st.sidebar.info(
            "Section table airfoils override the simple airfoil selector. "
            "Change Airfoil values directly in the blade geometry table.",
            icon="ℹ️",
        )
    else:
        with st.sidebar.expander("Airfoil", expanded=True):
            airfoil_type = st.selectbox(
                "Airfoil type",
                list(AIRFOIL_LIBRARY),
                help=(
                    "Choose the blade cross-section family used by the simplified lift/drag model."
                ),
            )
            st.caption(AIRFOIL_LIBRARY[airfoil_type].description)

    with st.sidebar.expander("Blade physical", expanded=True):
        blade_mass = st.number_input("Mass per blade (kg)", 0.01, 10000.0, 1.0, 0.1)
        material = st.selectbox("Material", list(MATERIALS))
        selected_material = MATERIALS[material]
        st.caption(
            f"Preset density: {selected_material.density_kg_m3:,.0f} kg/m³ · "
            f"roughness: {selected_material.roughness_factor:.2f}"
        )
        surface_finish = st.selectbox("Surface finish", list(SURFACE_FINISHES))
        st.caption(SURFACE_FINISHES[surface_finish].description)
        use_custom_material_properties = st.checkbox(
            "Use custom material properties",
            value=False,
            help="Override the selected material density, surface roughness, and durability.",
        )
        custom_material_density = st.number_input(
            "Material density (kg/m³)",
            1.0,
            30000.0,
            float(selected_material.density_kg_m3),
            10.0,
            disabled=not use_custom_material_properties,
        )
        custom_material_roughness = st.number_input(
            "Material roughness factor",
            0.10,
            1.50,
            float(selected_material.roughness_factor),
            0.01,
            disabled=not use_custom_material_properties,
        )
        custom_material_durability = st.number_input(
            "Material durability factor",
            0.0,
            1.0,
            float(selected_material.durability_factor),
            0.05,
            disabled=not use_custom_material_properties,
        )

        use_estimated_blade_mass = st.checkbox(
            "Estimate blade mass from density",
            value=False,
            help="Use blade planform area × thickness × material density instead of manual mass.",
        )
        blade_thickness = st.number_input(
            "Blade thickness (m)",
            0.0001,
            0.5000,
            0.0050,
            0.0005,
            format="%.4f",
            disabled=not use_estimated_blade_mass,
        )

    with st.sidebar.expander("Competition generator", expanded=True):
        volts_per_1000_rpm = st.number_input(
            "Generator voltage (V per 1,000 RPM)", 0.01, 100.0, 1.5, 0.1
        )
        internal_resistance = st.number_input(
            "Generator internal resistance (Ω)", 0.0, 10000.0, 20.0, 1.0
        )
        load_resistance = st.number_input("Competition load (Ω)", 0.01, 1000000.0, 100.0, 1.0)
        generator_efficiency = st.slider("Generator efficiency (%)", 1.0, 100.0, 70.0, 1.0)
        gear_ratio = st.number_input("Gear ratio (generator ÷ rotor)", 0.01, 100.0, 1.0, 0.1)
        trial_duration = st.number_input("Trial duration (seconds)", 0.1, 86400.0, 60.0, 1.0)

    with st.sidebar.expander("Advanced calibration", expanded=False):
        st.caption(
            "Teacher/testing controls. Leave these at default values for normal classroom use."
        )
        air_dynamic_viscosity = st.number_input(
            "Air dynamic viscosity (kg/m·s)",
            0.000001,
            0.000100,
            0.0000181,
            0.0000001,
            format="%.7f",
        )
        practical_cp_limit = st.number_input("Practical Cp limit", 0.05, 0.592, 0.50, 0.01)
        airfoil_efficiency_multiplier = st.number_input(
            "Airfoil efficiency multiplier", 0.10, 2.00, 1.00, 0.05
        )
        mechanical_loss = st.slider("Mechanical loss (%)", 0.0, 95.0, 0.0, 1.0)
        startup_torque = st.number_input("Startup/cogging torque (N·m)", 0.0, 10000.0, 0.0, 0.01)

        st.divider()
        use_hub_area_loss = st.checkbox("Use hub area loss", value=True)
        use_airfoil_correction = st.checkbox("Use airfoil correction", value=True)
        use_material_roughness = st.checkbox("Use material roughness", value=True)
        use_generator_power_cap = st.checkbox("Use generator power cap", value=True)
        use_generator_load_feedback = st.checkbox("Use generator load feedback", value=True)
        use_practical_cp_limit = st.checkbox("Use practical Cp limit", value=True)
        use_reynolds_correction = st.checkbox("Use Reynolds correction", value=True)
        use_prandtl_loss = st.checkbox("Use Prandtl tip/root loss", value=True)
        use_startup_torque_loss = st.checkbox("Use startup torque loss", value=True)
        use_bemt_lite = st.checkbox("Use BEMT-lite section model", value=True)

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
        blade_sections=blade_sections,
        airfoil_type=airfoil_type,
        blade_mass_kg=blade_mass,
        material=material,
        surface_finish=surface_finish,
        use_custom_material_properties=use_custom_material_properties,
        custom_material_density_kg_m3=custom_material_density,
        custom_material_roughness_factor=custom_material_roughness,
        custom_material_durability_factor=custom_material_durability,
        use_estimated_blade_mass=use_estimated_blade_mass,
        blade_thickness_m=blade_thickness,
        generator_volts_per_1000_rpm=volts_per_1000_rpm,
        generator_internal_resistance_ohm=internal_resistance,
        load_resistance_ohm=load_resistance,
        generator_efficiency_percent=generator_efficiency,
        gear_ratio=gear_ratio,
        trial_duration_s=trial_duration,
        air_dynamic_viscosity_kg_m_s=air_dynamic_viscosity,
        practical_cp_limit=practical_cp_limit,
        airfoil_efficiency_multiplier=airfoil_efficiency_multiplier,
        mechanical_loss_percent=mechanical_loss,
        startup_torque_n_m=startup_torque,
        use_hub_area_loss=use_hub_area_loss,
        use_airfoil_correction=use_airfoil_correction,
        use_material_roughness=use_material_roughness,
        use_generator_power_cap=use_generator_power_cap,
        use_generator_load_feedback=use_generator_load_feedback,
        use_practical_cp_limit=use_practical_cp_limit,
        use_reynolds_correction=use_reynolds_correction,
        use_prandtl_loss=use_prandtl_loss,
        use_startup_torque_loss=use_startup_torque_loss,
        use_bemt_lite_section_model=use_bemt_lite,
    )
