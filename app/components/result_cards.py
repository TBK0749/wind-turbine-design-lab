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

    second = st.columns(5)
    second[0].metric("Cp", f"{result.cp:.3f}")
    second[1].metric("Tip-speed ratio", f"{result.tip_speed_ratio:.2f}")
    second[2].metric("Efficiency", f"{result.efficiency_percent:.1f}%")
    second[3].metric("Rotor area", f"{result.rotor_area_m2:.2f} m²")
    second[4].metric("Blade mass", f"{result.effective_blade_mass_kg:.3f} kg")

    third = st.columns(3)
    third[0].metric("Model mode", result.model_mode)
    third[1].metric("BEMT sections", f"{result.bemt_section_count}")
    third[2].metric(
        "Mean relative wind",
        f"{result.bemt_mean_relative_wind_speed_m_s:,.2f} m/s",
    )


def render_competition_cards(result: SimulationResult) -> None:
    """Display the estimated electrical score and measurement values."""

    first = st.columns(4)
    first[0].metric("Competition power", f"{result.electrical_power_mw:,.2f} mW")
    first[1].metric("Load voltage", f"{result.load_voltage_v:,.3f} V")
    first[2].metric("Load current", f"{result.load_current_ma:,.3f} mA")
    first[3].metric("Trial energy", f"{result.electrical_energy_mj:,.1f} mJ")

    second = st.columns(3)
    second[0].metric("Generator RPM", f"{result.generator_rpm:,.1f}")
    second[1].metric("Open-circuit voltage", f"{result.open_circuit_voltage_v:,.3f} V")
    second[2].metric(
        "Mechanical → load",
        f"{result.conversion_efficiency_percent:,.2f}%",
    )


def render_airfoil_cards(result: SimulationResult) -> None:
    """Display simplified airfoil lift/drag indicators."""

    first = st.columns(4)
    first[0].metric("Airfoil efficiency", f"{result.airfoil_efficiency_factor:.3f}×")
    first[1].metric("Lift / drag", f"{result.airfoil_lift_drag_ratio:.1f}")
    first[2].metric("Angle of attack", f"{result.airfoil_angle_of_attack_deg:.1f}°")
    first[3].metric("Reynolds number", f"{result.airfoil_reynolds_number:,.0f}")

    second = st.columns(4)
    second[0].metric("Lift coefficient", f"{result.airfoil_lift_coefficient:.3f}")
    second[1].metric("Drag coefficient", f"{result.airfoil_drag_coefficient:.4f}")
    second[2].metric("Stall risk", "Yes" if result.airfoil_stall_risk else "No")
    second[3].metric("Representative airfoil", result.representative_airfoil_name)
