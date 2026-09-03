"""Base entity for the CTC EcoZenith i360 custom integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import software_version
from .const import DOMAIN
from .coordinator import CtcDataUpdateCoordinator


class CtcEcoZenithEntity(CoordinatorEntity[CtcDataUpdateCoordinator]):
    """Common device-info and naming for every CTC EcoZenith entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CtcDataUpdateCoordinator, key: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        entry = coordinator.config_entry
        info = coordinator.device.info
        self._attr_unique_id = f"{entry.entry_id}-{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="CTC EcoZenith i360",
            manufacturer=info.manufacturer,
            model=info.model,
            sw_version=software_version(coordinator.device.readings),
        )
