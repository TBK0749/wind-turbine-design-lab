"""Simplified DC generator and electrical-load model for competition use."""

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True, slots=True)
class GeneratorResult:
    """Electrical operating point for a resistive competition load."""

    unloaded_generator_rpm: float
    generator_rpm: float
    generator_load_factor: float
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
    cap_output_by_mechanical_power: bool = True,
    apply_load_feedback: bool = True,
) -> GeneratorResult:
    """Estimate electrical output from a DC generator and resistive load.

    The open-circuit voltage scales linearly with generator RPM. Current follows
    the generator's internal resistance plus the external load. Output is capped
    by the mechanical power available after the stated conversion efficiency.
    When load feedback is enabled, an overloaded resistive demand reduces the
    operating generator RPM enough for the ideal load power to match the cap.
    """

    unloaded_generator_rpm = rotor_rpm * gear_ratio
    generator_rpm = unloaded_generator_rpm
    open_circuit_voltage = volts_per_1000_rpm * generator_rpm / 1000.0
    total_resistance = internal_resistance_ohm + load_resistance_ohm
    ideal_current_a = open_circuit_voltage / total_resistance
    ideal_load_power_w = ideal_current_a**2 * load_resistance_ohm
    maximum_electrical_power_w = mechanical_power_w * efficiency_percent / 100.0
    generator_load_factor = 1.0

    if (
        apply_load_feedback
        and cap_output_by_mechanical_power
        and ideal_load_power_w > maximum_electrical_power_w
        and ideal_load_power_w > 0.0
    ):
        generator_load_factor = sqrt(maximum_electrical_power_w / ideal_load_power_w)
        generator_rpm = unloaded_generator_rpm * generator_load_factor
        open_circuit_voltage = volts_per_1000_rpm * generator_rpm / 1000.0
        ideal_current_a = open_circuit_voltage / total_resistance
        ideal_load_power_w = ideal_current_a**2 * load_resistance_ohm

    electrical_power_w = min(ideal_load_power_w, maximum_electrical_power_w)
    if not cap_output_by_mechanical_power:
        electrical_power_w = ideal_load_power_w

    load_current_a = sqrt(electrical_power_w / load_resistance_ohm)
    load_voltage = load_current_a * load_resistance_ohm
    conversion_efficiency = (
        100.0 * electrical_power_w / mechanical_power_w if mechanical_power_w > 0.0 else 0.0
    )

    return GeneratorResult(
        unloaded_generator_rpm=unloaded_generator_rpm,
        generator_rpm=generator_rpm,
        generator_load_factor=generator_load_factor,
        open_circuit_voltage_v=open_circuit_voltage,
        load_voltage_v=load_voltage,
        load_current_ma=load_current_a * 1000.0,
        electrical_power_mw=electrical_power_w * 1000.0,
        electrical_energy_mj=electrical_power_w * trial_duration_s * 1000.0,
        conversion_efficiency_percent=conversion_efficiency,
    )
