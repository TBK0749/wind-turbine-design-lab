import pytest

from windlab.airfoils import (
    AIRFOIL_LIBRARY,
    estimate_airfoil_performance,
    lookup_airfoil_polar,
)


def test_airfoil_library_contains_classroom_options() -> None:
    assert set(AIRFOIL_LIBRARY) == {
        "Flat plate / Foam board",
        "Cambered plate",
        "Symmetric airfoil",
        "High-lift airfoil",
    }


def test_cambered_plate_outperforms_flat_plate_at_moderate_angle() -> None:
    flat = estimate_airfoil_performance(
        "Flat plate / Foam board",
        angle_of_attack_deg=6.0,
        reynolds_number=150_000.0,
    )
    cambered = estimate_airfoil_performance(
        "Cambered plate",
        angle_of_attack_deg=6.0,
        reynolds_number=150_000.0,
    )

    assert cambered.lift_drag_ratio > flat.lift_drag_ratio
    assert cambered.efficiency_factor > flat.efficiency_factor


def test_high_angle_warns_about_stall_and_penalizes_efficiency() -> None:
    moderate = estimate_airfoil_performance(
        "High-lift airfoil",
        angle_of_attack_deg=8.0,
        reynolds_number=150_000.0,
    )
    stalled = estimate_airfoil_performance(
        "High-lift airfoil",
        angle_of_attack_deg=24.0,
        reynolds_number=150_000.0,
    )

    assert stalled.stall_risk
    assert stalled.efficiency_factor < moderate.efficiency_factor
    assert any("stall" in warning.lower() for warning in stalled.warnings)


def test_low_reynolds_number_reduces_lift_and_increases_drag() -> None:
    moderate_re = estimate_airfoil_performance(
        "High-lift airfoil",
        angle_of_attack_deg=6.0,
        reynolds_number=200_000.0,
    )
    very_low_re = estimate_airfoil_performance(
        "High-lift airfoil",
        angle_of_attack_deg=6.0,
        reynolds_number=25_000.0,
    )

    assert very_low_re.lift_coefficient < moderate_re.lift_coefficient
    assert very_low_re.drag_coefficient > moderate_re.drag_coefficient
    assert very_low_re.efficiency_factor < moderate_re.efficiency_factor
    assert any("Reynolds" in warning for warning in very_low_re.warnings)


def test_high_lift_low_re_polar_preserves_useful_lift_to_drag() -> None:
    high_lift = estimate_airfoil_performance(
        "High-lift airfoil",
        angle_of_attack_deg=6.0,
        reynolds_number=25_000.0,
    )
    flat_plate = estimate_airfoil_performance(
        "Flat plate / Foam board",
        angle_of_attack_deg=6.0,
        reynolds_number=25_000.0,
    )

    assert high_lift.lift_coefficient > 0.60
    assert high_lift.drag_coefficient < 0.10
    assert high_lift.efficiency_factor > 0.60
    assert high_lift.lift_drag_ratio > flat_plate.lift_drag_ratio * 2.0


def test_lookup_airfoil_polar_interpolates_angle_and_reynolds_number() -> None:
    low_re = lookup_airfoil_polar(
        "NACA 4412",
        angle_of_attack_deg=6.0,
        reynolds_number=50_000.0,
    )
    high_re = lookup_airfoil_polar(
        "NACA 4412",
        angle_of_attack_deg=6.0,
        reynolds_number=200_000.0,
    )

    assert low_re.lift_coefficient < high_re.lift_coefficient
    assert low_re.drag_coefficient > high_re.drag_coefficient
    assert 0.70 < high_re.lift_coefficient < 1.10
    assert 0.020 < high_re.drag_coefficient < 0.050


def test_specific_naca_polar_changes_drag_and_efficiency() -> None:
    root = estimate_airfoil_performance(
        "High-lift airfoil",
        airfoil_name="NACA 4418",
        angle_of_attack_deg=6.0,
        reynolds_number=100_000.0,
    )
    mid = estimate_airfoil_performance(
        "High-lift airfoil",
        airfoil_name="NACA 4412",
        angle_of_attack_deg=6.0,
        reynolds_number=100_000.0,
    )
    tip = estimate_airfoil_performance(
        "Cambered plate",
        airfoil_name="NACA 2412",
        angle_of_attack_deg=6.0,
        reynolds_number=100_000.0,
    )

    assert root.drag_coefficient > mid.drag_coefficient
    assert root.lift_drag_ratio < mid.lift_drag_ratio
    assert tip.drag_coefficient <= mid.drag_coefficient


def test_unknown_airfoil_is_rejected() -> None:
    with pytest.raises(ValueError, match="Airfoil"):
        estimate_airfoil_performance(
            "Magic airfoil",
            angle_of_attack_deg=6.0,
            reynolds_number=150_000.0,
        )
