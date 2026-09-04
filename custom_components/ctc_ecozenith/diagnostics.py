"""Diagnostics support for the CTC EcoZenith i360 custom integration."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST

from .api import LIBRARY_VERSION

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import CtcConfigEntry

TO_REDACT = {CONF_HOST}


def _describe(value: Any) -> Any:
    """Render a held override value for the dump (enum -> its lowercase name)."""
    return value.name.lower() if isinstance(value, Enum) else value


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: CtcConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = entry.runtime_data
    coordinator = data.coordinator
    alarms = coordinator.alarms
    readings = coordinator.device.readings
    return {
        "vendored_library_version": LIBRARY_VERSION,
        "entry_data": async_redact_data(entry.data, TO_REDACT),
        "alarms": {
            "codes": [f"E{alarm.code}" for alarm in alarms.alarms],
            "heat_pump": [alarm.heat_pump for alarm in alarms.alarms],
            "info_texts": [f"I{info.code}" for info in alarms.infos],
        },
        "control_overrides": {
            f"{component}.{field}": _describe(value)
            for (component, field), value in coordinator.overrides.items()
        },
        "keepalive_active": coordinator.keepalive_active,
        "elspot": {
            "sg_mode": _describe(readings.sg_mode),
            "price_amount_62302": readings.elspot_price_amount,
            "price_fraction_62303": readings.elspot_price_fraction,
            "price": readings.elspot_price,
            "price_mode_select_available": coordinator.elspot_price_available,
        },
        "raw": await coordinator.device.async_read_raw(),
    }
