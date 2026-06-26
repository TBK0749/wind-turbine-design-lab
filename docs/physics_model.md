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
the stated generator efficiency. Competition power is displayed in milliwatts:

```text
mW = volts × milliamps
energy (mJ) = power (mW) × trial duration (seconds)
```

## Educational approximations

Version 0.1 accepts either simple root/tip geometry or several measured blade
stations. In sectional mode, each station contains radial position, chord, and
local twist. The current pre-BEMT model calculates representative chord and
twist values using radial-area weighting, so outer stations contribute more
than inner stations. It then estimates Cp and tip-speed ratio from broad trends
in blade count, chord, pitch, twist, and material roughness. Values are smoothly
bounded, and Cp is kept below practical and Betz limits.

The airfoil model is also simplified. Users choose one classroom airfoil family:
flat plate / foam board, cambered plate, symmetric airfoil, or high-lift
airfoil. The simulator estimates a representative angle of attack:

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
efficiency factor, and stall risk. The efficiency factor adjusts Cp and slightly
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
- Airfoil correction: when disabled, airfoil efficiency is treated as 1.0.
- Material roughness: when disabled, material roughness is treated as 1.0.
- Generator power cap: when disabled, the resistive-load electrical estimate is
  not capped by available mechanical power.
- Practical Cp limit: when disabled, Cp is still capped by the Betz limit.
- Reynolds correction: when disabled, the airfoil model uses a neutral reference
  Reynolds number instead of applying low-Reynolds penalties.
- Startup torque loss: when disabled, startup/cogging torque is ignored.

When any calibration value or toggle differs from the classroom default, the app
shows a custom-calibration warning. Record these settings with every experiment
because results with different toggles are not directly comparable.

The supplied 50 cm competition preset uses:

| Position (cm) | Chord (cm) | Twist (deg) |
|---:|---:|---:|
| 5 | 9.0 | 20 |
| 15 | 7.5 | 14 |
| 25 | 5.5 | 9 |
| 35 | 4.0 | 5 |
| 45 | 2.8 | 2 |
| 50 | 2.0 | 0 |

Whole-blade pitch is added to each local twist value for the fabrication
preview. A later BEMT version will calculate forces independently at each
station instead of reducing the table to representative values.

The generator model is a simplified DC equivalent. It does not yet solve the
full two-way effect of electrical loading on rotor RPM, startup torque,
nonlinear motor losses, rectifier losses, or battery charging. The aerodynamic
model does not use measured airfoil polar files and does not calculate blade
element induction, structural stress, fatigue, control systems, or turbulent
inflow. These require measured calibration data, BEMT, or higher-fidelity
models.
