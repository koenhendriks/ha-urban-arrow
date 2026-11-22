from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from urban_arrow_api import (
    Bike,
    Telemetry,
    UrbanArrowApiError,
    UrbanArrowAuthError,
    UrbanArrowClient,
    UrbanArrowError,
)

from .const import DOMAIN, SCAN_INTERVAL
from .types import UrbanArrowConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class UrbanArrowBikeData:
    bike: Bike
    telemetry: Telemetry | None


class UrbanArrowCoordinator(DataUpdateCoordinator[dict[str, UrbanArrowBikeData]]):
    config_entry: UrbanArrowConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: UrbanArrowConfigEntry, client: UrbanArrowClient
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, UrbanArrowBikeData]:
        try:
            summaries = await self.client.get_bikes()
            results = await asyncio.gather(*(self._async_fetch_bike(s.id) for s in summaries))
        except UrbanArrowAuthError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="auth_failed"
            ) from err
        except UrbanArrowError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        return {data.bike.id: data for data in results}

    async def _async_fetch_bike(self, bike_id: str) -> UrbanArrowBikeData:
        bike = await self.client.get_bike(bike_id)
        telemetry = None
        if bike.is_smart:
            try:
                telemetry = await self.client.get_telemetry(bike_id)
            except UrbanArrowApiError as err:
                # Bikes without an active data subscription have no telemetry.
                if err.status != 404:
                    raise
        return UrbanArrowBikeData(bike, telemetry)
