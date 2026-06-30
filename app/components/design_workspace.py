"""Local design workspace controls for autosave, undo/redo, and presets."""

from __future__ import annotations

import streamlit as st

from windlab.blade_presets import blade_preset_options, get_blade_preset, preset_to_simulation_input
from windlab.design_state import DEFAULT_DESIGN_NAME, default_design_input, design_input_to_dict
from windlab.design_store import DesignStore
from windlab.models import SimulationInput

ACTIVE_DESIGN_KEY = "windlab_active_design"
DESIGN_HISTORY_KEY = "windlab_design_history"
REDO_HISTORY_KEY = "windlab_redo_history"
DESIGN_VERSION_KEY = "windlab_design_version"
DESIGN_STORE_KEY = "windlab_design_store"
WORKSPACE_NAME_KEY = "windlab_workspace_design_name"
MAX_HISTORY = 50


def widget_key(name: str) -> str:
    """Return a versioned key so programmatic loads refresh Streamlit widgets."""

    version = int(st.session_state.get(DESIGN_VERSION_KEY, 0))
    return f"{name}_{version}"


def active_design() -> SimulationInput:
    """Return the current working design, initialising it if necessary."""

    initialize_design_workspace()
    return st.session_state[ACTIVE_DESIGN_KEY]


def _serialized(inputs: SimulationInput) -> dict[str, object]:
    return design_input_to_dict(inputs)


def _same_design(left: SimulationInput | None, right: SimulationInput | None) -> bool:
    if left is None or right is None:
        return left is right
    return _serialized(left) == _serialized(right)


def _history() -> list[SimulationInput]:
    return st.session_state.setdefault(DESIGN_HISTORY_KEY, [])


def _redo_history() -> list[SimulationInput]:
    return st.session_state.setdefault(REDO_HISTORY_KEY, [])


def _push_history(inputs: SimulationInput) -> None:
    history = _history()
    history.append(inputs)
    if len(history) > MAX_HISTORY:
        del history[:-MAX_HISTORY]


def _bump_widget_version() -> None:
    st.session_state[DESIGN_VERSION_KEY] = int(st.session_state.get(DESIGN_VERSION_KEY, 0)) + 1


def get_design_store() -> DesignStore | None:
    """Return the local SQLite store, or None if it cannot be opened."""

    store = st.session_state.get(DESIGN_STORE_KEY)
    if isinstance(store, DesignStore):
        return store

    try:
        store = DesignStore()
    except OSError as error:
        st.warning(f"Local design database is not available: {error}")
        return None

    st.session_state[DESIGN_STORE_KEY] = store
    return store


def initialize_design_workspace() -> None:
    """Load the autosaved design once per Streamlit session."""

    st.session_state.setdefault(DESIGN_HISTORY_KEY, [])
    st.session_state.setdefault(REDO_HISTORY_KEY, [])
    st.session_state.setdefault(DESIGN_VERSION_KEY, 0)
    st.session_state.setdefault(WORKSPACE_NAME_KEY, DEFAULT_DESIGN_NAME)

    if ACTIVE_DESIGN_KEY in st.session_state:
        return

    store = get_design_store()
    saved_design = store.load_current_design() if store else None
    st.session_state[ACTIVE_DESIGN_KEY] = saved_design or default_design_input()


def _set_active_design(
    inputs: SimulationInput,
    *,
    add_history: bool = True,
    refresh_widgets: bool = True,
) -> None:
    current = st.session_state.get(ACTIVE_DESIGN_KEY)
    if add_history and current is not None and not _same_design(current, inputs):
        _push_history(current)
        st.session_state[REDO_HISTORY_KEY] = []
    st.session_state[ACTIVE_DESIGN_KEY] = inputs
    if refresh_widgets:
        _bump_widget_version()


def record_design_snapshot(inputs: SimulationInput) -> None:
    """Record user-edited widget values into the undo history."""

    initialize_design_workspace()
    current = st.session_state.get(ACTIVE_DESIGN_KEY)
    if _same_design(current, inputs):
        return
    if current is not None:
        _push_history(current)
        st.session_state[REDO_HISTORY_KEY] = []
    st.session_state[ACTIVE_DESIGN_KEY] = inputs


def autosave_current_design(inputs: SimulationInput, store: DesignStore | None = None) -> None:
    """Persist the current design to the local SQLite database."""

    store = store or get_design_store()
    if store is None:
        return
    try:
        store.autosave_current(inputs)
    except OSError as error:
        st.warning(f"Could not autosave design: {error}")


def _undo() -> None:
    history = _history()
    if not history:
        return
    current = st.session_state.get(ACTIVE_DESIGN_KEY)
    previous = history.pop()
    if current is not None:
        _redo_history().append(current)
    st.session_state[ACTIVE_DESIGN_KEY] = previous
    _bump_widget_version()


def _redo() -> None:
    redo_history = _redo_history()
    if not redo_history:
        return
    current = st.session_state.get(ACTIVE_DESIGN_KEY)
    next_design = redo_history.pop()
    if current is not None:
        _push_history(current)
    st.session_state[ACTIVE_DESIGN_KEY] = next_design
    _bump_widget_version()


def current_design_name() -> str:
    """Return the current user-facing design name."""

    name = str(st.session_state.get(WORKSPACE_NAME_KEY, DEFAULT_DESIGN_NAME)).strip()
    return name or DEFAULT_DESIGN_NAME


def render_design_workspace() -> DesignStore | None:
    """Render local persistence and preset controls."""

    initialize_design_workspace()
    store = get_design_store()

    st.subheader("Design workspace")
    st.caption(
        "Autosaves to a local SQLite database on this computer. "
        "Use Undo/Redo for simulator changes; browser Command+Z does not reliably undo widgets."
    )

    undo_col, redo_col, reset_col = st.columns(3)
    with undo_col:
        if st.button("Undo last change", disabled=not bool(_history()), width="stretch"):
            _undo()
            st.rerun()
    with redo_col:
        if st.button("Redo", disabled=not bool(_redo_history()), width="stretch"):
            _redo()
            st.rerun()
    with reset_col:
        if st.button("Reset to default", width="stretch"):
            _set_active_design(default_design_input())
            st.rerun()

    save_col, load_col, preset_col = st.columns(3)
    with save_col:
        st.text_input("Workspace design name", key=WORKSPACE_NAME_KEY)
        if st.button("Save design", width="stretch"):
            if store is None:
                st.warning("Local design database is not available.")
            else:
                store.save_named_design(current_design_name(), active_design())
                st.success(f"Saved '{current_design_name()}'.")

    with load_col:
        saved_names = store.list_design_names() if store else []
        selected_name = st.selectbox(
            "Saved design",
            saved_names or ["No saved designs yet"],
            disabled=not bool(saved_names),
        )
        if st.button("Load design", disabled=not bool(saved_names), width="stretch"):
            loaded = store.load_named_design(selected_name) if store else None
            if loaded is None:
                st.warning("Saved design was not found.")
            else:
                st.session_state[WORKSPACE_NAME_KEY] = selected_name
                _set_active_design(loaded)
                st.rerun()

    with preset_col:
        presets = blade_preset_options()
        preset_names = [preset.name for preset in presets]
        selected_preset_name = st.selectbox("Blade preset", preset_names)
        selected_preset = get_blade_preset(selected_preset_name)
        st.caption(selected_preset.description)
        if st.button("Load preset", width="stretch"):
            st.session_state[WORKSPACE_NAME_KEY] = selected_preset.name
            _set_active_design(preset_to_simulation_input(selected_preset))
            st.rerun()

    return store
