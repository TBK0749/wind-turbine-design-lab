"""Material presets used by the educational scoring model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Material:
    """Simple material metadata for classroom comparison."""

    name: str
    density_kg_m3: float
    roughness_factor: float
    durability_factor: float


MATERIALS: dict[str, Material] = {
    "Wood": Material("Wood", 650.0, 0.94, 0.70),
    "Plastic": Material("Plastic", 1100.0, 0.96, 0.65),
    "Aluminum": Material("Aluminum", 2700.0, 0.98, 0.90),
    "Carbon fiber": Material("Carbon fiber", 1600.0, 1.00, 1.00),
}


def get_material(name: str) -> Material:
    """Return material data, raising a friendly error for unknown values."""

    try:
        return MATERIALS[name]
    except KeyError as exc:
        choices = ", ".join(MATERIALS)
        raise ValueError(f"Unknown material '{name}'. Choose one of: {choices}.") from exc
