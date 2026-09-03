"""The CTC EcoZenith i360 custom integration.

This build owns its Modbus connection (via the vendored ``tmodbus`` backend)
instead of borrowing one from the core ``modbus`` integration, so it works on a
stand-alone HACS install with no extra configuration. The connection opens
lazily on the first read and reconnects on its own; the entry is never reloaded
when the link drops.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_HOST, CONF_PORT, Platform

from .api import CtcApiClient, build_connection
from .const import CONF_UNIT
from .coordinator import CtcDataUpdateCoordinator
from .data import CtcData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import CtcConfigEntry

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.WATER_HEATER,
]


async def async_setup_entry(hass: HomeAssistant, entry: CtcConfigEntry) -> bool:
    """Set up CTC EcoZenith i360 from a config entry."""
    connection = build_connection(entry.data[CONF_HOST], entry.data[CONF_PORT])
    entry.async_on_unload(connection.close)

    client = CtcApiClient(connection, entry.data[CONF_UNIT])
    coordinator = CtcDataUpdateCoordinator(hass, entry, client)
    entry.runtime_data = CtcData(
        client=client, connection=connection, coordinator=coordinator
    )

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CtcConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
