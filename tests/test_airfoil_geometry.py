import pytest

from windlab.airfoil_geometry import airfoil_profile_points, parse_naca_4digit


def test_parse_naca_4digit_airfoil_code() -> None:
    assert parse_naca_4digit("NACA 4418") == pytest.approx((0.04, 0.40, 0.18))
    assert parse_naca_4digit("NACA 0012") == pytest.approx((0.0, 0.0, 0.12))


def test_naca_profile_points_have_visible_thickness() -> None:
    thick = airfoil_profile_points("NACA 4418")
    thin = airfoil_profile_points("NACA 2412")

    assert len(thick) > 80
    assert max(y for _, y in thick) > max(y for _, y in thin)
    assert min(x for x, _ in thick) == pytest.approx(0.0, abs=0.01)
    assert max(x for x, _ in thick) == pytest.approx(1.0, abs=0.01)


def test_flat_plate_profile_is_supported() -> None:
    profile = airfoil_profile_points("Flat plate")

    assert len(profile) == 4
    assert max(y for _, y in profile) > 0.0
