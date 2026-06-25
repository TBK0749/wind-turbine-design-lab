"""Simplified DC generator and electrical-load model for competition use."""

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True, slots=True)
class GeneratorResult:
    """Electrical operating point for a resistive competition load."""

    generator_rpm: float
    open_circuit_voltage_v: float
    load_voltage_v: float
    load_current_ma: float
    electrical_power_mw: float
    electrical_energy_mj: float
    conversion_efficiency_percent: float


def simulate_generator(
    *,
    rotor_rpm: float,
    mechanical_power_w: float,
    volts_per_1000_rpm: float,
    internal_resistance_ohm: float,
    load_resistance_ohm: float,
    efficiency_percent: float,
    gear_ratio: float,
    trial_duration_s: float,
) -> GeneratorResult:
    """Estimate electrical output from a DC generator and resistive load.

    The open-circuit voltage scales linearly with generator RPM. Current follows
    the generator's internal resistance plus the external load. Output is capped
    by the mechanical power available after the stated conversion efficiency.
    """

    generator_rpm = rotor_rpm * gear_ratio
    open_circuit_voltage = volts_per_1000_rpm * generator_rpm / 1000.0
    total_resistance = internal_resistance_ohm + load_resistance_ohm
    ideal_current_a = open_circuit_voltage / total_resistance
    ideal_load_power_w = ideal_current_a**2 * load_resistance_ohm
    maximum_electrical_power_w = mechanical_power_w * efficiency_percent / 100.0
    electrical_power_w = min(ideal_load_power_w, maximum_electrical_power_w)

    load_current_a = sqrt(electrical_power_w / load_resistance_ohm)
    load_voltage = load_current_a * load_resistance_ohm
    conversion_efficiency = (
        100.0 * electrical_power_w / mechanical_power_w if mechanical_power_w > 0.0 else 0.0
    )

    return GeneratorResult(
        generator_rpm=generator_rpm,
        open_circuit_voltage_v=open_circuit_voltage,
        load_voltage_v=load_voltage,
        load_current_ma=load_current_a * 1000.0,
        electrical_power_mw=electrical_power_w * 1000.0,
        electrical_energy_mj=electrical_power_w * trial_duration_s * 1000.0,
        conversion_efficiency_percent=conversion_efficiency,
    )
