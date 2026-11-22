from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import UrbanArrowBikeData
from .entity import UrbanArrowEntity
from .types import UrbanArrowConfigEntry

PARALLEL_UPDATES = 0

PROTECTION_LEVELS = ["geofence", "motion_sensor", "none"]
# Bosch support modes as the app decodes them (ComoduleBleAdapter.decodeAssistLevel).
ASSIST_LEVELS = {0: "off", 1: "eco", 2: "tour", 3: "sport", 4: "turbo"}


@dataclass(frozen=True, kw_only=True)
class UrbanArrowSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[UrbanArrowBikeData], float | int | str | datetime | None]


def _telemetry(attr: str) -> Callable[[UrbanArrowBikeData], float | int | None]:
    def value(data: UrbanArrowBikeData) -> float | int | None:
        timed = getattr(data.telemetry, attr, None) if data.telemetry else None
        return timed.value if timed else None

    return value


def _assist_level(data: UrbanArrowBikeData) -> str | None:
    level = _telemetry("assist_level")(data)
    return ASSIST_LEVELS.get(int(level)) if level is not None else None


def _protection_level(data: UrbanArrowBikeData) -> str | None:
    level = data.bike.protection_level
    return level.lower() if level and level.lower() in PROTECTION_LEVELS else None


SENSORS: tuple[UrbanArrowSensorEntityDescription, ...] = (
    UrbanArrowSensorEntityDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_telemetry("battery_charge"),
    ),
    UrbanArrowSensorEntityDescription(
        key="range",
        translation_key="range",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=_telemetry("range"),
    ),
    UrbanArrowSensorEntityDescription(
        key="odometer",
        translation_key="odometer",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
        value_fn=_telemetry("odometer"),
    ),
    UrbanArrowSensorEntityDescription(
        key="assist_level",
        translation_key="assist_level",
        device_class=SensorDeviceClass.ENUM,
        options=list(ASSIST_LEVELS.values()),
        value_fn=_assist_level,
    ),
    UrbanArrowSensorEntityDescription(
        key="module_battery",
        translation_key="module_battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_telemetry("module_charge"),
    ),
    UrbanArrowSensorEntityDescription(
        key="protection_level",
        translation_key="protection_level",
        device_class=SensorDeviceClass.ENUM,
        options=PROTECTION_LEVELS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_protection_level,
    ),
    UrbanArrowSensorEntityDescription(
        key="last_online",
        translation_key="last_online",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.bike.module.last_online if data.bike.module else None,
    ),
    UrbanArrowSensorEntityDescription(
        key="subscription_end",
        translation_key="subscription_end",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: (
            data.bike.data_subscription.end_date if data.bike.data_subscription else None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UrbanArrowConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        UrbanArrowSensor(coordinator, bike_id, description)
        for bike_id in coordinator.data
        for description in SENSORS
    )


class UrbanArrowSensor(UrbanArrowEntity, SensorEntity):
    entity_description: UrbanArrowSensorEntityDescription

    @property
    def native_value(self) -> float | int | str | datetime | None:
        return self.entity_description.value_fn(self.bike_data)
