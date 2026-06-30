import json
import zipfile
from io import BytesIO

from windlab.blade_presets import get_blade_preset, preset_to_simulation_input
from windlab.onshape_export import (
    blade_geometry_csv,
    blade_planform_dxf,
    build_onshape_package,
    section_profiles_dxf,
)


def _sample_input():
    return preset_to_simulation_input(get_blade_preset("Balanced Competition 50 cm"))


def test_onshape_package_contains_expected_files() -> None:
    package = build_onshape_package(_sample_input(), design_name="student blade")

    with zipfile.ZipFile(BytesIO(package)) as archive:
        names = set(archive.namelist())
        metadata = json.loads(archive.read("design_metadata.json"))

    assert names == {
        "blade_geometry.csv",
        "airfoil_sections.csv",
        "blade_planform.dxf",
        "section_profiles.dxf",
        "design_metadata.json",
        "onshape_build_guide.md",
    }
    assert metadata["design_name"] == "student blade"
    assert metadata["rotor_diameter_m"] == 1.0
    assert metadata["blade_count"] == 3


def test_blade_geometry_csv_contains_sections_and_airfoils() -> None:
    csv_text = blade_geometry_csv(_sample_input())

    assert "Section,Position (cm),Chord (cm),Twist (deg),Airfoil,Role" in csv_text
    assert "1 (Root),6.0,9.0,20.0,NACA 4418" in csv_text
    assert "6 (Tip),50.0,1.8,0.0,E387" in csv_text


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
