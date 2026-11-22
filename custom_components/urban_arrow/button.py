from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from urban_arrow_api import UrbanArrowError

from .const import DOMAIN
from .entity import UrbanArrowEntity
from .types import UrbanArrowConfigEntry

PARALLEL_UPDATES = 1

FLASH_LIGHTS = ButtonEntityDescription(key="flash_lights", translation_key="flash_lights")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UrbanArrowConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        UrbanArrowFlashLightsButton(coordinator, bike_id, FLASH_LIGHTS)
        for bike_id in coordinator.data
    )


class UrbanArrowFlashLightsButton(UrbanArrowEntity, ButtonEntity):
    async def async_press(self) -> None:
        try:
            await self.coordinator.client.flash_lights(self.bike_id)
        except UrbanArrowError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="action_failed",
                translation_placeholders={"error": str(err)},
            ) from err
