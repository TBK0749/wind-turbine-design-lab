# Physics Model v0.1

## Equations

Rotor swept area, excluding the hub:

```text
A = π(R² - Rh²)
```

Available wind power:

```text
Pwind = 0.5 × ρ × A × V³
```

Mechanical power before optional mechanical losses:

```text
Pmechanical = Cp × Pwind
```

Angular speed and RPM:

```text
λadjusted = λ × (0.75 + 0.25 × airfoil efficiency factor)
ω = λadjustedV / R
RPM = ω × 60 / (2π)
```

Torque:

```text
T = Pmechanical / ω
```

## Competition generator model

Open-circuit generator voltage:

```text
Voc = generator RPM / 1000 × generator volts per 1000 RPM
```

For a resistive load:

```text
I = Voc / (generator internal resistance + load resistance)
Vload = I × load resistance
Pelectrical = Vload × I
```

By default, the electrical result is capped at mechanical power multiplied by
the stated generator efficiency. The app also applies a simple generator-load
feedback factor. If the ideal resistive-load demand is larger than the
available electrical power, the generator operating RPM is reduced by:

```text
load factor = √(available electrical power / ideal resistive-load power)
loaded generator RPM = unloaded generator RPM × load factor
```

This keeps the estimated mW inside the available mechanical-power budget and
shows when an aggressive electrical load would pull the rotor away from its
unloaded speed. Competition power is displayed in milliwatts:

```text
mW = volts × milliamps
energy (mJ) = power (mW) × trial duration (seconds)
```

## Educational approximations

The app accepts either simple root/tip geometry or several measured blade
stations. In sectional mode, each station contains radial position, chord,
local twist, station airfoil, and the airfoil's role. The default section-table
path uses **BEMT-lite**, a simplified blade-section force model. It divides the
blade into radial segments outside the hub radius, estimates local axial and
tangential induction factors with a damped iteration, then calculates relative
wind speed, angle of attack, lift, and drag from the local chord, twist, and
selected airfoil family. Segment torques are summed to estimate mechanical
power and Cp. Values are smoothly bounded, and Cp is kept below practical and
Betz limits.

BEMT-lite is closer to standard blade design thinking than a single whole-blade
Cp estimate because chord, twist, radius, and station airfoil choices can change
the result section by section. It also applies an optional Prandtl-style
root/tip loss factor so the model is less optimistic near the hub and blade
tip. It is still not full QBlade/BEMT. It uses simplified bounded induction
updates rather than full high-induction corrections, measured polar tables,
3D stall delay, wake rotation, turbulence, tower blockage, structural bending,
or manufacturing error.

Simple root/tip mode still uses an educational bounded Cp approximation and an
estimated tip-speed ratio. This mode is useful for quick comparison before
students have measured a full blade table.

The airfoil model is also simplified. In simple root/tip mode, users choose one
classroom airfoil family: flat plate / foam board, cambered plate, symmetric
airfoil, or high-lift airfoil. In section-table mode, each station can choose a
specific airfoil such as NACA 4418, NACA 4415, NACA 4412, NACA 2412, NACA 0012,
Clark Y, Selig S1223, or Flat plate. The simulator maps each named airfoil to
one of the educational airfoil families. In BEMT-lite mode, that family is used
directly at each blade segment. If BEMT-lite is disabled, the simulator falls
back to a representative whole-blade airfoil blend with radial/chord weighting.
Root sections retain a small startup/strength influence, mid-span sections
dominate lift, and tip sections receive extra RPM/drag weight.
The dashboard includes an **Airfoil Help** panel that decodes four-digit NACA
names, for example `4418 = 4% camber, 40% camber position, 18% thickness`.
The simulator estimates a representative angle of attack:

```text
αrepresentative = whole-blade pitch + 0.35 × representative twist
```

It estimates Reynolds number from air density, wind speed, and representative
chord:

```text
Re = ρ × V × chord / μ
```

where μ defaults to 1.81×10⁻⁵ kg/(m·s). Each airfoil family has classroom
constants for lift slope, drag, stall angle, and an efficiency bias. The model
produces estimated lift coefficient, drag coefficient, lift/drag ratio, airfoil
efficiency factor, and stall risk. Supplied small-turbine papers show that low
Reynolds number can reduce lift and increase drag strongly, especially around
`10^4` to `10^5`, so the model applies simplified polar-aware low-Reynolds
corrections when Reynolds correction is enabled. Flat plates receive stronger
penalties, while cambered and high-lift families retain more useful lift at
student-scale Reynolds numbers. The efficiency factor adjusts Cp and slightly
adjusts TSR/RPM so draggy airfoils can reduce the generator mW score.

## Advanced calibration controls

The sidebar includes a collapsed **Advanced calibration** panel. It is meant
for teachers, teams, or judges who want to match measured competition hardware.
Normal classroom users should leave these controls at their defaults.

Manual constants:

- Air dynamic viscosity, used in the Reynolds number estimate.
- Practical Cp limit, used as a configurable cap below the Betz limit.
- Airfoil efficiency multiplier, used to calibrate simplified airfoil behavior.
- Mechanical loss percentage, subtracted after aerodynamic mechanical power.
- Startup/cogging torque, used to stop the rotor when estimated torque is too
  low to start the generator.

Model toggles:

- Hub area loss: when disabled, swept area uses the full rotor disk.
- BEMT-lite section model: when enabled, section-table geometry calculates
  torque by summing local lift/drag forces along the blade. When disabled, the
  simulator falls back to the simpler representative Cp model.
- Prandtl tip/root loss: when enabled, BEMT-lite reduces section torque near the
  blade root and tip using a Prandtl-style loss factor.
- Airfoil correction: when disabled, airfoil efficiency is treated as 1.0.
- Material roughness: when disabled, material roughness is treated as 1.0.
- Generator power cap: when disabled, the resistive-load electrical estimate is
  not capped by available mechanical power.
- Generator load feedback: when disabled, the generator can still be power-capped,
  but the displayed operating RPM is not reduced by heavy electrical loading.
- Practical Cp limit: when disabled, Cp is still capped by the Betz limit.
- Reynolds correction: when disabled, the airfoil model uses a neutral reference
  Reynolds number instead of applying low-Reynolds penalties.
- Startup torque loss: when disabled, startup/cogging torque is ignored.

When any calibration value or toggle differs from the classroom default, the app
shows a custom-calibration warning. Record these settings with every experiment
because results with different toggles are not directly comparable.

## Material and blade mass model

The **Blade physical** panel supports preset materials and custom material
properties. Presets provide density, surface roughness, and durability values
for classroom comparison. The separate **Surface finish** selector models the
extra drag from layer lines or rough hand-cut surfaces. Raw 3D prints apply a
larger drag penalty than sanded, coated, or smooth molded blades.

When **Use custom material properties** is enabled, the user can override:

- Material density in kg/m³.
- Material roughness factor.
- Material durability factor.

By default, the model uses the manually entered **Mass per blade** value. When
**Estimate blade mass from density** is enabled, one blade's mass is estimated
from its top-view area, thickness, and material density:

```text
blade mass ≈ blade planform area × blade thickness × material density
```

For simple root/tip geometry, blade planform area is approximated as:

```text
area ≈ (rotor radius - hub radius) × average(root chord, tip chord)
```

For section-table geometry, the app sums trapezoids between adjacent blade
stations. This is still an educational estimate: it does not include glue,
fasteners, spars, hubs, leading-edge reinforcement, or actual 3D airfoil volume.
If the real blade can be weighed, manual mass is usually more reliable.

Blade mass also affects the timed competition estimate. The simulator estimates
rotor inertia from blade mass and radius:

```text
Irotor ≈ blade count × blade mass × (R² + R×Rhub + Rhub²) / 3
```

It then estimates whether the rotor can reach steady-state speed inside the
configured trial duration:

```text
spin-up factor = 1 - exp(-trial duration / (Irotor × target ω / torque))
```

The spin-up factor reduces effective RPM and mechanical power before the
generator model runs. This makes very heavy 3D-printed blades less competitive
in short trials, even if their steady-state aerodynamic geometry looks good.
The model also adds a small blade-mass startup torque allowance before applying
the generator startup/cogging torque setting.

The supplied 45 cm competition preset uses:

| Position (cm) | Chord (cm) | Twist (deg) | Airfoil | Role |
|---:|---:|---:|---|---|
| 5 | 8.5 | 20 | NACA 4418 | Thick root section for strength and startup torque |
| 13 | 7.2 | 14 | NACA 4415 | Transition section with reduced thickness |
| 21 | 5.6 | 9 | NACA 4412 | Primary lift section |
| 29 | 4.2 | 5 | NACA 4412 | Primary lift support section |
| 37 | 3.0 | 2 | NACA 2412 | Fast outer-blade section with lower drag |
| 45 | 1.8 | 0 | NACA 2412 | Thin tip section to reduce tip-vortex drag |

Whole-blade pitch is added to each local twist value for the fabrication
preview. In BEMT-lite mode, forces are calculated along blade segments. If
BEMT-lite is disabled, the simulator falls back to representative whole-blade
values for simpler classroom comparison. Simple root/tip geometry still uses
the empirical Cp path in the dashboard because a reliable BEMT calculation
needs measured radial chord and twist distribution.

The generator model is a simplified DC equivalent. It now includes a first-order
load feedback factor when electrical demand exceeds available converted
mechanical power, but it still does not recalculate the full aerodynamic power
curve at the new operating TSR. It also does not model nonlinear motor losses,
rectifier losses, battery charging, or detailed startup dynamics. The
aerodynamic model does not yet use external measured airfoil polar files and
does not calculate structural stress, fatigue, control systems, or turbulent
inflow. These require measured calibration data, full BEMT, or higher-fidelity
models.

See `docs/paper_model_notes.md` for the current paper-backed reliability notes.

## Validation status

The simulator is checked against selected values from the supplied small-wind
turbine papers in `docs/model_validation_report.md`. Rows marked `runnable` or
`range_check` can be used for model-error discussion. Rows marked
`reference_only` document useful paper results but are not used for calibration
until matching geometry and generator/load details are available.
