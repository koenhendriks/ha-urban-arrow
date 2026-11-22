from unittest.mock import AsyncMock

import pytest
from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.components.button import SERVICE_PRESS
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)
from urban_arrow_api import BikeSetting, UrbanArrowApiError

from custom_components.urban_arrow.const import DOMAIN

from .conftest import BIKE_ID

PREFIX = "test_arrow"


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant, mock_client: AsyncMock, mock_config_entry: MockConfigEntry
) -> MockConfigEntry:
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry


async def test_device(
    device_registry: dr.DeviceRegistry, setup_integration: MockConfigEntry
) -> None:
    device = device_registry.async_get_device_by_identifier(
        (DOMAIN, BIKE_ID), setup_integration.entry_id
    )
    assert device.name == "Test Arrow"
    assert device.manufacturer == "Urban Arrow"
    assert device.model == "Family Active Line Plus"
    assert device.sw_version == "260828"


@pytest.mark.usefixtures("setup_integration")
@pytest.mark.parametrize(
    ("entity_id", "state"),
    [
        (f"sensor.{PREFIX}_battery", "72"),
        (f"sensor.{PREFIX}_range", "26.0"),
        (f"sensor.{PREFIX}_odometer", "1705.04"),
        (f"sensor.{PREFIX}_assist_level", "turbo"),
        (f"sensor.{PREFIX}_module_battery", "22"),
        (f"sensor.{PREFIX}_protection_level", "motion_sensor"),
        (f"sensor.{PREFIX}_last_online", "2026-11-24T08:05:21+00:00"),
        (f"binary_sensor.{PREFIX}_charging", "off"),
        (f"switch.{PREFIX}_theft_protection", "on"),
        (f"switch.{PREFIX}_auto_protection", "on"),
        (f"switch.{PREFIX}_module_battery_management", "on"),
        (f"device_tracker.{PREFIX}_location", "not_home"),
        (f"button.{PREFIX}_flash_lights", "unknown"),
    ],
)
async def test_entity_states(hass: HomeAssistant, entity_id: str, state: str) -> None:
    assert hass.states.get(entity_id).state == state


@pytest.mark.usefixtures("setup_integration")
async def test_tracker_location(hass: HomeAssistant) -> None:
    attrs = hass.states.get(f"device_tracker.{PREFIX}_location").attributes
    assert (attrs["latitude"], attrs["longitude"]) == (52.0, 5.0)


@pytest.mark.usefixtures("setup_integration")
async def test_flash_lights(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: f"button.{PREFIX}_flash_lights"},
        blocking=True,
    )
    mock_client.flash_lights.assert_awaited_once_with(BIKE_ID)


@pytest.mark.usefixtures("setup_integration")
async def test_switches_call_api(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: f"switch.{PREFIX}_theft_protection"},
        blocking=True,
    )
    mock_client.set_theft_protection.assert_awaited_once_with(BIKE_ID, False)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: f"switch.{PREFIX}_auto_protection"},
        blocking=True,
    )
    mock_client.set_setting.assert_awaited_once_with(BIKE_ID, BikeSetting.AUTO_PROTECTION, True)


@pytest.mark.usefixtures("setup_integration")
async def test_action_error_is_raised(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    mock_client.flash_lights.side_effect = UrbanArrowApiError(500, "nope")
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: f"button.{PREFIX}_flash_lights"},
            blocking=True,
        )


async def test_bike_without_telemetry(
    hass: HomeAssistant, mock_client: AsyncMock, mock_config_entry: MockConfigEntry
) -> None:
    mock_client.get_telemetry.side_effect = UrbanArrowApiError(404, "no subscription")
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(f"sensor.{PREFIX}_battery").state == "unknown"
    assert hass.states.get(f"switch.{PREFIX}_theft_protection").state == "on"


async def test_diagnostics_are_redacted(
    hass: HomeAssistant, hass_client, setup_integration: MockConfigEntry
) -> None:
    diag = await get_diagnostics_for_config_entry(hass, hass_client, setup_integration)
    text = str(diag)
    for secret in ("rider@example.com", "secret", "0000000TEST", "52.0", "refresh"):
        assert secret not in text
    assert diag["bikes"][0]["telemetry"]["battery"]["charge"]["value"] == 72
