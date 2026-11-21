"""Estimate aerodynamic torque at a specified rotor speed."""

from math import pi

from windlab.bemt import calculate_bemt_lite
from windlab.materials import get_material, get_surface_finish
from windlab.models import SimulationInput


def aerodynamic_torque(inputs: SimulationInput, rpm: float) -> float:
    omega = max(rpm, 0.001) * 2 * pi / 60
    material_roughness = (
        inputs.custom_material_roughness_factor
        if inputs.use_custom_material_properties
        else get_material(inputs.material).roughness_factor
    )
    roughness = (
        material_roughness * get_surface_finish(inputs.surface_finish).drag_factor
        if inputs.use_material_roughness
        else 1.0
    )
    result = calculate_bemt_lite(
        inputs,
        tip_speed_ratio=omega * inputs.rotor_radius_m / inputs.wind_speed_m_s,
        material_roughness_factor=roughness,
        airfoil_efficiency_multiplier=inputs.airfoil_efficiency_multiplier,
        use_airfoil_correction=inputs.use_airfoil_correction,
        use_reynolds_correction=inputs.use_reynolds_correction,
        practical_cp_limit=inputs.practical_cp_limit,
        use_practical_cp_limit=inputs.use_practical_cp_limit,
        use_prandtl_loss=inputs.use_prandtl_loss,
    )
    return result.mechanical_power_w / omega
