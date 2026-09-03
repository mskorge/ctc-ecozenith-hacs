"""ctc-ecozenith - read and control a CTC EcoZenith i360 over the BMS Modbus interface.

An asynchronous, transport-independent library. It does not open the Modbus
connection itself: build a :class:`modbus_connection.ModbusUnit` with any backend
``modbus-connection`` supports and hand it to :class:`CtcEcoZenith`.
"""

from __future__ import annotations

from .alarms import Alarms, AlarmSnapshot, CtcAlarm, CtcInfoText
from .control_parameters import (
    HS_SETPOINT_MAX,
    HS_SETPOINT_MIN,
    SETPOINT_STEP,
    ControlParameters,
)
from .device import (
    MANUFACTURER,
    MODEL,
    PROBE_REGISTER,
    PRODUCT_TYPE,
    CtcEcoZenith,
    DeviceInformation,
    software_version,
)
from .enums import (
    DhwMode,
    ElPriceMode,
    HeatingSystemStatus,
    HeatPumpStatus,
    ShuntState,
    SystemStatus,
    ZoneMode,
)
from .exceptions import CtcError, CtcValueError
from .readings import Readings
from .settings import Settings

__all__ = [
    "HS_SETPOINT_MAX",
    "HS_SETPOINT_MIN",
    "MANUFACTURER",
    "MODEL",
    "PRODUCT_TYPE",
    "PROBE_REGISTER",
    "SETPOINT_STEP",
    "AlarmSnapshot",
    "Alarms",
    "ControlParameters",
    "CtcAlarm",
    "CtcEcoZenith",
    "CtcError",
    "CtcInfoText",
    "CtcValueError",
    "DeviceInformation",
    "DhwMode",
    "ElPriceMode",
    "HeatPumpStatus",
    "HeatingSystemStatus",
    "Readings",
    "Settings",
    "ShuntState",
    "SystemStatus",
    "ZoneMode",
    "software_version",
]
