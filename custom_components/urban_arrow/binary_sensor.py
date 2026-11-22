from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import UrbanArrowEntity
from .types import UrbanArrowConfigEntry

PARALLEL_UPDATES = 0

CHARGING = BinarySensorEntityDescription(
    key="charging",
    device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UrbanArrowConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        UrbanArrowChargingSensor(coordinator, bike_id, CHARGING) for bike_id in coordinator.data
    )


class UrbanArrowChargingSensor(UrbanArrowEntity, BinarySensorEntity):
    @property
    def is_on(self) -> bool | None:
        telemetry = self.bike_data.telemetry
        if telemetry is None or telemetry.battery_charging is None:
            return None
        return telemetry.battery_charging.value
