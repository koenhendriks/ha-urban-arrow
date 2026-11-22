import logging

from aiohttp import ClientSession
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from urban_arrow_api import Token, TokenAuth, UrbanArrowAuthError, login_with_credentials

from .const import CONF_TOKEN
from .types import UrbanArrowConfigEntry

_LOGGER = logging.getLogger(__name__)


class ConfigEntryAuth(TokenAuth):
    """Keeps the token in the config entry and logs in again when the refresh token dies."""

    def __init__(
        self, hass: HomeAssistant, entry: UrbanArrowConfigEntry, session: ClientSession
    ) -> None:
        super().__init__(session, Token.from_dict(entry.data[CONF_TOKEN]), self._async_save_token)
        self._hass = hass
        self._entry = entry

    @callback
    def _async_save_token(self, token: Token) -> None:
        self._hass.config_entries.async_update_entry(
            self._entry, data={**self._entry.data, CONF_TOKEN: token.as_dict()}
        )

    async def async_refresh_token(self, token: Token) -> Token:
        try:
            return await super().async_refresh_token(token)
        except UrbanArrowAuthError:
            _LOGGER.debug("Refresh token rejected, logging in again with stored credentials")
        # Raises UrbanArrowAuthError when the password changed; the coordinator then
        # starts a reauth flow.
        return await login_with_credentials(
            self._entry.data[CONF_USERNAME],
            self._entry.data[CONF_PASSWORD],
            session=self.session,
        )
