from math import pi

import pytest

from windlab.physics import (
    BETZ_LIMIT,
    available_wind_power,
    estimate_cp,
    rotor_swept_area,
    torque_from_power,
)


def test_rotor_swept_area_excludes_hub() -> None:
    assert rotor_swept_area(2.0, 0.5) == pytest.approx(pi * (4.0 - 0.25))


def test_wind_power_follows_cube_law() -> None:
    area = 5.0
    low = available_wind_power(1.225, area, 4.0)
    high = available_wind_power(1.225, area, 8.0)
    assert high == pytest.approx(low * 8.0)


def test_cp_stays_below_betz_limit() -> None:
    cp = estimate_cp(
        tip_speed_ratio=7.0,
        blade_count=3,
        root_chord_m=0.2,
        tip_chord_m=0.1,
        rotor_radius_m=1.0,
        pitch_angle_deg=4.0,
        twist_angle_deg=12.0,
        roughness_factor=1.0,
    )
    assert 0.0 < cp < BETZ_LIMIT


def test_large_clean_rotor_gets_small_scale_recovery() -> None:
    small_clean = estimate_cp(
        tip_speed_ratio=6.85,
        blade_count=3,
        root_chord_m=0.045,
        tip_chord_m=0.012,
        rotor_radius_m=0.2,
        pitch_angle_deg=2.0,
        twist_angle_deg=18.0,
        roughness_factor=0.93,
        mean_chord_m=0.0285,
    )
    large_clean = estimate_cp(
        tip_speed_ratio=6.85,
        blade_count=3,
        root_chord_m=0.22,
        tip_chord_m=0.06,
        rotor_radius_m=2.0,
        pitch_angle_deg=2.0,
        twist_angle_deg=14.0,
        roughness_factor=0.93,
        mean_chord_m=0.14,
    )
    large_rough = estimate_cp(
        tip_speed_ratio=6.85,
        blade_count=3,
        root_chord_m=0.22,
        tip_chord_m=0.06,
        rotor_radius_m=2.0,
        pitch_angle_deg=2.0,
        twist_angle_deg=14.0,
        roughness_factor=0.70,
        mean_chord_m=0.14,
    )

    assert large_clean > large_rough / 0.70 * 0.93
    assert small_clean < large_clean


def test_torque_is_stable_at_zero_angular_speed() -> None:
    assert torque_from_power(100.0, 0.0) == pytest.approx(2000.0)
