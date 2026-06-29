"""Phase 2 scaffold for measured experiment logging and calibration."""

import pandas as pd
import streamlit as st

from windlab.calibration import (
    ExperimentMeasurement,
    average_correction_factors,
    calibration_markdown_report,
    measurement_row,
    measurements_as_csv,
    measurements_as_validation_benchmark_csv,
)
from windlab.models import SimulationInput, SimulationResult

CALIBRATION_LOG_KEY = "windlab_calibration_measurements"


def render_calibration_lab(inputs: SimulationInput, result: SimulationResult) -> None:
    """Render measured-data scaffold for Phase 2 calibration work."""

    st.subheader("Phase 2 calibration scaffold")
    st.write(
        "Use this page after a real prototype test. Record measured RPM and mW, compare "
        "them with the simulator prediction, and export the calibration worksheet."
    )
    st.info(
        "This scaffold does not automatically change the physics model yet. It prepares "
        "measured data so future calibration is based on real tests, not guesses.",
        icon="ℹ️",
    )

    measurements: list[ExperimentMeasurement] = st.session_state.setdefault(
        CALIBRATION_LOG_KEY,
        [],
    )

    st.markdown("### Current prediction")
    cols = st.columns(4)
    cols[0].metric("Predicted RPM", f"{result.rpm:,.2f}")
    cols[1].metric("Predicted mW", f"{result.electrical_power_mw:,.4f}")
    cols[2].metric("Wind speed", f"{inputs.wind_speed_m_s:,.2f} m/s")
    cols[3].metric("Model mode", result.model_mode)

    st.markdown("### Add measured trial")
    left, right = st.columns(2)
    with left:
        design_name = st.text_input("Measured design name", value="Prototype 1")
        measured_wind_speed = st.number_input(
            "Measured wind speed (m/s)",
            0.0,
            60.0,
            float(inputs.wind_speed_m_s),
            0.1,
        )
        measured_rpm = st.number_input("Measured RPM", 0.0, 100000.0, 0.0, 10.0)
    with right:
        measured_power = st.number_input("Measured competition power (mW)", 0.0, 1e9, 0.0, 0.1)
        notes = st.text_area("Measurement notes", value="")

    add_col, clear_col = st.columns(2)
    with add_col:
        if st.button("Add measured trial", width="stretch"):
            measurements.append(
                ExperimentMeasurement(
                    design_name=design_name.strip() or "Unnamed prototype",
                    wind_speed_m_s=measured_wind_speed,
                    predicted_rpm=result.rpm,
                    measured_rpm=measured_rpm,
                    predicted_power_mw=result.electrical_power_mw,
                    measured_power_mw=measured_power,
                    notes=notes.strip(),
                )
            )
            st.session_state[CALIBRATION_LOG_KEY] = measurements
            st.success("Measured trial added.")
    with clear_col:
        if st.button("Clear calibration log", width="stretch"):
            st.session_state[CALIBRATION_LOG_KEY] = []
            measurements = []
            st.info("Calibration log cleared.")

    st.markdown("### Calibration log")
    if measurements:
        rows = [measurement_row(measurement) for measurement in measurements]
        frame = pd.DataFrame(rows)
        st.dataframe(frame, hide_index=True, width="stretch")
        rpm_factor, power_factor = average_correction_factors(measurements)
        factor_cols = st.columns(2)
        factor_cols[0].metric("Average RPM correction factor", f"{rpm_factor:.4f}")
        factor_cols[1].metric("Average mW correction factor", f"{power_factor:.4f}")
    else:
        st.caption("No measured trials yet. Add a prototype test after 3D printing.")

    export_left, export_middle, export_right = st.columns(3)
    with export_left:
        st.download_button(
            "Download calibration CSV",
            measurements_as_csv(measurements),
            file_name="wind_turbine_calibration_log.csv",
            mime="text/csv",
            width="stretch",
        )
    with export_middle:
        st.download_button(
            "Download validation benchmark CSV",
            measurements_as_validation_benchmark_csv(measurements, inputs),
            file_name="classroom_measured_benchmarks.csv",
            mime="text/csv",
            width="stretch",
        )
    with export_right:
        st.download_button(
            "Download calibration worksheet",
            calibration_markdown_report(measurements),
            file_name="wind_turbine_calibration_worksheet.md",
            mime="text/markdown",
            width="stretch",
        )
