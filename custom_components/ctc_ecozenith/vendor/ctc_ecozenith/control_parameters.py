"""The volatile 1000-series "Control parameters".

These holding registers are the manufacturer's sanctioned way to *actively*
drive the installation: they carry no write-cycle penalty, but the controller
resets each one to "no override" if it is not re-written within five minutes
(and on every controller restart). The re-assertion loop lives in the consumer
(e.g. a Home Assistant coordinator), not here.

Reads of this range are unreliable (the registers are documented write-only), so
this component is **never pooled** into the device's read group - it exists only
to dispatch validated writes.
"""

from __future__ import annotations

from modbus_connection.model import Component, enum, gauge

from ._fields import ranged
from .enums import DhwMode, ElPriceMode, ZoneMode

__all__ = [
    "HS_SETPOINT_MAX",
    "HS_SETPOINT_MIN",
    "SETPOINT_STEP",
    "ControlParameters",
]

# Heating-circuit room-temperature setpoint bounds, degrees Celsius. These are a
# generous sanity envelope for the UI dial and the write validator - NOT the
# controller's real limits. Per unit, those are reported by the read-only helper
# registers for setting 61509 (60027 = max, 60028 = min, 60029 = step, each x0.1);
# widen these to match once read from a real i360H. 1010 is a volatile register
# with no write-cycle cost, so the controller clamps a borderline value anyway.
HS_SETPOINT_MIN = 5.0
HS_SETPOINT_MAX = 40.0
SETPOINT_STEP = 0.5


class ControlParameters(Component):
    """Write-only control parameters. Not part of the pooled read group."""

    register_space = "holding"

    # 1005 ElPriceMode: 1 = Low, 2 = Normal, 3 = High.
    el_price_mode = enum(1005, ElPriceMode, writable=True)
    # 1007 DHW Mode: 0 = Economy, 1 = Normal, 2 = Comfort.
    dhw_mode = enum(1007, DhwMode, writable=True)
    # 1010 Setpoint heat HC1, degrees Celsius (Factor 0,1).
    hs1_room_setpoint = gauge(
        1010, 0.1, signed=True, writable=ranged(HS_SETPOINT_MIN, HS_SETPOINT_MAX)
    )
    # 1015 Zone mode HC1: 0 = Off, 1 = Heat, 2 = Cool, 3 = Auto, 4 = On.
    hs1_zone_mode = enum(1015, ZoneMode, writable=True)
