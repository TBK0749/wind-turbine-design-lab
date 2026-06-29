# Model Validation Report

This report compares the current educational simulator with benchmark values extracted from the supplied small-wind-turbine papers.

The report separates strict comparisons from reference-only paper values. Reference-only rows are not used for calibration because geometry, load, or generator details are incomplete.

## Runnable and range-check comparisons

| Case | Paper | Role | Confidence | Metric | Target | Predicted | Status | Error |
|---|---|---|---|---|---:|---:|---|---:|
| `swept_final_cp_4ms` | Small-scale Wind Energy Portable Turbine (SWEPT).pdf | range_check | medium | cp | 0.3100 to 0.3400 dimensionless | 0.1713 | below_range | -44.7% |
| `conf4_naca4412_power_10ms_range` | Conf4_Experimental Study of Small-Scale Wind Turbine Rotors_EEAE_2020.pdf | range_check | low | mechanical_power_w | 22.00 to 48.00 W | 38.97 | within_range | 0.0% |
| `optimization_large_rotor_cp_5_5ms` | Small_Wind_Turbine_Blade_Design_and_Optimization.pdf | range_check | medium | cp | 0.4200 to 0.4700 dimensionless | 0.2796 | below_range | -33.4% |
| `classroom_competition_baseline_3_6ms` | Internal classroom target | runnable | high | cp | - | 0.0043 | recorded | - |
| `classroom_competition_baseline_3_6ms` | Internal classroom target | runnable | high | rpm | - | 126.5 | recorded | - |
| `classroom_competition_baseline_3_6ms` | Internal classroom target | runnable | high | mechanical_power_w | - | 0.0740 | recorded | - |
| `classroom_competition_baseline_3_6ms` | Internal classroom target | runnable | high | electrical_power_mw | - | 0.2502 | recorded | - |

## Reference-only paper results

| Case | Paper | Role | Confidence | Paper value | Why reference-only |
|---|---|---|---|---|---|
| `swept_electrical_power_reference` | Small-scale Wind Energy Portable Turbine (SWEPT).pdf | reference_only | medium | electrical_power_w: 1.0000 to 1.0000 W at 4.0 m/s; electrical_power_w: 2.2000 to 2.2000 W at 5.5 m/s | Electrical output depends on generator/load details that are not equivalent to the classroom generator model. |
| `riej_no_diffuser_cp_reference` | riej.2022.364299.1341.pdf | reference_only | medium | cp: 0.0900 to 0.2200 dimensionless | Useful low-speed Cp range, but diffuser/no-diffuser geometry and test setup are not equivalent to the classroom rotor. |

## Calibration interpretation

- If the model is consistently below measured Cp for reliable runnable cases, inspect low-Reynolds penalties and practical Cp limits.
- If the model is consistently above measured Cp, inspect Prandtl loss, surface finish, startup torque, and generator loading assumptions.
- Do not calibrate against reference-only rows until the missing geometry and load details are added.

## Next validation data to collect

- Actual classroom rotor geometry after slicing or printing.
- Wind tunnel speed at the rotor plane.
- Measured RPM, voltage, current, load resistance, and trial duration.
- Blade mass, surface finish, and generator internal resistance.
