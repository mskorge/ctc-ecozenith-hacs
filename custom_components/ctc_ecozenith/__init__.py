"""The CTC EcoZenith i360 custom integration.

The Modbus unit comes from the core ``modbus`` integration's shared connections
(:func:`homeassistant.components.modbus.async_get_unit`), so anything else
talking to the same CTC address shares one link instead of competing for it. No
``modbus:`` YAML is needed. The connection opens lazily on the first read and
reconnects on its own; the entry is never reloaded when the link drops.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.modbus import async_get_unit
from homeassistant.const import CONF_HOST, CONF_PORT, Platform

from .api import CtcApiClient, tcp_params
from .const import CONF_UNIT
from .coordinator import CtcDataUpdateCoordinator
from .data import CtcData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import CtcConfigEntry

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.WATER_HEATER,
]


async def async_setup_entry(hass: HomeAssistant, entry: CtcConfigEntry) -> bool:
    """Set up CTC EcoZenith i360 from a config entry."""
    # The hold on the shared connection is released when the entry unloads.
    unit = async_get_unit(
        hass,
        entry,
        tcp_params(entry.data[CONF_HOST], entry.data[CONF_PORT]),
        entry.data[CONF_UNIT],
    )

    client = CtcApiClient(unit)
    coordinator = CtcDataUpdateCoordinator(hass, entry, client)
    entry.runtime_data = CtcData(client=client, unit=unit, coordinator=coordinator)

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CtcConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
