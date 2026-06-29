# Paper-backed model notes

These notes summarize the first reliability pass made from the supplied
small-wind-turbine papers. The goal is not to claim full QBlade accuracy; the
goal is to make the classroom model less optimistic and more useful before
students commit to 3D printing a rotor.

## Papers reviewed

- `COMPARATIVE ANALYSIS OF SMALL-SCALE WIND TURBINE.pdf`
- `Conf4_Experimental Study of Small-Scale Wind Turbine Rotors_EEAE_2020.pdf`
- `DesignandexperimentalvericationofahighefciencysmallwindenergyportableturbineSWEPT.pdf`
- `Paper_JMES2022_accepted_version.pdf`
- `riej.2022.364299.1341.pdf`
- `Small_Wind_Turbine_Blade_Design_and_Optimization.pdf`
- `Small-scale Wind Energy Portable Turbine (SWEPT).pdf`

## Highest-impact findings for this simulator

### 1. Low Reynolds number is a major accuracy risk

Small classroom rotors often run at low Reynolds number because the blade chord
is short and the wind speed is low. The SWEPT work reports a design Reynolds
number around `2 x 10^4`, and notes that the `10^4` to `10^6` range is critical
because laminar separation bubbles can reduce lift and increase drag.

Model change:

- The airfoil model now applies simplified polar-aware low-Reynolds corrections
  instead of one generic penalty for every airfoil family.
- Flat plates remain strongly penalized at low Reynolds number, while cambered
  and high-lift families retain more useful lift before the model applies drag
  and efficiency losses.
- This makes the simulator more conservative than ideal textbook equations but
  less pessimistic for purpose-built low-speed airfoils such as the SWEPT-style
  high-lift rotor.

### 2. Section losses near the root and tip should not be ignored

The SWEPT blade-element code uses local radius, chord, tip-speed ratio, inflow
angle, Reynolds number, induction factors, and Prandtl-style tip/root loss
factors. Full BEMT adds more robust convergence, high-induction handling,
measured polar tables, and validation against test data.

Model change:

- BEMT-lite now includes damped axial/tangential induction estimates and an
  optional Prandtl-style tip/root loss factor for measured section-table blades.
- The result panel reports the mean BEMT loss factor so teachers can see when
  root and tip effects are reducing useful torque.

### 3. Pitch, twist, and TSR are trade-offs, not independent sliders

The experimental rotor papers show that lower pitch can increase speed and
power, but can also raise starting speed. Higher pitch can improve starting
torque but may stall or slow the rotor. This is consistent with the app's
guidance to change one variable at a time and compare Cp, RPM, torque, and mW
together.

Model implication:

- Keep whole-blade pitch and section twist visible in the same workflow.
- Do not optimize only for RPM; competition mW also depends on torque,
  generator loading, and timed spin-up.

### 4. Small turbines can be much less efficient than ideal textbook rotors

The supplied papers show a wide range of Cp depending on rotor size, Reynolds
number, geometry, diffuser use, and test conditions. Some small experimental
systems report Cp near 0.09 to 0.22 without a diffuser at low wind speed, while
the SWEPT rotor reports roughly 0.31 to 0.34 near its design condition. Larger
or more idealized BEM/QBlade examples can report higher Cp, but those values
should not be copied directly to a 45-50 cm classroom rotor.

Model implication:

- Keep the practical Cp cap configurable.
- Treat paper values as calibration ranges, not as a single universal constant.

### 5. Geometry sensitivity matters before printing

The papers consistently support checking chord, twist, blade count, pitch, and
airfoil selection before fabrication. A table-based blade description is more
useful than one root chord, one tip chord, and one generic airfoil.

Model implication:

- The section table remains the recommended workflow for printable blades.
- Airfoil choice is now evaluated by station in BEMT-lite mode.

## What is still not full engineering BEMT

The current model still does not perform:

- full high-induction and convergence corrections used by engineering BEMT;
- external measured airfoil polar lookup tables;
- post-stall or Viterna extrapolation;
- 3D stall delay;
- wake rotation;
- turbulence or tunnel blockage correction;
- two-way generator load feedback on rotor RPM;
- structural deflection or print-quality error modeling.

These are candidates for future Phase 2/Phase 3 work after measured classroom
data is available.
