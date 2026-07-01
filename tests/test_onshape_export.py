import json
import zipfile
from io import BytesIO

from windlab.blade_presets import blade_preset_options, get_blade_preset, preset_to_simulation_input
from windlab.onshape_export import (
    blade_geometry_csv,
    blade_planform_dxf,
    build_onshape_package,
    individual_section_profile_dxfs,
    section_profile_dxf,
    section_profile_filename,
    section_profiles_dxf,
)


def _sample_input():
    return preset_to_simulation_input(get_blade_preset("Balanced Competition 50 cm"))


def _dxf_lwpolyline_vertex_count(dxf: str) -> int:
    tokens = dxf.splitlines()
    for index, token in enumerate(tokens):
        if token == "90" and index + 1 < len(tokens):
            return int(tokens[index + 1])
    raise AssertionError("DXF does not contain an LWPOLYLINE vertex count")


def _dxf_lwpolyline_points(dxf: str) -> list[tuple[float, float]]:
    tokens = dxf.splitlines()
    points: list[tuple[float, float]] = []
    index = 0
    while index < len(tokens):
        if tokens[index] == "10" and index + 3 < len(tokens) and tokens[index + 2] == "20":
            points.append((float(tokens[index + 1]), float(tokens[index + 3])))
            index += 4
            continue
        index += 1
    if not points:
        raise AssertionError("DXF does not contain LWPOLYLINE points")
    return points


def _signed_area(points: list[tuple[float, float]]) -> float:
    return 0.5 * sum(
        points[index][0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * points[index][1]
        for index in range(len(points))
    )


def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _segments_cross(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> bool:
    return (
        _orientation(a, b, c) * _orientation(a, b, d) < 0
        and _orientation(
            c,
            d,
            a,
        )
        * _orientation(c, d, b)
        < 0
    )


def _has_self_intersection(points: list[tuple[float, float]]) -> bool:
    segment_count = len(points)
    for left_index in range(segment_count):
        left_start = points[left_index]
        left_end = points[(left_index + 1) % segment_count]
        for right_index in range(left_index + 1, segment_count):
            if abs(left_index - right_index) <= 1:
                continue
            if {left_index, right_index} == {0, segment_count - 1}:
                continue
            right_start = points[right_index]
            right_end = points[(right_index + 1) % segment_count]
            if _segments_cross(left_start, left_end, right_start, right_end):
                return True
    return False


def _minimum_edge_length(points: list[tuple[float, float]]) -> float:
    return min(
        (
            (points[(index + 1) % len(points)][0] - points[index][0]) ** 2
            + (points[(index + 1) % len(points)][1] - points[index][1]) ** 2
        )
        ** 0.5
        for index in range(len(points))
    )


def test_onshape_package_contains_expected_files() -> None:
    package = build_onshape_package(_sample_input(), design_name="student blade")

    with zipfile.ZipFile(BytesIO(package)) as archive:
        names = set(archive.namelist())
        metadata = json.loads(archive.read("design_metadata.json"))

    assert {
        "blade_geometry.csv",
        "airfoil_sections.csv",
        "blade_planform.dxf",
        "section_profiles.dxf",
        "section_profiles/README.md",
        "design_metadata.json",
        "onshape_build_guide.md",
    }.issubset(names)
    assert sorted(name for name in names if name.startswith("section_profiles/section_")) == [
        "section_profiles/section_01_root_NACA4418.dxf",
        "section_profiles/section_02_NACA4418.dxf",
        "section_profiles/section_03_SG6040.dxf",
        "section_profiles/section_04_SG6043.dxf",
        "section_profiles/section_05_SG6043.dxf",
        "section_profiles/section_06_NACA2412.dxf",
        "section_profiles/section_07_NACA2412.dxf",
        "section_profiles/section_08_tip_E387.dxf",
    ]
    assert metadata["design_name"] == "student blade"
    assert metadata["rotor_diameter_m"] == 1.0
    assert metadata["blade_count"] == 3


def test_onshape_package_build_guide_mentions_stl_workflow() -> None:
    package = build_onshape_package(_sample_input(), design_name="student blade")

    with zipfile.ZipFile(BytesIO(package)) as archive:
        guide = archive.read("onshape_build_guide.md").decode()

    assert "Beginner hub" in guide
    assert "Circular Pattern" in guide
    assert "Quantity: `3`" in guide
    assert "Export format: `STL`" in guide
    assert "Open the STL in your slicer before printing" in guide


def test_blade_geometry_csv_contains_sections_and_airfoils() -> None:
    csv_text = blade_geometry_csv(_sample_input())

    assert "Section,Position (cm),Chord (cm),Twist (deg),Airfoil,Role" in csv_text
    assert "1 (Root),6.0,9.0,20.0,NACA 4418" in csv_text
    assert "8 (Tip),50.0,1.8,0.0,E387" in csv_text


def test_dxf_exports_have_basic_sections() -> None:
    inputs = _sample_input()
    planform = blade_planform_dxf(inputs)
    profiles = section_profiles_dxf(inputs)

    assert "SECTION" in planform
    assert "LWPOLYLINE" in planform
    assert "blade planform" in planform
    assert "NACA 4418" in profiles
    assert "E387" in profiles
    assert profiles.count("LWPOLYLINE") == len(inputs.blade_sections)


def test_individual_section_profile_filenames_are_onshape_friendly() -> None:
    inputs = _sample_input()
    sections = inputs.blade_sections

    assert section_profile_filename(0, sections[0], len(sections)) == (
        "section_01_root_NACA4418.dxf"
    )
    assert section_profile_filename(1, sections[1], len(sections)) == "section_02_NACA4418.dxf"
    assert section_profile_filename(7, sections[7], len(sections)) == ("section_08_tip_E387.dxf")


def test_individual_section_profile_dxf_has_one_centered_pre_twisted_profile() -> None:
    inputs = _sample_input()
    dxf = section_profile_dxf(inputs.blade_sections[0], index=0, section_count=6)

    assert dxf.count("LWPOLYLINE") == 1
    assert "TEXT" not in dxf
    assert "S2" not in dxf
    assert "section_1_profile" in dxf
    assert "-4." in dxf
    assert "4." in dxf


def test_individual_section_profile_manifest_contains_all_sections() -> None:
    profiles = individual_section_profile_dxfs(_sample_input())

    assert list(profiles) == [
        "section_01_root_NACA4418.dxf",
        "section_02_NACA4418.dxf",
        "section_03_SG6040.dxf",
        "section_04_SG6043.dxf",
        "section_05_SG6043.dxf",
        "section_06_NACA2412.dxf",
        "section_07_NACA2412.dxf",
        "section_08_tip_E387.dxf",
    ]
    assert all(text.count("LWPOLYLINE") == 1 for text in profiles.values())


def test_individual_section_profiles_use_loft_safe_vertex_counts() -> None:
    """Use the selected 120-vertex balance of airfoil fidelity and Onshape safety."""

    for preset in blade_preset_options():
        profiles = individual_section_profile_dxfs(preset_to_simulation_input(preset))
        vertex_counts = {_dxf_lwpolyline_vertex_count(text) for text in profiles.values()}

        assert vertex_counts == {120}


def test_individual_section_profiles_are_clean_for_lofting() -> None:
    """Profiles must be clean closed regions with consistent point orientation."""

    for preset in blade_preset_options():
        profiles = individual_section_profile_dxfs(preset_to_simulation_input(preset))
        point_counts = set()
        area_signs = set()

        for dxf in profiles.values():
            points = _dxf_lwpolyline_points(dxf)
            point_counts.add(len(points))
            area_signs.add(_signed_area(points) > 0)

            assert not _has_self_intersection(points)

        assert len(point_counts) == 1
        assert len(area_signs) == 1


def test_individual_section_profiles_avoid_tiny_sliver_edges() -> None:
    """Avoid near-zero DXF edges while preserving 120-vertex airfoil detail."""

    for preset in blade_preset_options():
        profiles = individual_section_profile_dxfs(preset_to_simulation_input(preset))

        for dxf in profiles.values():
            points = _dxf_lwpolyline_points(dxf)

            assert _minimum_edge_length(points) >= 0.003
