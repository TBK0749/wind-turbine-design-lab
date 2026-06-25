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
