"""Water heater platform for the CTC EcoZenith i360 custom integration.

One entity for domestic hot water. ``operation_mode`` drives control parameter
1007 (DHW comfort mode). The first option, ``auto``, releases the override and
lets the controller's own logic decide; picking ``economy`` / ``normal`` /
``comfort`` asserts it and the coordinator keeps re-writing it every keep-alive
interval until ``auto`` is picked again.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONTROL_PARAMETERS, DOMAIN
from .entity import CtcEcoZenithEntity
from .vendor.ctc_ecozenith import DhwMode

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CtcDataUpdateCoordinator
    from .data import CtcConfigEntry

PARALLEL_UPDATES = 0

_FIELD = "dhw_mode"
_OPTION_AUTO = "auto"
_MODES = [member.name.lower() for member in DhwMode]
_OPERATIONS = [_OPTION_AUTO, *_MODES]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CtcConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the CTC EcoZenith water heater entity."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([CtcDomesticHotWater(coordinator)])


class CtcDomesticHotWater(CtcEcoZenithEntity, WaterHeaterEntity, RestoreEntity):
    """Domestic hot water of the CTC EcoZenith i360."""

    _attr_translation_key = "dhw"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_operation_list = _OPERATIONS
    _attr_supported_features = WaterHeaterEntityFeature.OPERATION_MODE

    def __init__(self, coordinator: CtcDataUpdateCoordinator) -> None:
        """Initialize the water heater entity."""
        super().__init__(coordinator, "dhw")

    @property
    def current_temperature(self) -> float | None:
        """Return the measured hot-water temperature."""
        return self.coordinator.device.readings.dhw_temperature

    @property
    def current_operation(self) -> str:
        """Return the held DHW mode, or ``auto`` when no override is asserted.

        The controller is always in one of the three real modes, but this
        entity's state reflects only what Home Assistant is forcing - ``auto``
        means "not overridden", i.e. the panel setting is left to decide. The
        panel's own value is in the diagnostics dump / library ``settings``.
        """
        held = self.coordinator.held(CONTROL_PARAMETERS, _FIELD)
        if held is None:
            return _OPTION_AUTO
        return DhwMode(int(held)).name.lower()

    async def async_added_to_hass(self) -> None:
        """Re-assert a restored DHW mode so it survives a restart."""
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is None or last.state in (
            None,
            _OPTION_AUTO,
            "unknown",
            "unavailable",
        ):
            return
        with suppress(HomeAssistantError, KeyError):
            await self.coordinator.async_write_control(
                CONTROL_PARAMETERS, _FIELD, DhwMode[last.state.upper()]
            )

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Hold a DHW comfort mode, or release the override for ``auto``."""
        try:
            if operation_mode == _OPTION_AUTO:
                await self.coordinator.async_release_control(CONTROL_PARAMETERS, _FIELD)
            else:
                await self.coordinator.async_write_control(
                    CONTROL_PARAMETERS, _FIELD, DhwMode[operation_mode.upper()]
                )
        except (HomeAssistantError, KeyError) as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="set_dhw_mode_failed"
            ) from err
        await self.coordinator.async_request_refresh()
