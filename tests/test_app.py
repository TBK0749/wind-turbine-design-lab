from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_streamlit_app_renders_competition_result() -> None:
    app_path = Path(__file__).parents[1] / "app" / "main.py"
    app = AppTest.from_file(str(app_path), default_timeout=15).run()

    assert not app.exception
    assert any(metric.label == "Competition power" for metric in app.metric)
    assert any(metric.label == "Airfoil efficiency" for metric in app.metric)
    assert any(section.value == "Blade geometry table" for section in app.subheader)
    assert any(section.value == "Blade build preview" for section in app.subheader)
    assert any(section.value == "Airfoil result" for section in app.subheader)
    assert any(section.value == "Competition result" for section in app.subheader)


def test_streamlit_app_renders_english_guide_and_glossary() -> None:
    app_path = Path(__file__).parents[1] / "app" / "main.py"
    app = AppTest.from_file(str(app_path), default_timeout=15).run()

    assert not app.exception
    assert any(section.value == "Quick start guide" for section in app.subheader)
    assert any(section.value == "Local installation guide" for section in app.subheader)
    assert any(section.value == "Updating to the latest version" for section in app.subheader)
    assert any(section.value == "Key terms glossary" for section in app.subheader)
    assert any("Run the app locally" in text.value for text in app.markdown)
    assert any("git pull" in text.value for text in app.markdown)
    assert any("Power coefficient (Cp)" in text.value for text in app.markdown)
    assert any("Tip-speed ratio (TSR)" in text.value for text in app.markdown)
    assert any("Competition power (mW)" in text.value for text in app.markdown)


def test_advanced_calibration_controls_are_available() -> None:
    app_path = Path(__file__).parents[1] / "app" / "main.py"
    app = AppTest.from_file(str(app_path), default_timeout=15).run()

    assert not app.exception
    assert any("Advanced calibration" in expander.label for expander in app.expander)
    assert any("Use airfoil correction" in checkbox.label for checkbox in app.checkbox)
    assert any("Startup/cogging torque" in number.label for number in app.number_input)


def test_custom_material_controls_are_available() -> None:
    app_path = Path(__file__).parents[1] / "app" / "main.py"
    app = AppTest.from_file(str(app_path), default_timeout=15).run()

    assert not app.exception
    assert any("Use custom material properties" in checkbox.label for checkbox in app.checkbox)
    assert any("Estimate blade mass from density" in checkbox.label for checkbox in app.checkbox)
    assert any("Material density" in number.label for number in app.number_input)
    assert any(selectbox.label == "Surface finish" for selectbox in app.selectbox)
    assert any(metric.label == "Blade mass" for metric in app.metric)


def test_section_airfoil_table_columns_are_available() -> None:
    app_path = Path(__file__).parents[1] / "app" / "main.py"
    app = AppTest.from_file(str(app_path), default_timeout=15).run()

    assert not app.exception
    assert any("NACA 4418" in text.value for text in app.markdown)
    assert any(metric.label == "Representative airfoil" for metric in app.metric)


def test_global_airfoil_selector_is_hidden_in_section_table_mode() -> None:
    app_path = Path(__file__).parents[1] / "app" / "main.py"
    app = AppTest.from_file(str(app_path), default_timeout=15).run()

    assert not app.exception
    assert not any(selectbox.label == "Airfoil type" for selectbox in app.selectbox)
    assert any(
        "Section table airfoils override the simple airfoil selector" in text.value
        for text in app.markdown
    )


def test_airfoil_help_explains_naca_codes() -> None:
    app_path = Path(__file__).parents[1] / "app" / "main.py"
    app = AppTest.from_file(str(app_path), default_timeout=15).run()

    assert not app.exception
    assert any("Airfoil Help" in expander.label for expander in app.expander)
    assert any("Airfoil is the blade cross-section" in text.value for text in app.markdown)
    assert any("4418 = 4% camber" in text.value for text in app.markdown)
    assert any("Best zone" in text.value for text in app.markdown)


def test_bemt_lite_model_mode_is_visible() -> None:
    app_path = Path(__file__).parents[1] / "app" / "main.py"
    app = AppTest.from_file(str(app_path), default_timeout=15).run()

    assert not app.exception
    assert any(metric.label == "Model mode" for metric in app.metric)
    assert any(metric.label == "BEMT sections" for metric in app.metric)
    assert any(metric.label == "Spin-up factor" for metric in app.metric)
    assert any(metric.label == "Required start torque" for metric in app.metric)
    assert any("Use BEMT-lite section model" in checkbox.label for checkbox in app.checkbox)
