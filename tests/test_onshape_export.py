import json
import zipfile
from io import BytesIO

from windlab.blade_presets import get_blade_preset, preset_to_simulation_input
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
