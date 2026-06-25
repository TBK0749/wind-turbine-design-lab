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

## Educational approximations

Version 0.1 estimates Cp and tip-speed ratio from broad trends involving blade
count, chord ratio, pitch, twist, and material roughness. Values are smoothly
bounded, and Cp is kept below practical and Betz limits.

The model does not calculate airfoil lift/drag, Reynolds number, induction,
structural stress, fatigue, generator losses, startup torque, control systems,
or turbulent inflow. These require later validation and BEMT or higher-fidelity
models.
