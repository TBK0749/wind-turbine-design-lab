import pytest

from app.components.input_panel import _competition_section_frame
from windlab.blade_geometry import competition_50cm_sections
from windlab.models import BladeSection, SimulationInput
from windlab.simulator import simulate


def test_competition_sections_include_naca_airfoils_and_roles() -> None:
    sections = competition_50cm_sections()

    assert sections[0].position_m == pytest.approx(0.05)
    assert sections[0].chord_m == pytest.approx(0.085)
    assert sections[0].airfoil_name == "NACA 4418"
    assert "Root strength" in sections[0].airfoil_role
    assert sections[-1].position_m == pytest.approx(0.45)
    assert sections[-1].airfoil_name == "NACA 2412"
    assert "Tip vortex" in sections[-1].airfoil_role


def test_section_table_frame_exposes_airfoil_columns() -> None:
    frame = _competition_section_frame()

    assert "Airfoil" in frame.columns
    assert "Airfoil role / purpose" in frame.columns
    assert frame.loc[0, "Airfoil"] == "NACA 4418"


def test_hub_can_cover_inner_fabrication_section_without_validation_error() -> None:
    inputs = SimulationInput(
        rotor_radius_m=0.45,
        hub_radius_m=0.10,
        blade_sections=competition_50cm_sections(),
    )

    result = simulate(inputs)

    assert result.rpm > 0.0
    assert result.representative_airfoil_name in {"NACA 4412", "NACA 4415", "NACA 2412"}


def test_unknown_section_airfoil_is_rejected() -> None:
    with pytest.raises(ValueError, match="Section airfoil"):
        BladeSection(
            position_m=0.10,
            chord_m=0.05,
            twist_angle_deg=10.0,
            airfoil_name="Magic airfoil",
        )


def test_section_airfoils_override_global_airfoil_family() -> None:
    result = simulate(
        SimulationInput(
            rotor_radius_m=0.45,
            hub_radius_m=0.10,
            blade_sections=competition_50cm_sections(),
            airfoil_type="Flat plate / Foam board",
        )
    )

    assert result.representative_airfoil_family != "Flat plate / Foam board"
    assert result.airfoil_efficiency_factor > 0.70


def _with_section_airfoil(section_index: int, airfoil_name: str) -> tuple[BladeSection, ...]:
    sections = list(competition_50cm_sections())
    section = sections[section_index]
    sections[section_index] = section.model_copy(update={"airfoil_name": airfoil_name})
    return tuple(sections)


def test_root_section_airfoil_affects_efficiency() -> None:
    baseline = simulate(
        SimulationInput(
            rotor_radius_m=0.45,
            hub_radius_m=0.10,
            blade_sections=competition_50cm_sections(),
        )
    )
    root_flat = simulate(
        SimulationInput(
            rotor_radius_m=0.45,
            hub_radius_m=0.10,
            blade_sections=_with_section_airfoil(0, "Flat plate"),
        )
    )

    assert root_flat.airfoil_efficiency_factor < baseline.airfoil_efficiency_factor
    assert root_flat.electrical_power_mw < baseline.electrical_power_mw


def test_tip_section_airfoil_affects_rpm() -> None:
    baseline = simulate(
        SimulationInput(
            rotor_radius_m=0.45,
            hub_radius_m=0.10,
            blade_sections=competition_50cm_sections(),
        )
    )
    draggy_tip = simulate(
        SimulationInput(
            rotor_radius_m=0.45,
            hub_radius_m=0.10,
            blade_sections=_with_section_airfoil(5, "Flat plate"),
        )
    )

    assert draggy_tip.rpm < baseline.rpm
    assert draggy_tip.electrical_power_mw < baseline.electrical_power_mw
