from __future__ import annotations

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from urban_arrow_api import Location

from .entity import UrbanArrowEntity
from .types import UrbanArrowConfigEntry

PARALLEL_UPDATES = 0

LOCATION = EntityDescription(key="location", translation_key="location")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UrbanArrowConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        UrbanArrowTracker(coordinator, bike_id, LOCATION) for bike_id in coordinator.data
    )


class UrbanArrowTracker(UrbanArrowEntity, TrackerEntity):
    _attr_source_type = SourceType.GPS
    # Trackers default to diagnostic, which hides them from generated dashboards;
    # for a bike the position is primary information.
    _attr_entity_category = None

    @property
    def _location(self) -> Location | None:
        telemetry = self.bike_data.telemetry
        if telemetry is None or telemetry.location is None:
            return None
        location = telemetry.location.value
        # The module reports 0,0 when it has no GPS fix.
        if location is None or (location.latitude == 0 and location.longitude == 0):
            return None
        return location

    @property
    def latitude(self) -> float | None:
        return self._location.latitude if self._location else None

    @property
    def longitude(self) -> float | None:
        return self._location.longitude if self._location else None
