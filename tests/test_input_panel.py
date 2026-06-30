import pytest

from app.components.input_panel import _resolve_rotor_radius_for_sections
from windlab.models import BladeSection


def _sections_with_50cm_tip() -> tuple[BladeSection, ...]:
    return (
        BladeSection(position_m=0.06, chord_m=0.09, twist_angle_deg=20.0),
        BladeSection(position_m=0.50, chord_m=0.018, twist_angle_deg=0.0),
    )


def test_section_table_extends_effective_rotor_radius_to_tip_station() -> None:
    rotor_radius, warning = _resolve_rotor_radius_for_sections(0.45, _sections_with_50cm_tip())

    assert rotor_radius == pytest.approx(0.50)
    assert warning is not None
    assert "Final blade section is 50.0 cm" in warning
    assert "rotor radius is 45.0 cm" in warning
    assert "change the final Position" in warning


def test_section_table_keeps_matching_rotor_radius_without_warning() -> None:
    rotor_radius, warning = _resolve_rotor_radius_for_sections(0.50, _sections_with_50cm_tip())

    assert rotor_radius == pytest.approx(0.50)
    assert warning is None
