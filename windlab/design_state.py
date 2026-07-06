"""Serialization helpers for local design persistence."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from windlab.blade_geometry import competition_50cm_sections
from windlab.models import BladeSection, SimulationInput
from windlab.section_airfoils import get_section_airfoil

DEFAULT_DESIGN_NAME = "Current design"
BLANK_DESIGN_NAME = "Untitled custom design"
DESIGN_SCHEMA_VERSION = 1


def _section_role(airfoil_name: str) -> str:
    """Return the default catalog role for a blade-section airfoil."""

    return get_section_airfoil(airfoil_name).role


def blank_blade_sections(rotor_radius_m: float = 0.45) -> tuple[BladeSection, ...]:
    """Return a minimal editable blade table for building from scratch."""

    tip_position_m = max(float(rotor_radius_m), 0.12)
    return (
        BladeSection(
            position_m=0.06,
            chord_m=0.08,
            twist_angle_deg=12.0,
            airfoil_name="NACA 4412",
            airfoil_role=_section_role("NACA 4412"),
        ),
        BladeSection(
            position_m=tip_position_m,
            chord_m=0.03,
            twist_angle_deg=0.0,
            airfoil_name="NACA 0012",
            airfoil_role=_section_role("NACA 0012"),
        ),
    )


def blank_design_input() -> SimulationInput:
    """Return a valid custom-design starting point with only root and tip sections."""

    rotor_radius_m = 0.45
    return SimulationInput(
        wind_speed_m_s=3.6,
        rotor_radius_m=rotor_radius_m,
        hub_radius_m=0.05,
        blade_count=3,
        blade_sections=blank_blade_sections(rotor_radius_m),
    )


def default_design_input() -> SimulationInput:
    """Return the default competition-oriented design."""

    return SimulationInput(
        wind_speed_m_s=3.6,
        rotor_radius_m=0.45,
        hub_radius_m=0.10,
        blade_count=3,
        blade_sections=competition_50cm_sections(),
    )


def design_input_to_dict(inputs: SimulationInput) -> dict[str, Any]:
    """Return a JSON-safe dictionary for a simulation input."""

    payload = inputs.model_dump(mode="json")
    payload["schema_version"] = DESIGN_SCHEMA_VERSION
    return deepcopy(payload)


def design_input_from_dict(payload: dict[str, Any]) -> SimulationInput:
    """Build a SimulationInput from a JSON-safe dictionary."""

    clean_payload = dict(payload)
    clean_payload.pop("schema_version", None)
    return SimulationInput.model_validate(clean_payload)
