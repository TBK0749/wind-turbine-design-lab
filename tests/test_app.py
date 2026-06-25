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
    assert any(section.value == "Key terms glossary" for section in app.subheader)
    assert any("Power coefficient (Cp)" in text.value for text in app.markdown)
    assert any("Tip-speed ratio (TSR)" in text.value for text in app.markdown)
    assert any("Competition power (mW)" in text.value for text in app.markdown)
