"""Sidebar controls for simulation inputs."""

import pandas as pd
import streamlit as st

from app.components.design_workspace import active_design, widget_key
from windlab.airfoils import AIRFOIL_LIBRARY
from windlab.blade_geometry import competition_50cm_sections
from windlab.design_state import blank_blade_sections
from windlab.materials import MATERIALS, SURFACE_FINISHES
from windlab.models import BladeSection, SimulationInput
from windlab.section_airfoils import get_section_airfoil, section_airfoil_options

SECTION_TABLE_COLUMNS = [
    "Section",
    "Position (cm)",
    "Chord (cm)",
    "Twist (deg)",
    "Airfoil",
    "Airfoil role / purpose",
]


def _section_label(index: int, section_count: int) -> str:
    """Return the display label for a blade section row."""

    if index == 0:
        return "1 (Root)"
    if index == section_count - 1:
        return f"{section_count} (Tip)"
    return str(index + 1)


def _section_frame_from_sections(sections: tuple[BladeSection, ...]) -> pd.DataFrame:
    """Build an editable centimetre-based table for the supplied blade."""

    return pd.DataFrame(
        {
            "Section": [_section_label(index, len(sections)) for index, _ in enumerate(sections)],
            "Position (cm)": [section.position_m * 100.0 for section in sections],
            "Chord (cm)": [section.chord_m * 100.0 for section in sections],
            "Twist (deg)": [section.twist_angle_deg for section in sections],
            "Airfoil": [section.airfoil_name for section in sections],
            "Airfoil role / purpose": [section.airfoil_role for section in sections],
        }
    )


def _normalise_airfoil_name(value: object) -> str:
    """Return a valid student-facing airfoil name."""

    if pd.isna(value) or not str(value).strip():
        return "NACA 4412"
    airfoil_name = str(value).strip()
    if airfoil_name not in section_airfoil_options():
        return "NACA 4412"
    return airfoil_name


def _role_for_airfoil(airfoil_name: str, role: object = "") -> str:
    """Return an editable role, falling back to the catalog explanation."""

    if not pd.isna(role) and str(role).strip():
        return str(role)
    return get_section_airfoil(airfoil_name).role


def _section_frame_with_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a table that has all expected section-editor columns."""

    prepared = frame.copy()
    for column in SECTION_TABLE_COLUMNS:
        if column not in prepared:
            prepared[column] = None
    return prepared[SECTION_TABLE_COLUMNS]


def _relabel_section_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Sort complete positioned rows by radius and refresh display labels."""

    prepared = _section_frame_with_columns(frame)
    positions = pd.to_numeric(prepared["Position (cm)"], errors="coerce")
    positioned = prepared[positions.notna()].copy()
    unpositioned = prepared[positions.isna()].copy()

    if not positioned.empty:
        positioned["Position (cm)"] = pd.to_numeric(positioned["Position (cm)"], errors="coerce")
        positioned = positioned.sort_values("Position (cm)", kind="mergesort")

    relabelled = pd.concat([positioned, unpositioned], ignore_index=True)
    for index in range(len(relabelled)):
        relabelled.loc[index, "Section"] = _section_label(index, len(relabelled))
    return relabelled


def _complete_section_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Return rows that contain enough numeric data to interpolate from."""

    prepared = _section_frame_with_columns(frame)
    prepared["Position (cm)"] = pd.to_numeric(prepared["Position (cm)"], errors="coerce")
    prepared["Chord (cm)"] = pd.to_numeric(prepared["Chord (cm)"], errors="coerce")
    prepared["Twist (deg)"] = pd.to_numeric(prepared["Twist (deg)"], errors="coerce")
    prepared["Airfoil"] = prepared["Airfoil"].map(_normalise_airfoil_name)
    prepared["Airfoil role / purpose"] = [
        _role_for_airfoil(str(airfoil), role)
        for airfoil, role in zip(
            prepared["Airfoil"],
            prepared["Airfoil role / purpose"],
            strict=True,
        )
    ]
    complete = prepared.dropna(subset=["Position (cm)", "Chord (cm)", "Twist (deg)"])
    return complete.sort_values("Position (cm)", kind="mergesort").reset_index(drop=True)


def _root_refinement_positions(first_position_cm: float, count: int) -> tuple[float, ...]:
    """Return evenly spaced stations before the first existing blade station."""

    if count <= 0:
        return ()
    step = first_position_cm / float(count + 1)
    return tuple(round(max(step * index, 0.1), 3) for index in range(1, count + 1))


def _interpolated_section_row(frame: pd.DataFrame, position_cm: float) -> dict[str, object] | None:
    """Build one inserted row using neighbouring section values."""

    complete = _complete_section_rows(frame)
    if complete.empty:
        return None

    position_cm = max(float(position_cm), 0.1)
    if position_cm <= float(complete.iloc[0]["Position (cm)"]):
        source = complete.iloc[0]
        return {
            "Section": "",
            "Position (cm)": position_cm,
            "Chord (cm)": float(source["Chord (cm)"]),
            "Twist (deg)": float(source["Twist (deg)"]),
            "Airfoil": str(source["Airfoil"]),
            "Airfoil role / purpose": str(source["Airfoil role / purpose"]),
        }

    if position_cm >= float(complete.iloc[-1]["Position (cm)"]):
        source = complete.iloc[-1]
        return {
            "Section": "",
            "Position (cm)": position_cm,
            "Chord (cm)": float(source["Chord (cm)"]),
            "Twist (deg)": float(source["Twist (deg)"]),
            "Airfoil": str(source["Airfoil"]),
            "Airfoil role / purpose": str(source["Airfoil role / purpose"]),
        }

    for index in range(len(complete) - 1):
        left = complete.iloc[index]
        right = complete.iloc[index + 1]
        left_position = float(left["Position (cm)"])
        right_position = float(right["Position (cm)"])
        if left_position <= position_cm <= right_position:
            span = right_position - left_position
            ratio = 0.0 if span == 0 else (position_cm - left_position) / span
            nearest = left if ratio <= 0.5 else right
            return {
                "Section": "",
                "Position (cm)": position_cm,
                "Chord (cm)": round(
                    float(left["Chord (cm)"])
                    + (float(right["Chord (cm)"]) - float(left["Chord (cm)"])) * ratio,
                    3,
                ),
                "Twist (deg)": round(
                    float(left["Twist (deg)"])
                    + (float(right["Twist (deg)"]) - float(left["Twist (deg)"])) * ratio,
                    3,
                ),
                "Airfoil": str(nearest["Airfoil"]),
                "Airfoil role / purpose": str(nearest["Airfoil role / purpose"]),
            }

    return None


def _insert_interpolated_section_rows(
    frame: pd.DataFrame,
    positions_cm: tuple[float, ...],
) -> pd.DataFrame:
    """Insert one or more section rows and return a sorted, relabelled table."""

    prepared = _section_frame_with_columns(frame)
    existing_positions = {
        round(float(position), 6)
        for position in pd.to_numeric(prepared["Position (cm)"], errors="coerce").dropna()
    }
    new_rows = []
    for position_cm in positions_cm:
        safe_position = max(float(position_cm), 0.1)
        if round(safe_position, 6) in existing_positions:
            continue
        row = _interpolated_section_row(prepared, safe_position)
        if row is None:
            continue
        new_rows.append(row)
        existing_positions.add(round(safe_position, 6))

    if not new_rows:
        return _relabel_section_frame(prepared)
    updated = pd.concat([prepared, pd.DataFrame(new_rows)], ignore_index=True)
    return _relabel_section_frame(updated)


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
        )
        if any(pd.isna(value) for value in values):
            continue
        airfoil_name = _normalise_airfoil_name(row.get("Airfoil"))
        role = row.get("Airfoil role / purpose")
        airfoil_role = _role_for_airfoil(airfoil_name, role)
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


def _resolve_rotor_radius_for_sections(
    rotor_radius_m: float,
    sections: tuple[BladeSection, ...],
) -> tuple[float, str | None]:
    """Return a rotor radius that can contain the section table."""

    if not sections:
        return rotor_radius_m, None

    final_position_m = sections[-1].position_m
    if final_position_m <= rotor_radius_m:
        return rotor_radius_m, None

    warning = (
        f"Final blade section is {final_position_m * 100.0:.1f} cm, but the rotor radius "
        f"is {rotor_radius_m * 100.0:.1f} cm. The simulator is using "
        f"{final_position_m * 100.0:.1f} cm for this run so the blade table remains "
        "physically valid. To use the smaller blade length, change the final Position "
        "in the blade geometry table to match the rotor radius."
    )
    return final_position_m, warning


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
        section_frame_state_key = widget_key("blade_section_frame")
        section_editor_refresh_key = widget_key("blade_section_editor_refresh")
        st.session_state.setdefault(section_editor_refresh_key, 0)
        if section_frame_state_key not in st.session_state:
            st.session_state[section_frame_state_key] = _section_frame_from_sections(base_sections)

        section_frame_source = _section_frame_with_columns(st.session_state[section_frame_state_key])
        complete_rows = _complete_section_rows(section_frame_source)
        first_position_cm = (
            float(complete_rows.iloc[0]["Position (cm)"]) if not complete_rows.empty else 6.0
        )

        with st.expander("Insert / sort section rows", expanded=False):
            st.caption(
                "Use these tools when you need rows before the current root station. "
                "The table + button can only append rows at the bottom; this tool inserts "
                "by Position (cm), then sorts and relabels the sections automatically."
            )
            st.caption(
                "Use positions above 0 cm. A true 0 cm station is the rotor axis, which is "
                "not a stable aerodynamic station for the simulator."
            )
            root_col, insert_col, sort_col, clear_col = st.columns(4)
            with root_col:
                root_refinement_count = st.number_input(
                    "Rows before first station",
                    min_value=1,
                    max_value=12,
                    value=3,
                    step=1,
                    key=widget_key("root_refinement_count"),
                    help="Example: first station 6 cm and 3 rows creates 1.5, 3.0, 4.5 cm.",
                )
                if st.button("Add root refinement rows", width="stretch"):
                    positions = _root_refinement_positions(
                        first_position_cm,
                        int(root_refinement_count),
                    )
                    st.session_state[section_frame_state_key] = _insert_interpolated_section_rows(
                        section_frame_source,
                        positions,
                    )
                    st.session_state[section_editor_refresh_key] += 1
                    st.rerun()
            with insert_col:
                insert_position_cm = st.number_input(
                    "Insert at position (cm)",
                    min_value=0.1,
                    max_value=10000.0,
                    value=round(max(first_position_cm / 2.0, 0.1), 1),
                    step=0.5,
                    key=widget_key("insert_section_position_cm"),
                )
                if st.button("Insert section", width="stretch"):
                    st.session_state[section_frame_state_key] = _insert_interpolated_section_rows(
                        section_frame_source,
                        (float(insert_position_cm),),
                    )
                    st.session_state[section_editor_refresh_key] += 1
                    st.rerun()
            with sort_col:
                st.write("")
                st.write("")
                if st.button("Sort rows by position", width="stretch"):
                    st.session_state[section_frame_state_key] = _relabel_section_frame(
                        section_frame_source
                    )
                    st.session_state[section_editor_refresh_key] += 1
                    st.rerun()
            with clear_col:
                st.write("")
                st.write("")
                if st.button(
                    "Clear section table",
                    width="stretch",
                    help="Replace the table with editable root and tip rows.",
                ):
                    st.session_state[section_frame_state_key] = _section_frame_from_sections(
                        blank_blade_sections(float(rotor_radius))
                    )
                    st.session_state[section_editor_refresh_key] += 1
                    st.rerun()

        section_frame = st.data_editor(
            _section_frame_with_columns(st.session_state[section_frame_state_key]),
            key=(
                f"{widget_key('blade_section_editor')}_"
                f"{st.session_state[section_editor_refresh_key]}"
            ),
            hide_index=True,
            num_rows="dynamic",
            width="stretch",
            column_config={
                "Section": st.column_config.TextColumn("Section", disabled=True),
                "Position (cm)": st.column_config.NumberColumn(
                    "Position (cm)",
                    min_value=0.1,
                    step=1.0,
                    format="%.1f",
                    help="Use 0.1 cm or greater; 0 cm is the rotor axis.",
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
                    required=False,
                ),
                "Airfoil role / purpose": st.column_config.TextColumn(
                    "Airfoil role / purpose",
                    help="Why this airfoil is used at this blade station.",
                    width="large",
                ),
            },
        )
        st.session_state[section_frame_state_key] = _section_frame_with_columns(section_frame)
        blade_sections = _sections_from_frame(section_frame)
        airfoil_sequence = " → ".join(section.airfoil_name for section in blade_sections)
        st.markdown(
            f"**Airfoil preset:** {airfoil_sequence}. "
            "Use thicker root sections for strength and thinner tip sections to reduce drag."
        )
        if blade_sections:
            section_count_inside_hub = sum(
                1 for section in blade_sections if section.position_m <= float(hub_radius)
            )
            if section_count_inside_hub:
                st.caption(
                    f"{section_count_inside_hub} section row(s) are inside the current "
                    f"{float(hub_radius) * 100.0:.1f} cm hub radius. That can be useful for "
                    "CAD root shaping, but wind-power contribution is mainly from stations "
                    "outside the hub."
                )
        root_chord = blade_sections[0].chord_m if blade_sections else 0.09
        tip_chord = blade_sections[-1].chord_m if blade_sections else 0.02
        twist = blade_sections[0].twist_angle_deg if blade_sections else 20.0
        rotor_radius, radius_warning = _resolve_rotor_radius_for_sections(
            float(rotor_radius),
            blade_sections,
        )
        if radius_warning:
            st.warning(radius_warning, icon="⚠️")
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
