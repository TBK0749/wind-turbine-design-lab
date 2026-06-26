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
   position, chord, local twist, station airfoil, and the airfoil's role.
3. **Choose or review airfoils.** Section-table mode can assign different NACA
   airfoils along the blade. Simple root/tip mode uses one global airfoil family.
4. **Check the build preview.** Confirm the chord distribution and pitch-plus-twist
   angles before cutting material.
5. **Review the predicted score.** Focus on competition power in mW, load voltage,
   load current, RPM, Cp, TSR, and stall warnings.
6. **Set blade material and mass.** Use preset materials, or enable custom
   material properties when you know the density, roughness, or durability.
   You may enter mass manually or estimate it from density and blade thickness.
7. **Change one variable at a time.** Adjust one geometry, airfoil, generator, or
   load setting, then compare the result.
8. **Use advanced calibration only when needed.** Teachers or teams can open
   **Advanced calibration** to match measured generator, air, and loss values.
   Leave it unchanged for normal classroom comparisons.
9. **Build and test.** Place the turbine in front of the wind source for the fixed
   trial time and record voltage, current, RPM if available, and mW.
10. **Explain the difference.** Use the glossary to connect design changes to the
   measured output.
"""
    )

    st.info(
        "The simulator is a learning tool. It ranks ideas and explains trade-offs, "
        "but measured competition data is still the final judge.",
        icon="ℹ️",
    )

    st.subheader("Local installation guide")
    st.write(
        "Use these steps when sharing the GitHub repository with students, teammates, "
        "or judges who will run the simulator on their own computers."
    )

    st.markdown(
        """
1. **Install Python 3.12 or newer.**
2. **Install Git** if you want to clone the repository. If not, use GitHub's
   **Download as ZIP** option.
3. **Install uv** for dependency setup.
4. **Get the project from GitHub.**

   Clone with Git:

   ```bash
   git clone https://github.com/TBK0749/wind-turbine-design-lab.git
   cd wind-turbine-design-lab
   ```

   Or use **Download as ZIP**, unzip the folder, and open a terminal in that folder.

5. **Install dependencies.**

   ```bash
   uv sync
   ```

6. **Run the app locally.**

   ```bash
   uv run streamlit run app/main.py
   ```

7. **Open the local URL.**

   ```text
   http://127.0.0.1:8501
   ```

8. **Stop the app** by returning to the terminal and pressing `Ctrl + C`.
"""
    )

    st.subheader("Updating to the latest version")
    st.write(
        "Users who cloned the repository with Git can update the existing "
        "installation without downloading the whole project again."
    )

    st.markdown(
        """
1. Stop the running app with `Ctrl + C`.
2. Open a terminal in the `wind-turbine-design-lab` project folder.
3. Download the latest code, synchronize dependencies, and restart:

   ```bash
   git pull
   uv sync
   uv run streamlit run app/main.py
   ```

`git pull` downloads the latest project files. `uv sync` installs or updates
the dependencies required by that version.

If the project was downloaded as a ZIP file, `git pull` is not available.
Download the latest ZIP and replace the old project folder, or clone with Git
next time for easier updates. Save exported CSV, JSON, and experiment files
outside the project folder before replacing it.
"""
    )

    st.warning(
        "Do not click Deploy for local classroom use. The app runs on your computer, "
        "and no cloud service is required.",
        icon="⚠️",
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
            "Section airfoil",
            "The specific airfoil assigned to one blade station, such as NACA 4418 near "
            "the root for strength or NACA 2412 near the tip for lower drag.",
        ),
        (
            "NACA 4418 / 4415 / 4412",
            "Cambered four-digit NACA airfoils used here for the root and main lift region. "
            "The final two digits describe approximate thickness as a percentage of chord.",
        ),
        (
            "NACA 2412",
            "A thinner cambered NACA airfoil used here near the faster outer blade and tip "
            "sections to reduce drag while keeping useful lift.",
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
            "Material density",
            "Mass per unit volume, measured in kg/m³. Higher-density materials usually make "
            "the blade heavier when the shape and thickness stay the same.",
        ),
        (
            "Estimated blade mass",
            "An optional estimate calculated from blade planform area, blade thickness, and "
            "material density. Manual mass entry remains available when the blade is weighed.",
        ),
        (
            "Surface roughness factor",
            "A simplified factor for how smooth the blade surface is. Lower values reduce "
            "the educational Cp estimate because rougher surfaces tend to add drag.",
        ),
        (
            "Advanced calibration",
            "A teacher/testing panel for manually tuning uncertain constants and disabling "
            "selected model corrections. Custom settings should be recorded with test results.",
        ),
        (
            "Startup/cogging torque",
            "The torque needed to begin turning the generator or rotor. If the rotor cannot "
            "exceed this torque, the model reports zero RPM and zero electrical output.",
        ),
        (
            "Model toggle",
            "A switch that enables or disables one simplified correction, such as airfoil "
            "efficiency, hub-area loss, Reynolds correction, or generator power capping.",
        ),
        (
            "BEMT",
            "Blade Element Momentum Theory. A higher-fidelity method that calculates forces "
            "at many blade stations. This dashboard is not full BEMT yet.",
        ),
    ]

    for term, meaning in terms:
        st.markdown(f"**{term}**  \n{meaning}")
