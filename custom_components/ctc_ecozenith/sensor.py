"""Sensor platform for the CTC EcoZenith i360 custom integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)

from .entity import CtcEcoZenithEntity
from .vendor.ctc_ecozenith import CtcEcoZenith, HeatPumpStatus, ShuntState, SystemStatus

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from .coordinator import CtcDataUpdateCoordinator
    from .data import CtcConfigEntry

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class CtcSensorEntityDescription(SensorEntityDescription):
    """Describes a CTC EcoZenith sensor."""

    value_fn: Callable[[CtcEcoZenith], StateType]


def _temperature(
    key: str,
    value_fn: Callable[[CtcEcoZenith], StateType],
    *,
    enabled: bool = True,
    diagnostic: bool = False,
) -> CtcSensorEntityDescription:
    return CtcSensorEntityDescription(
        key=key,
        translation_key=key,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_registry_enabled_default=enabled,
        entity_category=EntityCategory.DIAGNOSTIC if diagnostic else None,
        value_fn=value_fn,
    )


def _percent(
    key: str, value_fn: Callable[[CtcEcoZenith], StateType]
) -> CtcSensorEntityDescription:
    return CtcSensorEntityDescription(
        key=key,
        translation_key=key,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=value_fn,
    )


def _power(
    key: str, value_fn: Callable[[CtcEcoZenith], StateType]
) -> CtcSensorEntityDescription:
    return CtcSensorEntityDescription(
        key=key,
        translation_key=key,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=value_fn,
    )


def _enum(
    key: str,
    enum_cls: type[IntEnum],
    value_fn: Callable[[CtcEcoZenith], IntEnum | None],
) -> CtcSensorEntityDescription:
    return CtcSensorEntityDescription(
        key=key,
        translation_key=key,
        device_class=SensorDeviceClass.ENUM,
        options=[member.name.lower() for member in enum_cls],
        value_fn=lambda device: (
            member.name.lower() if (member := value_fn(device)) is not None else None
        ),
    )


SENSORS: tuple[CtcSensorEntityDescription, ...] = (
    # Temperatures
    _temperature("outdoor_temperature", lambda d: d.readings.outdoor_temperature),
    _temperature("return_temperature", lambda d: d.readings.return_temperature),
    _temperature(
        "radiator_water_temperature", lambda d: d.readings.radiator_water_temperature
    ),
    _temperature(
        "hs1_primary_flow_temperature",
        lambda d: d.readings.hs1_primary_flow_temperature,
    ),
    _temperature(
        "hs1_primary_flow_setpoint",
        lambda d: d.readings.hs1_primary_flow_setpoint,
        diagnostic=True,
    ),
    _temperature("hs1_room_temperature", lambda d: d.readings.hs1_room_temperature),
    _temperature("dhw_temperature", lambda d: d.readings.dhw_temperature),
    _temperature("dhw_upper_temperature", lambda d: d.readings.dhw_upper_temperature),
    _temperature(
        "dhw_lower_temperature",
        lambda d: d.readings.dhw_lower_temperature,
        enabled=False,
    ),
    _temperature(
        "dhw_outlet_setpoint",
        lambda d: d.readings.dhw_outlet_setpoint,
        diagnostic=True,
    ),
    _temperature(
        "dhw_stop_temperature",
        lambda d: d.readings.dhw_stop_temperature,
        diagnostic=True,
    ),
    _temperature(
        "dhw_lower_tank_setpoint",
        lambda d: d.readings.dhw_lower_tank_setpoint,
        diagnostic=True,
    ),
    _temperature("hp1_supply_temperature", lambda d: d.readings.hp1_supply_temperature),
    _temperature("hp1_return_temperature", lambda d: d.readings.hp1_return_temperature),
    _temperature(
        "hp1_discharge_temperature",
        lambda d: d.readings.hp1_discharge_temperature,
        diagnostic=True,
    ),
    _temperature(
        "hp1_outdoor_temperature",
        lambda d: d.readings.hp1_outdoor_temperature,
        diagnostic=True,
    ),
    # Enums
    _enum("system_status", SystemStatus, lambda d: d.readings.system_status),
    _enum("hp1_status", HeatPumpStatus, lambda d: d.readings.hp1_status),
    _enum("hs1_shunt_state", ShuntState, lambda d: d.readings.hs1_shunt_state),
    # Pump / fan output
    _percent("hp1_charge_pump", lambda d: d.readings.hp1_charge_pump),
    _percent("hp1_brine_pump", lambda d: d.readings.hp1_brine_pump),
    _percent("hp1_fan", lambda d: d.readings.hp1_fan),
    _percent("dhw_capacity", lambda d: d.readings.dhw_capacity),
    # Power
    _power("hp1_power", lambda d: d.readings.hp1_power),
    _power("immersion_heater_power", lambda d: d.readings.immersion_heater_power),
    # Misc
    CtcSensorEntityDescription(
        key="hp1_current_rps",
        translation_key="hp1_current_rps",
        native_unit_of_measurement="rps",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda d: d.readings.hp1_current_rps,
    ),
    CtcSensorEntityDescription(
        key="degree_minutes",
        translation_key="degree_minutes",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.readings.degree_minutes,
    ),
    CtcSensorEntityDescription(
        key="hp1_primary_flow",
        translation_key="hp1_primary_flow",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda d: d.readings.hp1_primary_flow,
    ),
    # Settings (read-only panel values), diagnostic
    CtcSensorEntityDescription(
        key="radiator_pump_setting",
        translation_key="radiator_pump_setting",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.settings.radiator_pump_setting,
    ),
    CtcSensorEntityDescription(
        key="hs1_inclination",
        translation_key="hs1_inclination",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda d: d.settings.hs1_inclination,
    ),
    CtcSensorEntityDescription(
        key="hs1_adjustment",
        translation_key="hs1_adjustment",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda d: d.settings.hs1_adjustment,
    ),
    CtcSensorEntityDescription(
        key="vacation_days",
        translation_key="vacation_days",
        native_unit_of_measurement="d",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.settings.vacation_days,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CtcConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up CTC EcoZenith sensors."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(CtcSensor(coordinator, description) for description in SENSORS)


class CtcSensor(CtcEcoZenithEntity, SensorEntity):
    """A single value read from the CTC EcoZenith unit."""

    entity_description: CtcSensorEntityDescription

    def __init__(
        self,
        coordinator: CtcDataUpdateCoordinator,
        description: CtcSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> StateType:
        """Return the current value."""
        return self.entity_description.value_fn(self.coordinator.device)
