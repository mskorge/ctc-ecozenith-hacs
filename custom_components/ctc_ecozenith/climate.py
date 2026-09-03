"""Climate platform for the CTC EcoZenith i360 custom integration.

One entity for heating circuit 1, driven through the volatile control
parameters:

- ``hvac_mode`` maps to control parameter 1015 (zone mode HC1): ``HEAT`` holds
  ``ZoneMode.ON``, ``OFF`` holds ``ZoneMode.OFF``, and ``AUTO`` **releases** the
  zone-mode and setpoint overrides so the controller's own heat curve decides.
- ``target_temperature`` holds control parameter 1010 (HC1 room setpoint).

Because the manual does not promise a 1000-series write shows up in the 61500
read-back, the entity reports the value it is *holding* first, falling back to
the panel setpoint / measured room temperature.

A bare setpoint hold reports ``HEAT`` (it is an active, re-asserted override), so
a restored ``HEAT`` state re-asserts *both* the zone override and the setpoint on
startup - which can override the controller's own night reduction until the user
picks ``AUTO`` again.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONTROL_PARAMETERS, DOMAIN
from .entity import CtcEcoZenithEntity
from .vendor.ctc_ecozenith import (
    HS_SETPOINT_MAX,
    HS_SETPOINT_MIN,
    SETPOINT_STEP,
    HeatPumpStatus,
    ZoneMode,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CtcDataUpdateCoordinator
    from .data import CtcConfigEntry

PARALLEL_UPDATES = 0

_ZONE_FIELD = "hs1_zone_mode"
_SETPOINT_FIELD = "hs1_room_setpoint"

_MODE_TO_ZONE: dict[HVACMode, ZoneMode] = {
    HVACMode.HEAT: ZoneMode.ON,
    HVACMode.OFF: ZoneMode.OFF,
}
_ZONE_TO_MODE: dict[ZoneMode, HVACMode] = {
    ZoneMode.ON: HVACMode.HEAT,
    ZoneMode.HEAT: HVACMode.HEAT,
    ZoneMode.OFF: HVACMode.OFF,
    ZoneMode.AUTO: HVACMode.AUTO,
    ZoneMode.COOL: HVACMode.AUTO,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CtcConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the CTC EcoZenith climate entity."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([CtcHeatingCircuitClimate(coordinator)])


class CtcHeatingCircuitClimate(CtcEcoZenithEntity, ClimateEntity, RestoreEntity):
    """Heating circuit 1 of the CTC EcoZenith i360."""

    _attr_translation_key = "heating_circuit_1"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_min_temp = HS_SETPOINT_MIN
    _attr_max_temp = HS_SETPOINT_MAX
    _attr_target_temperature_step = SETPOINT_STEP

    def __init__(self, coordinator: CtcDataUpdateCoordinator) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator, "heating_circuit_1")

    @property
    def current_temperature(self) -> float | None:
        """Return the measured room temperature."""
        return self.coordinator.device.readings.hs1_room_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the held setpoint, or the panel setpoint as a fallback."""
        held = self.coordinator.held(CONTROL_PARAMETERS, _SETPOINT_FIELD)
        if held is not None:
            return float(held)
        return self.coordinator.device.settings.hs1_room_setpoint

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the held zone mode, or ``AUTO`` when no override is asserted."""
        held = self.coordinator.held(CONTROL_PARAMETERS, _ZONE_FIELD)
        if held is not None:
            return _ZONE_TO_MODE.get(ZoneMode(int(held)), HVACMode.AUTO)
        # A bare setpoint hold (no explicit zone override) still means the
        # circuit is being driven and re-asserted, so report HEAT - not AUTO,
        # which the entity contract reserves for "the controller decides".
        if self.coordinator.held(CONTROL_PARAMETERS, _SETPOINT_FIELD) is not None:
            return HVACMode.HEAT
        return HVACMode.AUTO

    @property
    def hvac_action(self) -> HVACAction:
        """Return whether the heat pump is currently heating."""
        if self.hvac_mode is HVACMode.OFF:
            return HVACAction.OFF
        if self.coordinator.device.readings.hp1_status is HeatPumpStatus.HEATING:
            return HVACAction.HEATING
        return HVACAction.IDLE

    async def async_added_to_hass(self) -> None:
        """Re-assert restored overrides so they survive a restart."""
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is None:
            return
        try:
            if last.state in (HVACMode.HEAT, HVACMode.OFF):
                await self.coordinator.async_write_control(
                    CONTROL_PARAMETERS, _ZONE_FIELD, _MODE_TO_ZONE[HVACMode(last.state)]
                )
                target = last.attributes.get(ATTR_TEMPERATURE)
                if target is not None:
                    await self.coordinator.async_write_control(
                        CONTROL_PARAMETERS, _SETPOINT_FIELD, float(target)
                    )
        except (HomeAssistantError, ValueError, KeyError):
            pass

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Change the zone mode, or release control for ``AUTO``."""
        try:
            if hvac_mode is HVACMode.AUTO:
                await self.coordinator.async_release_control(
                    CONTROL_PARAMETERS, _ZONE_FIELD
                )
                await self.coordinator.async_release_control(
                    CONTROL_PARAMETERS, _SETPOINT_FIELD
                )
            else:
                await self.coordinator.async_write_control(
                    CONTROL_PARAMETERS, _ZONE_FIELD, _MODE_TO_ZONE[hvac_mode]
                )
        except HomeAssistantError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="set_hvac_mode_failed"
            ) from err
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Hold a new room setpoint."""
        target = kwargs.get(ATTR_TEMPERATURE)
        if target is None:
            return
        try:
            await self.coordinator.async_write_control(
                CONTROL_PARAMETERS, _SETPOINT_FIELD, float(target)
            )
        except HomeAssistantError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_failed",
                translation_placeholders={"name": "heating circuit 1 setpoint"},
            ) from err
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        """Hold the circuit on."""
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        """Hold the circuit off."""
        await self.async_set_hvac_mode(HVACMode.OFF)
