"""Validated input and output models."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from windlab.materials import MATERIALS


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
    blade_mass_kg: float = Field(1.0, gt=0.01, le=10000.0)
    material: str = Field("Wood")

    @model_validator(mode="after")
    def validate_geometry(self) -> "SimulationInput":
        """Validate relationships that individual field limits cannot express."""

        if self.hub_radius_m >= self.rotor_radius_m:
            raise ValueError("Hub radius must be smaller than rotor radius.")
        if self.material not in MATERIALS:
            raise ValueError(f"Material must be one of: {', '.join(MATERIALS)}.")
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
    design_score: float
    recommendations: tuple[str, ...]
    warnings: tuple[str, ...] = ()
