from pathlib import Path


def test_streamlit_config_hides_developer_toolbar() -> None:
    config = Path(".streamlit/config.toml").read_text()

    assert "[client]" in config
    assert 'toolbarMode = "viewer"' in config


def test_readme_contains_local_installation_guide() -> None:
    readme = Path("README.md").read_text()
    beginner_guide = Path("output/pdf/Wind_Turbine_Design_Lab_Local_Installation_Guide.pdf")

    assert "## Local installation guide" in readme
    assert "Beginner PDF manual" in readme
    assert beginner_guide.as_posix() in readme
    assert beginner_guide.exists()
    assert "## Updating to the latest version" in readme
    assert "Download as ZIP" in readme
    assert "git pull" in readme
    assert "Run the app locally" in readme
    assert "Do not click Deploy" in readme


def test_installation_doc_uses_real_github_url() -> None:
    install_doc = Path("docs/installation.md").read_text()

    assert "https://github.com/TBK0749/wind-turbine-design-lab.git" in install_doc
    assert "<repository-url>" not in install_doc
    assert "git pull" in install_doc


def test_paper_model_notes_document_supplied_papers() -> None:
    paper_notes = Path("docs/paper_model_notes.md").read_text()

    assert "SWEPT" in paper_notes
    assert "Low Reynolds" in paper_notes
    assert "Prandtl" in paper_notes
    assert "COMPARATIVE ANALYSIS OF SMALL-SCALE WIND TURBINE.pdf" in paper_notes


def test_docs_link_to_model_validation_report() -> None:
    readme = Path("README.md").read_text()
    physics_doc = Path("docs/physics_model.md").read_text()
    validation_report = Path("docs/model_validation_report.md")

    assert "docs/model_validation_report.md" in readme
    assert "docs/model_validation_report.md" in physics_doc
    assert validation_report.exists()


def test_physics_docs_describe_source_backed_airfoil_limits() -> None:
    physics_doc = Path("docs/physics_model.md").read_text()
    paper_notes = Path("docs/paper_model_notes.md").read_text()

    assert "Conservative source-backed airfoils" in physics_doc
    assert "SG6043" in physics_doc
    assert "not certify exact measured power" in physics_doc
    assert "Source-backed airfoil expansion" in paper_notes
    assert "not raw measured polar imports" in paper_notes


def test_docs_describe_local_workspace_and_onshape_export() -> None:
    readme = Path("README.md").read_text()

    assert "## Local design workspace" in readme
    assert "user_data/windlab.sqlite" in readme
    assert "Undo/Redo" in readme
    assert "six 3-blade starter presets" in readme
    assert "## Onshape package export" in readme
    assert "Download Onshape package" in readme
    assert "not a print-ready STL" in readme


def test_onshape_workflow_manual_exists_and_is_linked() -> None:
    readme = Path("README.md").read_text()
    manual = Path("docs/onshape_workflow_manual.md")
    pdf = Path("output/pdf/Wind_Turbine_Design_Lab_Onshape_Workflow_Manual.pdf")

    assert manual.exists()
    assert pdf.exists()
    assert "Onshape workflow manual" in readme
    assert pdf.as_posix() in readme


def test_onshape_manual_explains_right_plane_and_offset_error() -> None:
    manual = Path("docs/onshape_workflow_manual.md").read_text()

    assert "use the Right plane as S1 Root" in manual
    assert "Do not create a new plane for section 1" in manual
    assert "Right plane = S1 Root" in manual
    assert "Offset plane requires a plane" in manual
    assert "do not leave the distance as `1 in`" in manual


def test_onshape_manual_explains_split_section_profiles() -> None:
    manual = Path("docs/onshape_workflow_manual.md").read_text()

    assert "section_profiles/section_01_root_NACA4418.dxf" in manual
    assert "one ready-to-insert DXF per blade section" in manual
    assert "Do not use `section_profiles.dxf` as the main beginner workflow" in manual
    assert "do not need to delete the other sections" in manual


def test_onshape_manual_covers_beginner_to_stl_workflow() -> None:
    manual = Path("docs/onshape_workflow_manual.md").read_text()

    assert "Do not create the hub sketch on a Mate connector" in manual
    assert "Beginner hub dimensions" in manual
    assert "Circular Pattern" in manual
    assert "Pattern type: `Part pattern`" in manual
    assert "Quantity: `3`" in manual
    assert "S7 Tip plane is not an airfoil profile" in manual
    assert "Export format: `STL`" in manual
    assert "Binary STL" in manual
    assert "Open the STL in your slicer before printing" in manual
