"""User settings from the 61500 holding-register block.

These registers are read/write on the controller, but the CTC BMS manual warns
of a hard write-cycle limit on the 60000/61500 range, so this library exposes
them **read-only**. Frequently-changed values have safe equivalents in the
volatile 1000-series (see :mod:`ctc_ecozenith.control_parameters`).

Addresses are the BMS register number verbatim (base offset 0).
"""

from __future__ import annotations

from modbus_connection.model import Component, enum, gauge, integer

from ._fields import temperature
from .enums import DhwMode

__all__ = ["Settings"]


class Settings(Component):
    """The 61500-block user settings. Read-only in this library."""

    register_space = "holding"
    # A strict subset of the 61500 + 100 window the reference Node-RED flow reads
    # successfully on the real unit.
    register_ranges = ((61500, 61570),)
    # CTC caps a Modbus transfer at 100 registers; every ComponentGroup member
    # must agree on this value.
    max_span = 100

    dhw_mode = enum(61500, DhwMode)  # 0 = Economy, 1 = Normal, 2 = Comfort
    dhw_manual_stop_temperature = temperature(61501)
    dhw_outlet_setpoint = temperature(61502)
    # Factor 0,5 -> hours of extra-DHW runtime.
    extra_dhw_timer = gauge(61503, 0.5, signed=True, unit="h")
    heating_max_time = integer(61504, unit="min")
    dhw_max_time = integer(61505, unit="min")
    vacation_days = integer(61508, unit="d")
    hs1_room_setpoint = temperature(61509)
    hs1_inclination = gauge(61513, 0.1, signed=True)  # heat-curve slope
    hs1_adjustment = gauge(61517, 0.1, signed=True)  # heat-curve offset
    radiator_pump_setting = integer(61570, unit="%")
