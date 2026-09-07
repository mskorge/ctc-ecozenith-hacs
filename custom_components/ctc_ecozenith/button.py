"""Button platform for the CTC EcoZenith i360 custom integration.

One button: **Release control** drops every held 1000-series "Control
parameter" override at once and stops the keep-alive. It writes nothing to
the unit - the controller reverts each parameter to its panel setting
within five minutes, and the panel's "[I048] Extern styrning" clears with
it *if Home Assistant was the only external controller* (a bound myUpLink
cloud link or a wired SG Ready input keeps the message lit on its own).

It is a shortcut for setting the ``climate`` entity to ``AUTO``, the
``water_heater`` and ``select`` to ``auto`` and the Extra hot water
``switch`` off, one press instead of four.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory

from .entity import CtcEcoZenithEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CtcDataUpdateCoordinator
    from .data import CtcConfigEntry

PARALLEL_UPDATES = 0

_FIELD = "release_control"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CtcConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the CTC EcoZenith button entities."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([CtcReleaseControlButton(coordinator)])


class CtcReleaseControlButton(CtcEcoZenithEntity, ButtonEntity):
    """Release every held control-parameter override (control parameters 1005-1015)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = _FIELD

    def __init__(self, coordinator: CtcDataUpdateCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator, _FIELD)

    @property
    def available(self) -> bool:
        """Always available - releasing local overrides needs no device I/O.

        Handing control back is exactly what you want while the link is
        down and the keep-alive is retrying, so this must not gate on the
        coordinator's last update succeeding.
        """
        return True

    async def async_press(self) -> None:
        """Release every held override and stop the keep-alive."""
        await self.coordinator.async_release_all()
