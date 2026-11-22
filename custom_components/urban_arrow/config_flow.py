from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from urban_arrow_api import (
    Token,
    UrbanArrowAuthError,
    UrbanArrowCaptchaRequired,
    UrbanArrowConnectionError,
    UrbanArrowMfaRequired,
    login_with_credentials,
)

from .const import CONF_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

PASSWORD_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): TextSelector(
            TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="username")
        ),
        vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR,
    }
)
REAUTH_SCHEMA = vol.Schema({vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR})


class UrbanArrowConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _async_login(self, username: str, password: str) -> tuple[Token | None, str | None]:
        try:
            token = await login_with_credentials(
                username, password, session=async_get_clientsession(self.hass)
            )
        except UrbanArrowCaptchaRequired:
            return None, "captcha_required"
        except UrbanArrowMfaRequired:
            return None, "mfa_required"
        except UrbanArrowAuthError:
            return None, "invalid_auth"
        except UrbanArrowConnectionError:
            return None, "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected error while logging in")
            return None, "unknown"
        return token, None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            await self.async_set_unique_id(username.lower())
            self._abort_if_unique_id_configured()
            token, error = await self._async_login(username, user_input[CONF_PASSWORD])
            if token:
                return self.async_create_entry(
                    title=username,
                    data={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_TOKEN: token.as_dict(),
                    },
                )
            errors["base"] = error or "unknown"
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            token, error = await self._async_login(
                entry.data[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            if token:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_TOKEN: token.as_dict(),
                    },
                )
            errors["base"] = error or "unknown"
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=REAUTH_SCHEMA,
            description_placeholders={"username": entry.data[CONF_USERNAME]},
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            await self.async_set_unique_id(username.lower())
            self._abort_if_unique_id_mismatch(reason="wrong_account")
            token, error = await self._async_login(username, user_input[CONF_PASSWORD])
            if token:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_TOKEN: token.as_dict(),
                    },
                )
            errors["base"] = error or "unknown"
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                USER_SCHEMA, user_input or {CONF_USERNAME: entry.data[CONF_USERNAME]}
            ),
            errors=errors,
        )
