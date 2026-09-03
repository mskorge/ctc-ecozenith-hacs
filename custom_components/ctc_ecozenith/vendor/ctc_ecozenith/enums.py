"""Enumerations for decoded register values.

Meanings come from the ``Function`` column of the CTC BMS register document
(doc 16260016) cross-checked against the Node-RED status-map functions in the
reference installation. An unknown raw code decodes to ``None``.
"""

from __future__ import annotations

from enum import IntEnum

__all__ = [
    "DhwMode",
    "ElPriceMode",
    "HeatPumpStatus",
    "HeatingSystemStatus",
    "ShuntState",
    "SystemStatus",
    "ZoneMode",
]


class SystemStatus(IntEnum):
    """Overall operating state of the installation (register 62005 ``sStatus``)."""

    HP_UPPER = 0
    HP_LOWER = 1
    ADD = 2
    HP_ADD = 3
    HC = 4
    DHW = 5
    POOL = 6
    OFF = 7
    HEATING_MIX = 8
    WOOD = 9
    DHW_HC = 10
    COOLING = 11
    SWAP = 12  # documented in the manual; missing from the Node-RED map


class HeatPumpStatus(IntEnum):
    """State of heat pump 1 / A1 (register 62017 ``hp1Status``)."""

    START_DELAY = 0  # compressor off, start delay
    READY_TO_START = 1  # compressor off, ready to start
    WAIT_FOR_FLOW = 2  # compressor wait until flow
    HEATING = 3  # compressor on, heating
    DEFROST = 4  # defrost active
    COOLING = 5  # compressor on, cooling
    BLOCKED = 6  # compressor off, blocked
    ALARM = 7  # compressor off, alarm
    FUNCTION_TEST = 8
    NOT_DEFINED = 30  # HP not defined
    COMPRESSOR_NOT_ENABLED = 31
    COMMUNICATION_ERROR = 32
    CHARGE_DHW = 33


class ShuntState(IntEnum):
    """Mixing-valve shunt state (register 62308 ``Heating system 1: Shunt state``)."""

    CLOSED = 0
    INACTIVE = 1
    OPEN = 2


class HeatingSystemStatus(IntEnum):
    """Heating-circuit 1 mode (register 62246 ``hs1Status``)."""

    HEATING_OFF = 0
    VACATION = 1
    NIGHT_REDUCTION = 2
    ON = 3  # on, normal mode


class DhwMode(IntEnum):
    """Domestic-hot-water comfort mode.

    Read back from settings register 61500 (``sDHWMode``); driven safely through
    control parameter 1007 (``DHW Mode``).
    """

    ECONOMY = 0
    NORMAL = 1
    COMFORT = 2


class ZoneMode(IntEnum):
    """Heating-circuit zone mode, driven through control parameters 1015 / 1016."""

    OFF = 0
    HEAT = 1
    COOL = 2
    AUTO = 3
    ON = 4


class ElPriceMode(IntEnum):
    """Electricity-price mode (control parameter 1005 ``ElPriceMode``)."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
