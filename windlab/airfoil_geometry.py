"""Simple airfoil profile coordinates for dashboard previews."""

from math import atan, cos, pi, sin, sqrt


def parse_naca_4digit(name: str) -> tuple[float, float, float] | None:
    """Return camber, camber-position, and thickness ratios for NACA 4-digit names."""

    digits = name.upper().replace("NACA", "").replace("-", "").replace(" ", "").strip()
    if len(digits) != 4 or not digits.isdigit():
        return None

    camber = int(digits[0]) / 100.0
    camber_position = int(digits[1]) / 10.0
    thickness = int(digits[2:]) / 100.0
    return camber, camber_position, thickness


def _naca_4digit_profile(
    *,
    camber: float,
    camber_position: float,
    thickness: float,
    point_count: int,
) -> list[tuple[float, float]]:
    """Generate normalized closed profile coordinates for a NACA 4-digit airfoil."""

    xs = [0.5 * (1.0 - cos(pi * index / (point_count - 1))) for index in range(point_count)]
    upper: list[tuple[float, float]] = []
    lower: list[tuple[float, float]] = []

    for x in xs:
        yt = (
            5.0
            * thickness
            * (
                0.2969 * sqrt(max(x, 0.0))
                - 0.1260 * x
                - 0.3516 * x**2
                + 0.2843 * x**3
                - 0.1015 * x**4
            )
        )
        if camber > 0.0 and 0.0 < camber_position < 1.0:
            if x < camber_position:
                yc = camber / camber_position**2 * (2.0 * camber_position * x - x**2)
                dyc_dx = 2.0 * camber / camber_position**2 * (camber_position - x)
            else:
                yc = (
                    camber
                    / (1.0 - camber_position) ** 2
                    * ((1.0 - 2.0 * camber_position) + 2.0 * camber_position * x - x**2)
                )
                dyc_dx = 2.0 * camber / (1.0 - camber_position) ** 2 * (camber_position - x)
        else:
            yc = 0.0
            dyc_dx = 0.0

        theta = atan(dyc_dx)
        upper.append((x - yt * sin(theta), yc + yt * cos(theta)))
        lower.append((x + yt * sin(theta), yc - yt * cos(theta)))

    return list(reversed(upper)) + lower[1:]


def airfoil_profile_points(name: str, point_count: int = 80) -> list[tuple[float, float]]:
    """Return normalized profile points for a student-facing airfoil preview."""

    if point_count < 8:
        raise ValueError("point_count must be at least 8.")

    parsed = parse_naca_4digit(name)
    if parsed is not None:
        camber, camber_position, thickness = parsed
        return _naca_4digit_profile(
            camber=camber,
            camber_position=camber_position,
            thickness=thickness,
            point_count=point_count,
        )

    if name == "Flat plate":
        thickness = 0.012
        return [
            (1.0, thickness / 2.0),
            (0.0, thickness / 2.0),
            (0.0, -thickness / 2.0),
            (1.0, -thickness / 2.0),
        ]
    source_backed_shapes = {
        "Clark Y": (0.035, 0.40, 0.117),
        "SG6040": (0.045, 0.45, 0.160),
        "SG6042": (0.045, 0.48, 0.100),
        "SG6043": (0.051, 0.533, 0.100),
        "S1223": (0.055, 0.35, 0.121),
        "Selig S1223": (0.055, 0.35, 0.121),
        "E387": (0.035, 0.40, 0.091),
        "NREL S822": (0.040, 0.42, 0.160),
        "NREL S823": (0.045, 0.42, 0.210),
    }
    if name in source_backed_shapes:
        camber, camber_position, thickness = source_backed_shapes[name]
        return _naca_4digit_profile(
            camber=camber,
            camber_position=camber_position,
            thickness=thickness,
            point_count=point_count,
        )

    return _naca_4digit_profile(
        camber=0.02,
        camber_position=0.40,
        thickness=0.12,
        point_count=point_count,
    )
