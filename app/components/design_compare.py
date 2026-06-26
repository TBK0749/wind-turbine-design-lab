"""Design comparison controls for saved dashboard runs."""

import pandas as pd
import streamlit as st

from windlab.models import SimulationInput, SimulationResult

COMPARISON_KEY = "windlab_design_comparisons"


def _comparison_row(
    name: str,
    inputs: SimulationInput,
    result: SimulationResult,
) -> dict[str, float | str]:
    """Build one compact row for design comparison."""

    return {
        "Design": name,
        "mW": result.electrical_power_mw,
        "RPM": result.rpm,
        "Cp": result.cp,
        "Torque (N·m)": result.torque_n_m,
        "Spin-up (%)": result.spinup_factor_percent,
        "Blade mass (kg)": result.effective_blade_mass_kg,
        "Surface finish": inputs.surface_finish,
        "Representative airfoil": result.representative_airfoil_name,
        "Score": result.design_score,
    }


def render_design_comparison(inputs: SimulationInput, result: SimulationResult) -> None:
    """Render save-and-compare UI for alternative blade designs."""

    st.subheader("Design comparison")
    st.caption("Save a few candidate designs, then compare mW, RPM, Cp, mass, and spin-up.")

    saved_rows: list[dict[str, float | str]] = st.session_state.setdefault(COMPARISON_KEY, [])
    name = st.text_input("Design name", value=f"Design {len(saved_rows) + 1}")
    save_col, clear_col = st.columns([1, 1])
    with save_col:
        if st.button("Save current design", width="stretch"):
            saved_rows.append(_comparison_row(name.strip() or "Unnamed design", inputs, result))
            st.session_state[COMPARISON_KEY] = saved_rows
            st.success("Design saved for comparison.")
    with clear_col:
        if st.button("Clear saved designs", width="stretch"):
            st.session_state[COMPARISON_KEY] = []
            saved_rows = []
            st.info("Saved design comparisons cleared.")

    rows = [_comparison_row("Current design", inputs, result), *saved_rows]
    frame = pd.DataFrame(rows)
    st.dataframe(frame, hide_index=True, width="stretch")
