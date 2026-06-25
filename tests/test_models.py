import pytest
from pydantic import ValidationError

from windlab.models import BladeSection, SimulationInput


def test_hub_must_be_smaller_than_rotor() -> None:
    with pytest.raises(ValidationError, match="Hub radius"):
        SimulationInput(rotor_radius_m=1.0, hub_radius_m=1.0)


def test_unknown_material_is_rejected() -> None:
    with pytest.raises(ValidationError, match="Material"):
        SimulationInput(material="Unobtainium")


def test_unknown_airfoil_is_rejected() -> None:
    with pytest.raises(ValidationError, match="Airfoil"):
        SimulationInput(airfoil_type="Magic airfoil")


def test_section_cannot_extend_beyond_blade_tip() -> None:
    with pytest.raises(ValidationError, match="final blade section"):
        SimulationInput(
            rotor_radius_m=0.5,
            hub_radius_m=0.05,
            blade_sections=(
                BladeSection(position_m=0.05, chord_m=0.09, twist_angle_deg=20.0),
                BladeSection(position_m=0.60, chord_m=0.02, twist_angle_deg=0.0),
            ),
        )
