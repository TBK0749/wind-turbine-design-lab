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

Mechanical power:

```text
Pmechanical = Cp × Pwind
```

Angular speed and RPM:

```text
ω = λV / R
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

The electrical result is capped at mechanical power multiplied by the stated
generator efficiency. Competition power is displayed in milliwatts:

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
two-way effect of electrical loading on rotor RPM, startup torque, nonlinear
motor losses, rectifier losses, or battery charging. The aerodynamic model does
not calculate airfoil lift/drag, Reynolds number, induction, structural stress,
fatigue, control systems, or turbulent inflow. These require measured
calibration data, BEMT, or higher-fidelity models.
