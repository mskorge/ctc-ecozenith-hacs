"""Binary sensor platform for the CTC EcoZenith i360 custom integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .entity import CtcEcoZenithEntity
from .vendor.ctc_ecozenith import CtcEcoZenith

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CtcDataUpdateCoordinator
    from .data import CtcConfigEntry

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class CtcBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a CTC EcoZenith binary sensor."""

    value_fn: Callable[[CtcEcoZenith], bool | None]


def _raw_to_bool(
    raw: float | None,
) -> bool | None:
    """A raw pump register: 0/1 on the reference unit, possibly 0-100 elsewhere."""
    return None if raw is None else raw > 0


BINARY_SENSORS: tuple[CtcBinarySensorEntityDescription, ...] = (
    CtcBinarySensorEntityDescription(
        key="radiator_pump",
        translation_key="radiator_pump",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: _raw_to_bool(d.readings.radiator_pump),
    ),
    CtcBinarySensorEntityDescription(
        key="dhw_circulation",
        translation_key="dhw_circulation",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: _raw_to_bool(d.readings.dhw_circulation),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CtcConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up CTC EcoZenith binary sensors."""
    coordinator = entry.runtime_data.coordinator
    entities: list[BinarySensorEntity] = [
        CtcBinarySensor(coordinator, description) for description in BINARY_SENSORS
    ]
    entities.append(CtcProblemBinarySensor(coordinator))
    async_add_entities(entities)


class CtcBinarySensor(CtcEcoZenithEntity, BinarySensorEntity):
    """A single boolean flag derived from the CTC EcoZenith unit."""

    entity_description: CtcBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: CtcDataUpdateCoordinator,
        description: CtcBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return true if the flag is set."""
        return self.entity_description.value_fn(self.coordinator.device)


class CtcProblemBinarySensor(CtcEcoZenithEntity, BinarySensorEntity):
    """On whenever the controller has one or more active alarms."""

    _attr_translation_key = "problem"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: CtcDataUpdateCoordinator) -> None:
        """Initialize the problem sensor."""
        super().__init__(coordinator, "problem")

    @property
    def is_on(self) -> bool:
        """Return true if at least one alarm is active."""
        return self.coordinator.alarms.has_alarm

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """List the active alarm and info-text codes."""
        snapshot = self.coordinator.alarms
        return {
            "alarm_count": snapshot.alarm_count,
            "alarm_codes": [f"E{alarm.code}" for alarm in snapshot.alarms],
            "heat_pump_alarm_codes": [
                f"E{alarm.code}" for alarm in snapshot.alarms if alarm.heat_pump
            ],
            "info_texts": [f"I{info.code}" for info in snapshot.infos],
        }
