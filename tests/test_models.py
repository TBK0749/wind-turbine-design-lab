import pytest
from pydantic import ValidationError

from windlab.models import SimulationInput


def test_hub_must_be_smaller_than_rotor() -> None:
    with pytest.raises(ValidationError, match="Hub radius"):
        SimulationInput(rotor_radius_m=1.0, hub_radius_m=1.0)


def test_unknown_material_is_rejected() -> None:
    with pytest.raises(ValidationError, match="Material"):
        SimulationInput(material="Unobtainium")
