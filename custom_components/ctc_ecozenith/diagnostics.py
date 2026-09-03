"""Diagnostics support for the CTC EcoZenith i360 custom integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST

from .api import LIBRARY_VERSION

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import CtcConfigEntry

TO_REDACT = {CONF_HOST}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: CtcConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = entry.runtime_data
    alarms = data.coordinator.alarms
    return {
        "vendored_library_version": LIBRARY_VERSION,
        "entry_data": async_redact_data(entry.data, TO_REDACT),
        "alarms": {
            "codes": [f"E{alarm.code}" for alarm in alarms.alarms],
            "heat_pump": [alarm.heat_pump for alarm in alarms.alarms],
            "info_texts": [f"I{info.code}" for info in alarms.infos],
        },
        "raw": await data.client.device.async_read_raw(),
    }
