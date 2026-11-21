import pytest

from app.components.input_panel import (
    _insert_interpolated_section_rows,
    _resolve_rotor_radius_for_sections,
    _root_refinement_positions,
    _section_frame_from_sections,
    _sections_from_frame,
)
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


def test_root_refinement_positions_split_space_before_first_station() -> None:
    positions = _root_refinement_positions(first_position_cm=6.0, count=3)

    assert positions == pytest.approx((1.5, 3.0, 4.5))


def test_insert_interpolated_section_rows_sorts_and_relabels_sections() -> None:
    frame = _section_frame_from_sections(_sections_with_50cm_tip())

    updated = _insert_interpolated_section_rows(frame, (1.5, 3.0, 4.5))

    assert list(updated["Position (cm)"])[:4] == pytest.approx([1.5, 3.0, 4.5, 6.0])
    assert list(updated["Section"]) == ["1 (Root)", "2", "3", "4", "5 (Tip)"]
    assert list(updated["Chord (cm)"])[:4] == pytest.approx([9.0, 9.0, 9.0, 9.0])
    assert list(updated["Twist (deg)"])[:4] == pytest.approx([20.0, 20.0, 20.0, 20.0])
    assert all(airfoil == "NACA 4412" for airfoil in updated["Airfoil"])


def test_insert_interpolated_section_rows_interpolates_between_existing_stations() -> None:
    frame = _section_frame_from_sections(_sections_with_50cm_tip())

    updated = _insert_interpolated_section_rows(frame, (28.0,))
    sections = _sections_from_frame(updated)
    inserted = sections[1]

    assert inserted.position_m == pytest.approx(0.28)
    assert inserted.chord_m == pytest.approx(0.054)
    assert inserted.twist_angle_deg == pytest.approx(10.0)
