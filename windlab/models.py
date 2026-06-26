"""Validated input and output models."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from windlab.airfoils import AIRFOIL_LIBRARY
from windlab.materials import MATERIALS


class BladeSection(BaseModel):
    """Geometry measured at one radial station along a blade."""

    model_config = ConfigDict(frozen=True)

    position_m: float = Field(gt=0.0, le=100.0)
    chord_m: float = Field(gt=0.001, le=10.0)
    twist_angle_deg: float = Field(ge=-20.0, le=60.0)


class SimulationInput(BaseModel):
    """User-controlled parameters for one educational simulation."""

    model_config = ConfigDict(frozen=True)

    wind_speed_m_s: float = Field(8.0, ge=0.5, le=40.0)
    air_density_kg_m3: float = Field(1.225, gt=0.5, le=1.5)
    rotor_radius_m: float = Field(1.0, gt=0.05, le=100.0)
    hub_radius_m: float = Field(0.1, ge=0.0, le=20.0)
    blade_count: int = Field(3, ge=1, le=12)
    root_chord_m: float = Field(0.18, gt=0.01, le=10.0)
    tip_chord_m: float = Field(0.08, gt=0.005, le=10.0)
    pitch_angle_deg: float = Field(4.0, ge=-10.0, le=35.0)
    twist_angle_deg: float = Field(12.0, ge=0.0, le=45.0)
    blade_sections: tuple[BladeSection, ...] = ()
    airfoil_type: str = Field("Flat plate / Foam board")
    blade_mass_kg: float = Field(1.0, gt=0.01, le=10000.0)
    material: str = Field("Wood")
    use_custom_material_properties: bool = False
    custom_material_density_kg_m3: float = Field(650.0, gt=1.0, le=30000.0)
    custom_material_roughness_factor: float = Field(0.94, ge=0.1, le=1.5)
    custom_material_durability_factor: float = Field(0.70, ge=0.0, le=1.0)
    use_estimated_blade_mass: bool = False
    blade_thickness_m: float = Field(0.005, gt=0.0001, le=0.5)
    generator_volts_per_1000_rpm: float = Field(1.5, gt=0.01, le=100.0)
    generator_internal_resistance_ohm: float = Field(20.0, ge=0.0, le=10000.0)
    load_resistance_ohm: float = Field(100.0, gt=0.01, le=1000000.0)
    generator_efficiency_percent: float = Field(70.0, gt=0.0, le=100.0)
    gear_ratio: float = Field(1.0, gt=0.01, le=100.0)
    trial_duration_s: float = Field(60.0, gt=0.0, le=86400.0)
    air_dynamic_viscosity_kg_m_s: float = Field(1.81e-5, gt=1e-6, le=1e-4)
    practical_cp_limit: float = Field(0.50, ge=0.05, le=0.592)
    airfoil_efficiency_multiplier: float = Field(1.0, ge=0.1, le=2.0)
    mechanical_loss_percent: float = Field(0.0, ge=0.0, le=95.0)
    startup_torque_n_m: float = Field(0.0, ge=0.0, le=10000.0)
    use_hub_area_loss: bool = True
    use_airfoil_correction: bool = True
    use_material_roughness: bool = True
    use_generator_power_cap: bool = True
    use_practical_cp_limit: bool = True
    use_reynolds_correction: bool = True
    use_startup_torque_loss: bool = True

    @model_validator(mode="after")
    def validate_geometry(self) -> "SimulationInput":
        """Validate relationships that individual field limits cannot express."""

        if self.hub_radius_m >= self.rotor_radius_m:
            raise ValueError("Hub radius must be smaller than rotor radius.")
        if self.material not in MATERIALS:
            raise ValueError(f"Material must be one of: {', '.join(MATERIALS)}.")
        if self.airfoil_type not in AIRFOIL_LIBRARY:
            raise ValueError(f"Airfoil must be one of: {', '.join(AIRFOIL_LIBRARY)}.")
        if self.blade_sections:
            if len(self.blade_sections) < 2:
                raise ValueError("Sectional geometry requires at least two blade sections.")
            positions = [section.position_m for section in self.blade_sections]
            if positions != sorted(positions) or len(positions) != len(set(positions)):
                raise ValueError("Blade section positions must be unique and increasing.")
            if positions[0] < self.hub_radius_m:
                raise ValueError("The first blade section cannot be inside the hub radius.")
            if positions[-1] > self.rotor_radius_m:
                raise ValueError("The final blade section cannot exceed the rotor radius.")
        return self


class SimulationResult(BaseModel):
    """Calculated performance values and student-facing feedback."""

    rotor_area_m2: float
    available_wind_power_w: float
    mechanical_power_w: float
    rpm: float
    torque_n_m: float
    cp: float
    tip_speed_ratio: float
    efficiency_percent: float
    effective_blade_mass_kg: float
    blade_planform_area_m2: float
    material_density_kg_m3: float
    design_score: float
    generator_rpm: float
    open_circuit_voltage_v: float
    load_voltage_v: float
    load_current_ma: float
    electrical_power_mw: float
    electrical_energy_mj: float
    conversion_efficiency_percent: float
    airfoil_lift_coefficient: float
    airfoil_drag_coefficient: float
    airfoil_lift_drag_ratio: float
    airfoil_efficiency_factor: float
    airfoil_angle_of_attack_deg: float
    airfoil_reynolds_number: float
    airfoil_stall_risk: bool
    recommendations: tuple[str, ...]
    warnings: tuple[str, ...] = ()
