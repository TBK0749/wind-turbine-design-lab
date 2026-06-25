"""Student-facing design score and recommendations."""

from windlab.models import SimulationInput


def design_score(
    *,
    inputs: SimulationInput,
    cp: float,
    tip_speed_ratio: float,
    material_durability: float,
) -> float:
    """Return a normalized 0-100 classroom comparison score."""

    cp_score = min(cp / 0.45, 1.0)
    tsr_score = max(0.0, 1.0 - abs(tip_speed_ratio - 7.0) / 7.0)
    mass_per_radius = inputs.blade_mass_kg / inputs.rotor_radius_m
    mass_score = 1.0 / (1.0 + mass_per_radius / 8.0)
    geometry_score = max(0.0, 1.0 - abs(inputs.pitch_angle_deg - 4.0) / 25.0)

    score = (
        0.45 * cp_score
        + 0.20 * tsr_score
        + 0.15 * mass_score
        + 0.10 * geometry_score
        + 0.10 * material_durability
    )
    return round(100.0 * score, 1)


def build_recommendations(
    inputs: SimulationInput,
    cp: float,
    tip_speed_ratio: float,
) -> tuple[str, ...]:
    """Generate concise next experiments instead of engineering instructions."""

    notes: list[str] = []
    if cp < 0.30:
        notes.append("Try pitch angles nearer 2-8° and compare the resulting Cp.")
    if inputs.twist_angle_deg < 6.0:
        notes.append("Test more blade twist; moderate twist may improve the educational model.")
    elif inputs.twist_angle_deg > 25.0:
        notes.append("Test less blade twist to see whether efficiency improves.")
    if tip_speed_ratio < 4.0:
        notes.append("The rotor is relatively slow; compare fewer blades or lower blade mass.")
    elif tip_speed_ratio > 9.0:
        notes.append("The estimated tip speed is high; compare a higher blade count.")
    if inputs.blade_mass_kg / inputs.rotor_radius_m > 10.0:
        notes.append("Compare a lighter blade while keeping its geometry unchanged.")
    if not notes:
        notes.append(
            "This is a balanced baseline. Change one variable at a time and record the result."
        )
    return tuple(notes)
