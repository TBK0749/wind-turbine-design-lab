"""Serialization helpers for local design persistence."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from windlab.blade_geometry import competition_50cm_sections
from windlab.models import SimulationInput

DEFAULT_DESIGN_NAME = "Current design"
DESIGN_SCHEMA_VERSION = 1


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
