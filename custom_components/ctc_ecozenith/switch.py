"""Switch platform for the CTC EcoZenith i360 custom integration.

One switch: **Extra hot water** drives control parameter 1006. Turning it on
writes ``1`` and the coordinator re-asserts it every keep-alive interval;
turning it off just stops re-asserting, so the controller ends the top-up on its
own within five minutes (there is no documented "cancel now" value for 1006).
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONTROL_PARAMETERS, DOMAIN
from .entity import CtcEcoZenithEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CtcDataUpdateCoordinator
    from .data import CtcConfigEntry

PARALLEL_UPDATES = 0

_FIELD = "extra_dhw"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CtcConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the CTC EcoZenith switch entities."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([CtcExtraHotWaterSwitch(coordinator)])


class CtcExtraHotWaterSwitch(CtcEcoZenithEntity, SwitchEntity, RestoreEntity):
    """Extra hot water top-up (control parameter 1006)."""

    _attr_translation_key = "extra_hot_water"
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator: CtcDataUpdateCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, _FIELD)

    @property
    def is_on(self) -> bool:
        """Return whether an extra-hot-water override is currently held."""
        return bool(self.coordinator.held(CONTROL_PARAMETERS, _FIELD))

    async def async_added_to_hass(self) -> None:
        """Re-assert a restored 'on' state so the top-up survives a restart."""
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state == "on":
            with suppress(HomeAssistantError):
                await self.coordinator.async_write_control(
                    CONTROL_PARAMETERS, _FIELD, 1
                )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Trigger extra hot water and keep re-asserting it."""
        try:
            await self.coordinator.async_write_control(CONTROL_PARAMETERS, _FIELD, 1)
        except HomeAssistantError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="set_extra_hot_water_failed",
            ) from err
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop re-asserting; the controller ends the top-up within five minutes."""
        await self.coordinator.async_release_control(CONTROL_PARAMETERS, _FIELD)
        await self.coordinator.async_request_refresh()
