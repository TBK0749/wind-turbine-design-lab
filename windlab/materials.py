"""Material presets used by the educational scoring model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Material:
    """Simple material metadata for classroom comparison."""

    name: str
    density_kg_m3: float
    roughness_factor: float
    durability_factor: float


@dataclass(frozen=True, slots=True)
class SurfaceFinish:
    """Surface finish multiplier for small educational rotors."""

    name: str
    drag_factor: float
    description: str


MATERIALS: dict[str, Material] = {
    "Wood": Material("Wood", 650.0, 0.94, 0.70),
    "Plastic": Material("Plastic", 1100.0, 0.96, 0.65),
    "Aluminum": Material("Aluminum", 2700.0, 0.98, 0.90),
    "Carbon fiber": Material("Carbon fiber", 1600.0, 1.00, 1.00),
}

SURFACE_FINISHES: dict[str, SurfaceFinish] = {
    "Raw 3D print": SurfaceFinish(
        "Raw 3D print",
        0.86,
        "Visible layer lines; easy to print but adds drag.",
    ),
    "Lightly sanded": SurfaceFinish(
        "Lightly sanded",
        0.93,
        "Layer lines reduced; good classroom improvement.",
    ),
    "Painted / coated": SurfaceFinish(
        "Painted / coated",
        0.97,
        "Smoother sealed surface with lower drag.",
    ),
    "Smooth molded": SurfaceFinish(
        "Smooth molded",
        1.00,
        "Best-case smooth surface for comparison.",
    ),
    "Rough foam board": SurfaceFinish(
        "Rough foam board",
        0.82,
        "Hand-cut rough surface; useful for quick prototypes.",
    ),
}


def get_material(name: str) -> Material:
    """Return material data, raising a friendly error for unknown values."""

    try:
        return MATERIALS[name]
    except KeyError as exc:
        choices = ", ".join(MATERIALS)
        raise ValueError(f"Unknown material '{name}'. Choose one of: {choices}.") from exc


def get_surface_finish(name: str) -> SurfaceFinish:
    """Return surface finish data, raising a friendly error for unknown values."""

    try:
        return SURFACE_FINISHES[name]
    except KeyError as exc:
        choices = ", ".join(SURFACE_FINISHES)
        raise ValueError(f"Unknown surface finish '{name}'. Choose one of: {choices}.") from exc
