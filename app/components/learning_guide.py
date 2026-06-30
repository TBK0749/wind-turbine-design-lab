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
3. **Use a starter preset if helpful.** The Design workspace includes five
   3-blade presets for a maximum 1 m rotor diameter. Treat them as starting
   points, not guaranteed winners.
4. **Choose or review airfoils.** Section-table mode can assign different NACA
   airfoils along the blade. The model blends root, mid-span, and tip effects.
   Simple root/tip mode uses one global airfoil family.
5. **Check the build preview.** Confirm the chord distribution and pitch-plus-twist
   angles before cutting material.
6. **Review the predicted score.** Focus on competition power in mW, load voltage,
   load current, RPM, Cp, TSR, and stall warnings.
7. **Set blade material and mass.** Use preset materials, or enable custom
   material properties when you know the density, roughness, or durability.
   You may enter mass manually or estimate it from density and blade thickness.
8. **Change one variable at a time.** Adjust one geometry, airfoil, generator, or
   load setting, then compare the result.
9. **Use advanced calibration only when needed.** Teachers or teams can open
   **Advanced calibration** to match measured generator, air, and loss values.
   Leave it unchanged for normal classroom comparisons.
10. **Export CAD reference files if needed.** Use **Download Onshape package**
   when you want CSV and DXF reference files for rebuilding the blade in CAD.
11. **Build and test.** Place the turbine in front of the wind source for the fixed
   trial time and record voltage, current, RPM if available, and mW.
12. **Log measured results.** Use the **Calibration** tab to enter measured RPM
   and mW after a real prototype test. Export the worksheet for your notebook.
13. **Explain the difference.** Use the glossary to connect design changes to the
   measured output.
"""
    )

    st.info(
        "The simulator is a learning tool. It ranks ideas and explains trade-offs, "
        "but measured competition data is still the final judge.",
        icon="ℹ️",
    )

    st.subheader("Local design workspace")
    st.write(
        "The Design workspace keeps student work on the local computer. It does "
        "not require an account, cloud database, or paid service."
    )
    st.markdown(
        """
- **Autosave:** the current design is saved to `user_data/windlab.sqlite`.
- **Refresh recovery:** after refreshing the browser, the latest autosaved design
  should return automatically.
- **Undo/Redo:** use the app buttons for simulator changes. Browser Command+Z
  does not reliably undo Streamlit widget changes.
- **Named saves:** save several candidate designs and load them later on the
  same computer.
- **Blade presets:** load six 3-blade starter presets for the 1 m maximum
  rotor-diameter rule, then edit the table for your own experiment.
"""
    )

    st.subheader("Onshape package export")
    st.write(
        "Use this when students want to rebuild a chosen blade in Onshape or "
        "another CAD tool instead of copying every table value by hand."
    )
    st.markdown(
        """
Click **Download Onshape package** in the export panel. The ZIP contains:

- `blade_geometry.csv` for station position, chord, twist, airfoil, and role;
- `airfoil_sections.csv` for airfoil metadata and Reynolds-number guidance;
- `blade_planform.dxf` for the top-view blade outline;
- `section_profiles.dxf` for scaled airfoil profiles;
- `design_metadata.json` for simulator settings;
- `onshape_build_guide.md` for the CAD rebuild workflow.

This package is **not a print-ready STL**. Students still need to create the 3D
loft, hub connector, wall thickness, reinforcement, and final print settings in CAD.
"""
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
            "the root for strength or NACA 2412 near the tip for lower drag. In section "
            "table mode, all station airfoils contribute to the estimate.",
        ),
        (
            "Camber",
            "How curved the airfoil is. More camber usually helps create lift at low speed, "
            "but too much angle can still stall.",
        ),
        (
            "Thickness",
            "The airfoil thickness as a percentage of chord. A 4418 airfoil is about 18% "
            "thick, while a 4412 airfoil is about 12% thick.",
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
            "SG6040 / SG6042 / SG6043",
            "Small-wind airfoils from the Selig/Giguere SG series. They are useful "
            "comparison choices for low-Reynolds classroom rotors, especially around "
            "the root and middle lift region.",
        ),
        (
            "S1223",
            "A very high-lift low-Reynolds airfoil. It can help startup experiments, "
            "but high lift also means stall and drag must be watched carefully.",
        ),
        (
            "E387",
            "A classic low-Reynolds reference airfoil. It is useful for comparing smoother, "
            "lower-drag sections but may need better fabrication quality than a flat plate.",
        ),
        (
            "NREL S822 / S823",
            "Thick wind-turbine airfoils designed for larger rotors. In this app they are "
            "educational comparison options and may be outside the best Reynolds range for "
            "small 3D-printed classroom blades.",
        ),
        (
            "Airfoil confidence",
            "A label showing how much source context the simulator has. It is not a promise "
            "that the predicted mW will match a real tunnel test.",
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
            "material density. Heavier blades increase rotor inertia and may reduce RPM "
            "during a timed run. Manual mass entry remains available when the blade is weighed.",
        ),
        (
            "Spin-up factor",
            "An estimate of how close the rotor gets to its steady-state speed during the "
            "competition time. Heavy blades and short runs lower this value.",
        ),
        (
            "Surface finish",
            "The smoothness of the blade surface. Raw 3D prints usually add drag from layer "
            "lines; sanding or coating can improve the simulated mW result.",
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
            "Calibration scaffold",
            "A Phase 2 worksheet for comparing predicted RPM/mW with measured prototype "
            "results. It calculates error and correction factors, but does not automatically "
            "change the physics model.",
        ),
        (
            "Correction factor",
            "Measured value divided by predicted value. If several tests give similar "
            "factors, a teacher or team can use them later to tune the model.",
        ),
        (
            "Startup/cogging torque",
            "The torque needed to begin turning the generator or rotor. If the rotor cannot "
            "exceed this torque, the model reports zero RPM and zero electrical output.",
        ),
        (
            "Model toggle",
            "A switch that enables or disables one simplified correction, such as airfoil "
            "efficiency, hub-area loss, Reynolds correction, generator power capping, or "
            "generator load feedback.",
        ),
        (
            "Local design workspace",
            "The app area for Undo/Redo, autosave, named saves, loading presets, and "
            "recovering the latest design after refresh. It stores data locally in "
            "`user_data/windlab.sqlite`.",
        ),
        (
            "Blade preset",
            "A prebuilt blade geometry table. Presets are useful starting points for "
            "comparison, but they are not guaranteed to win before real testing.",
        ),
        (
            "Onshape package",
            "A ZIP export containing CSV, DXF, JSON, and a Markdown guide for rebuilding "
            "the selected blade in CAD. It is not a finished STL.",
        ),
        (
            "DXF",
            "A 2D drawing exchange file used by CAD tools. This app exports DXF outlines "
            "and airfoil profiles as reference sketches.",
        ),
        (
            "STL",
            "A triangle mesh file often sent to slicer software for 3D printing. The app "
            "does not generate final STL files yet.",
        ),
        (
            "BEMT-lite",
            "A simplified Blade Element Momentum Theory style model. It calculates lift "
            "and drag at blade sections using local chord, twist, airfoil, and relative "
            "wind speed with bounded induction-factor estimates, but it is still much "
            "simpler than QBlade.",
        ),
        (
            "Full BEMT",
            "A higher-fidelity Blade Element Momentum Theory method that iteratively solves "
            "how the rotor slows and twists the airflow. QBlade uses much more advanced "
            "aerodynamic modeling than this classroom dashboard.",
        ),
    ]

    for term, meaning in terms:
        st.markdown(f"**{term}**  \n{meaning}")
