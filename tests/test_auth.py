import time
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pytest_homeassistant_custom_component.common import MockConfigEntry
from urban_arrow_api import Token, UrbanArrowAuthError

from custom_components.urban_arrow.auth import ConfigEntryAuth
from custom_components.urban_arrow.const import CONF_TOKEN

from .conftest import PASSWORD, USERNAME, make_token


async def test_refresh_is_persisted(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        data={**mock_config_entry.data, CONF_TOKEN: Token("old", "r", time.time() - 1).as_dict()},
    )
    auth = ConfigEntryAuth(hass, mock_config_entry, async_get_clientsession(hass))
    with patch("urban_arrow_api.auth.refresh_token", return_value=make_token("new")):
        assert await auth.async_get_access_token() == "new"
    assert mock_config_entry.data[CONF_TOKEN]["access_token"] == "new"


async def test_revoked_refresh_token_falls_back_to_login(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    mock_config_entry.add_to_hass(hass)
    auth = ConfigEntryAuth(hass, mock_config_entry, async_get_clientsession(hass))
    with (
        patch("urban_arrow_api.auth.refresh_token", side_effect=UrbanArrowAuthError("revoked")),
        patch(
            "custom_components.urban_arrow.auth.login_with_credentials",
            return_value=make_token("relogin"),
        ) as login,
    ):
        assert await auth.async_get_access_token(force_refresh=True) == "relogin"
    assert login.call_args.args == (USERNAME, PASSWORD)
    assert mock_config_entry.data[CONF_TOKEN]["access_token"] == "relogin"
