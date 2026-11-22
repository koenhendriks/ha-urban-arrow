from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from urban_arrow_api import UrbanArrowClient

from .auth import ConfigEntryAuth
from .coordinator import UrbanArrowCoordinator
from .types import UrbanArrowConfigEntry

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: UrbanArrowConfigEntry) -> bool:
    auth = ConfigEntryAuth(hass, entry, async_get_clientsession(hass))
    client = UrbanArrowClient(auth, language=hass.config.language)
    coordinator = UrbanArrowCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: UrbanArrowConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
