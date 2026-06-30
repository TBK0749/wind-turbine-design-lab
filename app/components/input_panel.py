"""Sidebar controls for simulation inputs."""

import pandas as pd
import streamlit as st

from app.components.design_workspace import active_design, widget_key
from windlab.airfoils import AIRFOIL_LIBRARY
from windlab.blade_geometry import competition_50cm_sections
from windlab.materials import MATERIALS, SURFACE_FINISHES
from windlab.models import BladeSection, SimulationInput
from windlab.section_airfoils import get_section_airfoil, section_airfoil_options


def _section_frame_from_sections(sections: tuple[BladeSection, ...]) -> pd.DataFrame:
    """Build an editable centimetre-based table for the supplied blade."""

    labels = [
        "1 (Root)"
        if index == 0
        else f"{len(sections)} (Tip)"
        if index == len(sections) - 1
        else str(index + 1)
        for index, _ in enumerate(sections)
    ]
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


def _competition_section_frame() -> pd.DataFrame:
    """Build the default competition section table."""

    return _section_frame_from_sections(competition_50cm_sections())


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

    design = active_design()
    st.sidebar.header("Design inputs")
    with st.sidebar.expander("Wind", expanded=True):
        wind_speed = st.number_input(
            "Wind speed (m/s)",
            0.5,
            40.0,
            float(design.wind_speed_m_s),
            0.5,
            key=widget_key("wind_speed_m_s"),
        )
        air_density = st.number_input(
            "Air density (kg/m³)",
            0.5,
            1.5,
            float(design.air_density_kg_m3),
            0.005,
            key=widget_key("air_density_kg_m3"),
        )

    with st.sidebar.expander("Rotor", expanded=True):
        rotor_radius = st.number_input(
            "Blade length / rotor radius (m)",
            0.06,
            100.0,
            float(design.rotor_radius_m),
            0.05,
            key=widget_key("rotor_radius_m"),
        )
        hub_radius = st.number_input(
            "Hub radius (m)",
            0.0,
            20.0,
            float(design.hub_radius_m),
            0.01,
            key=widget_key("hub_radius_m"),
        )
        blade_count = st.slider(
            "Number of blades",
            1,
            12,
            int(design.blade_count),
            key=widget_key("blade_count"),
        )

    geometry_options = ["Section table", "Simple root/tip"]
    default_geometry_mode = "Section table" if design.blade_sections else "Simple root/tip"
    geometry_mode = st.sidebar.radio(
        "Blade geometry input",
        geometry_options,
        index=geometry_options.index(default_geometry_mode),
        help="Use the section table when the blade is measured at several positions.",
        key=widget_key("geometry_mode"),
    )

    pitch = st.sidebar.slider(
        "Whole-blade pitch angle (°)",
        -10.0,
        35.0,
        float(design.pitch_angle_deg),
        0.5,
        help="Pitch rotates the whole blade. Local twist is entered separately per section.",
        key=widget_key("pitch_angle_deg"),
    )

    blade_sections: tuple[BladeSection, ...] = ()
    if geometry_mode == "Section table":
        st.subheader("Blade geometry table")
        st.caption(
            "Enter the measurements used to build one blade. Position and chord are in "
            "centimetres; the simulator converts them to metres."
        )
        base_sections = design.blade_sections or competition_50cm_sections()
        section_frame = st.data_editor(
            _section_frame_from_sections(base_sections),
            key=widget_key("blade_section_editor"),
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
        airfoil_sequence = " → ".join(section.airfoil_name for section in base_sections)
        st.markdown(
            f"**Airfoil preset:** {airfoil_sequence}. "
            "Use thicker root sections for strength and thinner tip sections to reduce drag."
        )
        blade_sections = _sections_from_frame(section_frame)
        root_chord = blade_sections[0].chord_m if blade_sections else 0.09
        tip_chord = blade_sections[-1].chord_m if blade_sections else 0.02
        twist = blade_sections[0].twist_angle_deg if blade_sections else 20.0
    else:
        st.subheader("Simple blade geometry")
        root_chord = st.number_input(
            "Root chord (m)",
            0.01,
            10.0,
            float(design.root_chord_m),
            0.01,
            key=widget_key("root_chord_m"),
        )
        tip_chord = st.number_input(
            "Tip chord (m)",
            0.005,
            10.0,
            float(design.tip_chord_m),
            0.005,
            key=widget_key("tip_chord_m"),
        )
        twist = st.slider(
            "Twist angle (°)",
            0.0,
            45.0,
            float(design.twist_angle_deg),
            0.5,
            key=widget_key("twist_angle_deg"),
        )

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
            airfoil_options = list(AIRFOIL_LIBRARY)
            airfoil_index = (
                airfoil_options.index(design.airfoil_type)
                if design.airfoil_type in airfoil_options
                else 0
            )
            airfoil_type = st.selectbox(
                "Airfoil type",
                airfoil_options,
                index=airfoil_index,
                help=(
                    "Choose the blade cross-section family used by the simplified lift/drag model."
                ),
                key=widget_key("airfoil_type"),
            )
            st.caption(AIRFOIL_LIBRARY[airfoil_type].description)

    with st.sidebar.expander("Blade physical", expanded=True):
        blade_mass = st.number_input(
            "Mass per blade (kg)",
            0.01,
            10000.0,
            float(design.blade_mass_kg),
            0.1,
            key=widget_key("blade_mass_kg"),
        )
        material_options = list(MATERIALS)
        material_index = (
            material_options.index(design.material) if design.material in material_options else 0
        )
        material = st.selectbox(
            "Material",
            material_options,
            index=material_index,
            key=widget_key("material"),
        )
        selected_material = MATERIALS[material]
        st.caption(
            f"Preset density: {selected_material.density_kg_m3:,.0f} kg/m³ · "
            f"roughness: {selected_material.roughness_factor:.2f}"
        )
        surface_options = list(SURFACE_FINISHES)
        surface_index = (
            surface_options.index(design.surface_finish)
            if design.surface_finish in surface_options
            else 0
        )
        surface_finish = st.selectbox(
            "Surface finish",
            surface_options,
            index=surface_index,
            key=widget_key("surface_finish"),
        )
        st.caption(SURFACE_FINISHES[surface_finish].description)
        use_custom_material_properties = st.checkbox(
            "Use custom material properties",
            value=bool(design.use_custom_material_properties),
            help="Override the selected material density, surface roughness, and durability.",
            key=widget_key("use_custom_material_properties"),
        )
        custom_material_density = st.number_input(
            "Material density (kg/m³)",
            1.0,
            30000.0,
            float(
                design.custom_material_density_kg_m3
                if use_custom_material_properties
                else selected_material.density_kg_m3
            ),
            10.0,
            disabled=not use_custom_material_properties,
            key=widget_key("custom_material_density_kg_m3"),
        )
        custom_material_roughness = st.number_input(
            "Material roughness factor",
            0.10,
            1.50,
            float(
                design.custom_material_roughness_factor
                if use_custom_material_properties
                else selected_material.roughness_factor
            ),
            0.01,
            disabled=not use_custom_material_properties,
            key=widget_key("custom_material_roughness_factor"),
        )
        custom_material_durability = st.number_input(
            "Material durability factor",
            0.0,
            1.0,
            float(
                design.custom_material_durability_factor
                if use_custom_material_properties
                else selected_material.durability_factor
            ),
            0.05,
            disabled=not use_custom_material_properties,
            key=widget_key("custom_material_durability_factor"),
        )

        use_estimated_blade_mass = st.checkbox(
            "Estimate blade mass from density",
            value=bool(design.use_estimated_blade_mass),
            help="Use blade planform area × thickness × material density instead of manual mass.",
            key=widget_key("use_estimated_blade_mass"),
        )
        blade_thickness = st.number_input(
            "Blade thickness (m)",
            0.0001,
            0.5000,
            float(design.blade_thickness_m),
            0.0005,
            format="%.4f",
            disabled=not use_estimated_blade_mass,
            key=widget_key("blade_thickness_m"),
        )

    with st.sidebar.expander("Competition generator", expanded=True):
        volts_per_1000_rpm = st.number_input(
            "Generator voltage (V per 1,000 RPM)",
            0.01,
            100.0,
            float(design.generator_volts_per_1000_rpm),
            0.1,
            key=widget_key("generator_volts_per_1000_rpm"),
        )
        internal_resistance = st.number_input(
            "Generator internal resistance (Ω)",
            0.0,
            10000.0,
            float(design.generator_internal_resistance_ohm),
            1.0,
            key=widget_key("generator_internal_resistance_ohm"),
        )
        load_resistance = st.number_input(
            "Competition load (Ω)",
            0.01,
            1000000.0,
            float(design.load_resistance_ohm),
            1.0,
            key=widget_key("load_resistance_ohm"),
        )
        generator_efficiency = st.slider(
            "Generator efficiency (%)",
            1.0,
            100.0,
            float(design.generator_efficiency_percent),
            1.0,
            key=widget_key("generator_efficiency_percent"),
        )
        gear_ratio = st.number_input(
            "Gear ratio (generator ÷ rotor)",
            0.01,
            100.0,
            float(design.gear_ratio),
            0.1,
            key=widget_key("gear_ratio"),
        )
        trial_duration = st.number_input(
            "Trial duration (seconds)",
            0.1,
            86400.0,
            float(design.trial_duration_s),
            1.0,
            key=widget_key("trial_duration_s"),
        )

    with st.sidebar.expander("Advanced calibration", expanded=False):
        st.caption(
            "Teacher/testing controls. Leave these at default values for normal classroom use."
        )
        air_dynamic_viscosity = st.number_input(
            "Air dynamic viscosity (kg/m·s)",
            0.000001,
            0.000100,
            float(design.air_dynamic_viscosity_kg_m_s),
            0.0000001,
            format="%.7f",
            key=widget_key("air_dynamic_viscosity_kg_m_s"),
        )
        practical_cp_limit = st.number_input(
            "Practical Cp limit",
            0.05,
            0.592,
            float(design.practical_cp_limit),
            0.01,
            key=widget_key("practical_cp_limit"),
        )
        airfoil_efficiency_multiplier = st.number_input(
            "Airfoil efficiency multiplier",
            0.10,
            2.00,
            float(design.airfoil_efficiency_multiplier),
            0.05,
            key=widget_key("airfoil_efficiency_multiplier"),
        )
        mechanical_loss = st.slider(
            "Mechanical loss (%)",
            0.0,
            95.0,
            float(design.mechanical_loss_percent),
            1.0,
            key=widget_key("mechanical_loss_percent"),
        )
        startup_torque = st.number_input(
            "Startup/cogging torque (N·m)",
            0.0,
            10000.0,
            float(design.startup_torque_n_m),
            0.01,
            key=widget_key("startup_torque_n_m"),
        )

        st.divider()
        use_hub_area_loss = st.checkbox(
            "Use hub area loss",
            value=bool(design.use_hub_area_loss),
            key=widget_key("use_hub_area_loss"),
        )
        use_airfoil_correction = st.checkbox(
            "Use airfoil correction",
            value=bool(design.use_airfoil_correction),
            key=widget_key("use_airfoil_correction"),
        )
        use_material_roughness = st.checkbox(
            "Use material roughness",
            value=bool(design.use_material_roughness),
            key=widget_key("use_material_roughness"),
        )
        use_generator_power_cap = st.checkbox(
            "Use generator power cap",
            value=bool(design.use_generator_power_cap),
            key=widget_key("use_generator_power_cap"),
        )
        use_generator_load_feedback = st.checkbox(
            "Use generator load feedback",
            value=bool(design.use_generator_load_feedback),
            key=widget_key("use_generator_load_feedback"),
        )
        use_practical_cp_limit = st.checkbox(
            "Use practical Cp limit",
            value=bool(design.use_practical_cp_limit),
            key=widget_key("use_practical_cp_limit"),
        )
        use_reynolds_correction = st.checkbox(
            "Use Reynolds correction",
            value=bool(design.use_reynolds_correction),
            key=widget_key("use_reynolds_correction"),
        )
        use_prandtl_loss = st.checkbox(
            "Use Prandtl tip/root loss",
            value=bool(design.use_prandtl_loss),
            key=widget_key("use_prandtl_loss"),
        )
        use_startup_torque_loss = st.checkbox(
            "Use startup torque loss",
            value=bool(design.use_startup_torque_loss),
            key=widget_key("use_startup_torque_loss"),
        )
        use_bemt_lite = st.checkbox(
            "Use BEMT-lite section model",
            value=bool(design.use_bemt_lite_section_model),
            key=widget_key("use_bemt_lite_section_model"),
        )

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
