"""Replay the bounded low-wind blade search against the original e3343e0 preset."""

import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from windlab.models import BladeSection, SimulationInput  # noqa: E402
from windlab.operating_point import aerodynamic_torque  # noqa: E402
from windlab.section_airfoils import get_section_airfoil  # noqa: E402
from windlab.simulator import simulate  # noqa: E402

# Frozen reference in cm and degrees. The search is independent of the current menu choice.
STATIONS = (
    (6.0, 12.54, 16.0),
    (10.0, 11.55, 12.7),
    (15.7, 10.55, 9.7),
    (21.4, 9.52, 6.9),
    (27.1, 8.43, 4.4),
    (32.9, 7.29, 2.5),
    (38.6, 6.08, 1.2),
    (44.3, 4.77, 0.3),
    (50.0, 3.22, 0.0),
)
WINDS = (2.0, 2.5, 3.0)


def blade(
    inner: str,
    middle: str,
    outer: str,
    chord_scale: float,
    twist_scale: float,
    tip_extra_cm: float = 0.0,
) -> SimulationInput:
    foils = ("NACA 4418", "NACA 4418", "SG6040", inner, middle, middle, outer, outer, outer)
    sections = tuple(
        BladeSection(
            position_m=r / 100,
            chord_m=round(c * chord_scale + tip_extra_cm * (r - 6.0) / 44.0, 2) / 100,
            twist_angle_deg=round(t * twist_scale, 1),
            airfoil_name=name,
            airfoil_role=get_section_airfoil(name).role,
        )
        for (r, c, t), name in zip(STATIONS, foils, strict=True)
    )
    return SimulationInput(
        wind_speed_m_s=2.5,
        rotor_radius_m=0.50,
        hub_radius_m=0.10,
        blade_count=3,
        blade_sections=sections,
        airfoil_type="High-lift airfoil",
    )


def at_wind(design: SimulationInput, wind: float) -> SimulationInput:
    return design.model_copy(update={"wind_speed_m_s": wind})


def main() -> None:
    original = blade("SG6042", "SG6043", "SG6043", 1.0, 1.0)
    reference = [simulate(at_wind(original, w)).electrical_power_mw for w in WINDS]
    static_reference = aerodynamic_torque(at_wind(original, 2.0), 0.0)
    required = simulate(at_wind(original, 2.0)).required_startup_torque_n_m
    finalists = []
    tested = 0
    for args in product(
        ("SG6042", "SG6043", "NACA 4412"),
        ("SG6042", "SG6043", "NACA 4412"),
        ("SG6043", "NACA 4412", "E387"),
        (0.90, 0.95, 1.0, 1.05),
        (0.75, 0.85, 1.0, 1.15, 1.25),
        (0.0, 0.5, 1.0, 1.5),
    ):
        candidate = blade(*args)
        tested += 1
        # Retain at least the original near-rest torque estimate at the weakest wind.
        near_rest = aerodynamic_torque(at_wind(candidate, 2.0), 0.0)
        if near_rest < static_reference:
            continue
        gains = tuple(
            simulate(at_wind(candidate, w)).electrical_power_mw / ref - 1
            for w, ref in zip(WINDS, reference, strict=True)
        )
        finalists.append((near_rest >= required, min(gains), sum(gains) / len(gains), args))
    _, worst_gain, _, settings = max(finalists)
    print(f"{sum(row[0] for row in finalists)} cleared the estimated starting torque threshold")
    winner = blade(*settings)
    print(f"{tested} candidates, {len(finalists)} passed the near-rest torque screen")
    print(f"Winner: {settings}. Smallest gain: {worst_gain:.2%}")
    print("wind | original mW | selected mW | original Cp | selected Cp | selected RPM")
    for w in (2.0, 2.25, 2.5, 2.75, 3.0):
        old, new = (simulate(at_wind(b, w)) for b in (original, winner))
        print(w, old.electrical_power_mw, new.electrical_power_mw, old.cp, new.cp, new.rpm)
    for design in (original, winner):
        point = at_wind(design, 2.0)
        print(
            "Near-rest / required torque at 2 m/s (N m):",
            aerodynamic_torque(point, 0.0),
            simulate(point).required_startup_torque_n_m,
        )
    for s in winner.blade_sections:
        print(
            f"{s.position_m * 100:.1f} {s.chord_m * 100:.2f} "
            f"{s.twist_angle_deg:.1f} {s.airfoil_name}"
        )


if __name__ == "__main__":
    main()
