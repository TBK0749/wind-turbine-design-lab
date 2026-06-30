from pathlib import Path

from windlab.design_state import default_design_input
from windlab.design_store import DesignStore


def test_design_store_saves_and_loads_named_design(tmp_path: Path) -> None:
    store = DesignStore(tmp_path / "windlab.sqlite")
    inputs = default_design_input().model_copy(update={"wind_speed_m_s": 3.6})

    store.save_named_design("Team A v1", inputs)
    names = store.list_design_names()
    loaded = store.load_named_design("Team A v1")

    assert names == ["Team A v1"]
    assert loaded is not None
    assert loaded.wind_speed_m_s == 3.6
    assert loaded.blade_sections[0].airfoil_name == "NACA 4418"


def test_design_store_autosaves_current_design(tmp_path: Path) -> None:
    store = DesignStore(tmp_path / "windlab.sqlite")
    inputs = default_design_input().model_copy(update={"rotor_radius_m": 0.50})

    store.autosave_current(inputs)
    loaded = store.load_current_design()

    assert loaded is not None
    assert loaded.rotor_radius_m == 0.50


def test_design_store_creates_parent_directory(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "windlab.sqlite"

    store = DesignStore(db_path)
    store.autosave_current(default_design_input())

    assert db_path.exists()
