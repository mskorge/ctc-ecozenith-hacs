"""Select platform for the CTC EcoZenith i360 custom integration.

One select: ``el_price_mode`` drives control parameter 1005. Its first option,
``auto``, releases the override and lets the controller's own logic decide;
picking a real mode asserts it and the coordinator keeps re-writing it.

The select is offered as unavailable on a unit that has never reported a spot
electricity price (see ``coordinator.elspot_price_available``): control
parameter 1005 only does something when the controller is being fed a price,
and asserting it otherwise just lights "[I048] Extern styrning" on the panel
for five minutes before the controller drops it.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONTROL_PARAMETERS, DOMAIN
from .entity import CtcEcoZenithEntity
from .vendor.ctc_ecozenith import ElPriceMode

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CtcDataUpdateCoordinator
    from .data import CtcConfigEntry

PARALLEL_UPDATES = 0

_OPTION_AUTO = "auto"
_FIELD = "el_price_mode"
_OPTIONS = [_OPTION_AUTO, *(member.name.lower() for member in ElPriceMode)]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CtcConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the CTC EcoZenith select entities."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([CtcElPriceModeSelect(coordinator)])


class CtcElPriceModeSelect(CtcEcoZenithEntity, SelectEntity, RestoreEntity):
    """Electricity-price mode override (control parameter 1005)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = _FIELD
    _attr_options = _OPTIONS

    def __init__(self, coordinator: CtcDataUpdateCoordinator) -> None:
        """Initialize the select."""
        super().__init__(coordinator, _FIELD)

    @property
    def available(self) -> bool:
        """Unavailable until the unit reports a live spot price (latched)."""
        return super().available and self.coordinator.elspot_price_available

    @property
    def current_option(self) -> str:
        """Return the held override, or ``auto`` when none is asserted."""
        held = self.coordinator.held(CONTROL_PARAMETERS, _FIELD)
        if held is None:
            return _OPTION_AUTO
        return ElPriceMode(int(held)).name.lower()

    async def async_added_to_hass(self) -> None:
        """Re-assert a restored override so it survives a Home Assistant restart."""
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if (
            last is None
            or last.state in (None, _OPTION_AUTO, "unknown", "unavailable")
            or not self.coordinator.elspot_price_available
        ):
            return
        with suppress(HomeAssistantError, KeyError):
            await self.coordinator.async_write_control(
                CONTROL_PARAMETERS, _FIELD, ElPriceMode[last.state.upper()]
            )

    async def async_select_option(self, option: str) -> None:
        """Assert an electricity-price mode, or release the override for ``auto``."""
        try:
            if option == _OPTION_AUTO:
                await self.coordinator.async_release_control(CONTROL_PARAMETERS, _FIELD)
            else:
                await self.coordinator.async_write_control(
                    CONTROL_PARAMETERS, _FIELD, ElPriceMode[option.upper()]
                )
        except HomeAssistantError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="set_el_price_mode_failed",
            ) from err
        await self.coordinator.async_request_refresh()
