"""English learning guide and glossary for the wind turbine dashboard."""

import streamlit as st


def render_quick_start_guide() -> None:
    """Render a student-facing guide for the competition workflow."""

    st.subheader("Quick start guide")
    st.write(
        "Use this simulator to plan one blade design, predict its competition output, "
        "build the blade, then compare the measured result with the prediction."
    )

    st.markdown(
        """
1. **Set the wind and trial conditions.** Match the fan or wind tunnel speed,
   air density if known, and the fixed trial duration.
2. **Enter the blade geometry.** Use the section table for measured blade stations:
   position, chord, and local twist.
3. **Choose the airfoil family.** Select the option that best matches the blade
   cross-section you will actually build.
4. **Check the build preview.** Confirm the chord distribution and pitch-plus-twist
   angles before cutting material.
5. **Review the predicted score.** Focus on competition power in mW, load voltage,
   load current, RPM, Cp, TSR, and stall warnings.
6. **Change one variable at a time.** Adjust one geometry, airfoil, generator, or
   load setting, then compare the result.
7. **Build and test.** Place the turbine in front of the wind source for the fixed
   trial time and record voltage, current, RPM if available, and mW.
8. **Explain the difference.** Use the glossary to connect design changes to the
   measured output.
"""
    )

    st.info(
        "The simulator is a learning tool. It ranks ideas and explains trade-offs, "
        "but measured competition data is still the final judge.",
        icon="ℹ️",
    )


def render_key_terms_glossary() -> None:
    """Render concise definitions for the main engineering terms."""

    st.subheader("Key terms glossary")

    terms = [
        (
            "Competition power (mW)",
            "The electrical score measured at the load. In this dashboard, "
            "mW = load voltage × load current in milliamps.",
        ),
        (
            "Power coefficient (Cp)",
            "The fraction of available wind power converted into mechanical rotor power. "
            "Higher Cp means the rotor extracts wind energy more effectively.",
        ),
        (
            "Tip-speed ratio (TSR)",
            "Blade tip speed divided by wind speed. Low TSR usually means a slow, torque-heavy "
            "rotor; high TSR usually means a faster rotor.",
        ),
        (
            "Airfoil",
            "The cross-section shape of the blade. Flat plates are easy to build; cambered "
            "or high-lift shapes can produce more lift but may be harder to fabricate.",
        ),
        (
            "Chord",
            "The blade width at a measured station, from leading edge to trailing edge.",
        ),
        (
            "Twist",
            "The change in local blade angle from root to tip. Twist helps different blade "
            "stations meet the wind at useful angles.",
        ),
        (
            "Pitch",
            "The whole-blade mounting angle. Increasing pitch can increase torque, but too "
            "much pitch can add drag or cause stall.",
        ),
        (
            "Angle of attack",
            "The angle between the incoming airflow and the blade section. Moderate angle "
            "creates lift; excessive angle can stall.",
        ),
        (
            "Lift / drag",
            "A quick quality indicator for an airfoil. More lift with less drag usually helps "
            "the rotor spin and produce more electrical output.",
        ),
        (
            "Reynolds number",
            "A scale number based on wind speed, chord, and air properties. Small classroom "
            "turbines often run at low Reynolds numbers, where drag can matter a lot.",
        ),
        (
            "Stall",
            "A flow separation condition where lift drops and drag rises. Stall often happens "
            "when pitch or twist makes the angle of attack too large.",
        ),
        (
            "Torque",
            "Turning force at the shaft. More torque can help overcome generator resistance, "
            "but power also depends on RPM.",
        ),
        (
            "RPM",
            "Revolutions per minute. Generator voltage normally increases with generator RPM.",
        ),
        (
            "Load resistance",
            "The electrical resistance connected to the generator during the test. It affects "
            "voltage, current, and measured mW.",
        ),
        (
            "BEMT",
            "Blade Element Momentum Theory. A higher-fidelity method that calculates forces "
            "at many blade stations. This dashboard is not full BEMT yet.",
        ),
    ]

    for term, meaning in terms:
        st.markdown(f"**{term}**  \n{meaning}")
