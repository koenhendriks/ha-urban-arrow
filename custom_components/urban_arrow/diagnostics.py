from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import CONF_TOKEN
from .types import UrbanArrowConfigEntry

TO_REDACT = {
    CONF_PASSWORD,
    CONF_TOKEN,
    CONF_USERNAME,
    "activationCode",
    "frameNumber",
    "id",
    "latitude",
    "longitude",
    "pin",
    "policeReportNumber",
    "policyNumber",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: UrbanArrowConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "bikes": [
            async_redact_data(
                {
                    "bike": data.bike.raw,
                    "telemetry": data.telemetry.raw if data.telemetry else None,
                },
                TO_REDACT,
            )
            for data in coordinator.data.values()
        ],
    }
