"""Live measurements from the 62000-62399 holding-register range.

Everything here is read-only. Addresses are the BMS register number verbatim
(base offset 0). Each declared range in :attr:`Readings.register_ranges` is a
strict subset of a 100-register window the reference Node-RED flow reads
successfully on the real unit, so no per-unit register scan is needed to poll
them; anything added *outside* those windows does need one first.
"""

from __future__ import annotations

from modbus_connection.model import Component, enum, integer

from ._fields import centi, temperature
from .enums import HeatPumpStatus, ShuntState, SystemStatus

__all__ = ["Readings"]


class Readings(Component):
    """Live sensor values. Everything here is read-only."""

    register_space = "holding"
    # Proven-safe windows (subsets of the flow's 62000/62100/62200/62300 blocks).
    register_ranges = (
        (62000, 62047),
        (62107, 62193),
        (62203, 62291),
        (62304, 62331),
    )
    max_span = 100

    # --- 62000 window -----------------------------------------------------
    outdoor_temperature = temperature(62000)
    dhw_stop_temperature = temperature(62001)
    # Manual Factor for 62002 is "1", but its neighbours 62001/62003 and the
    # matching setpoint 61502 are all Factor 0,1; the reference flow scales this
    # by 0.1 too. Treat the manual as a typo. Verify live against 61502.
    dhw_outlet_setpoint = temperature(62002)
    dhw_temperature = temperature(62003)
    system_status = enum(62005, SystemStatus)
    radiator_water_temperature = temperature(62006)
    hs1_primary_flow_setpoint = temperature(62007)
    hs1_primary_flow_temperature = temperature(62011)
    return_temperature = temperature(62015)
    # 0/1 on the reference unit; a sibling pump reg (62323) is documented 0-100,
    # so model raw and let the consumer threshold it.
    dhw_circulation = integer(62016, signed=False)
    hp1_status = enum(62017, HeatPumpStatus)
    hp1_supply_temperature = temperature(62027)  # "HP in"
    hp1_return_temperature = temperature(62037)  # "HP out"
    hp1_discharge_temperature = temperature(62047)

    # --- 62100 window ---------------------------------------------------------
    hp1_outdoor_temperature = temperature(62147)
    immersion_heater_power = centi(62168, unit="kW")
    hp1_current_rps = centi(62193, unit="rps")  # revolutions per second, not rpm
    hp1_charge_pump = centi(62107, unit="%")
    hp1_brine_pump = centi(62117, unit="%")
    hp1_fan = centi(62127, unit="%")
    degree_minutes = centi(62167)  # signed; not a duration

    # --- 62200 window ------------------------------------------------------
    hs1_room_temperature = temperature(62203)
    # Display software version, split across two registers (encoding per the
    # manual: 62244 = month/day, 62245 = year). Surfaced for diagnostics /
    # device-info; the exact packing is unverified against a real i360H.
    display_sw_version_date = integer(62244, signed=False)
    display_sw_version_year = integer(62245, signed=False)
    dhw_lower_tank_setpoint = temperature(62274)
    dhw_lower_temperature = temperature(62275)
    dhw_upper_temperature = temperature(62276)
    dhw_capacity = centi(62279, unit="%", signed=False)
    hp1_primary_flow = centi(62291, unit="L/min")

    # --- 62300 window ---------------------------------------------------------
    radiator_pump = integer(62304, signed=False)  # 0/1 on the reference unit
    hs1_shunt_state = enum(62308, ShuntState)
    hp1_power = centi(62331, unit="kW", signed=False)
