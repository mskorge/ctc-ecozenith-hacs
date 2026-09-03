"""Runtime data types for the CTC EcoZenith i360 custom integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from modbus_connection.tmodbus import ModbusConnection

    from .api import CtcApiClient
    from .coordinator import CtcDataUpdateCoordinator

type CtcConfigEntry = ConfigEntry[CtcData]


@dataclass
class CtcData:
    """Data held on a loaded CTC EcoZenith config entry."""

    client: CtcApiClient
    connection: ModbusConnection
    coordinator: CtcDataUpdateCoordinator
