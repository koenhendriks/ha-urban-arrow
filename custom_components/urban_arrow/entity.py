from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import UrbanArrowBikeData, UrbanArrowCoordinator


class UrbanArrowEntity(CoordinatorEntity[UrbanArrowCoordinator]):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UrbanArrowCoordinator,
        bike_id: str,
        description: EntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self.bike_id = bike_id
        self._attr_unique_id = f"{bike_id}_{description.key}"
        bike = coordinator.data[bike_id].bike
        module = bike.module
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, bike_id)},
            manufacturer=MANUFACTURER,
            model=bike.model,
            name=bike.name,
            serial_number=bike.frame_number,
            sw_version=module.firmware.version if module and module.firmware else None,
            hw_version=bike.system,
        )

    @property
    def bike_data(self) -> UrbanArrowBikeData:
        return self.coordinator.data[self.bike_id]

    @property
    def available(self) -> bool:
        return super().available and self.bike_id in self.coordinator.data
