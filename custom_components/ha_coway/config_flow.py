"""Config flow for Coway integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from pycoway import AuthError, CowayClient, CowayError, PasswordExpired

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import (
    CONF_POLLING_INTERVAL,
    CONF_SKIP_PASSWORD_CHANGE,
    DEFAULT_POLLING_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_SKIP_PASSWORD_CHANGE, default=True): bool,
    }
)

STEP_REAUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_SKIP_PASSWORD_CHANGE, default=True): bool,
    }
)


class CowayOptionsFlowHandler(OptionsFlow):
    """Handle Coway options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_POLLING_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL
                        ),
                    ): vol.All(int, vol.Range(min=30, max=600)),
                }
            ),
        )


class CowayConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Coway."""

    VERSION = 2

    @staticmethod
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> CowayOptionsFlowHandler:
        """Get the options flow for this handler."""
        return CowayOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = await self._async_validate_credentials(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                user_input[CONF_SKIP_PASSWORD_CHANGE],
            )
            if not errors:
                await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Trigger reauthentication when credentials become invalid."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Prompt the user for a fresh password."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        username = entry.data[CONF_USERNAME]

        if user_input is not None:
            skip_password_change = user_input.get(
                CONF_SKIP_PASSWORD_CHANGE,
                entry.data.get(CONF_SKIP_PASSWORD_CHANGE, True),
            )
            errors = await self._async_validate_credentials(
                username,
                user_input[CONF_PASSWORD],
                skip_password_change,
            )
            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_SKIP_PASSWORD_CHANGE: skip_password_change,
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_DATA_SCHEMA,
            description_placeholders={"username": username},
            errors=errors,
        )

    async def _async_validate_credentials(
        self, username: str, password: str, skip_password_change: bool
    ) -> dict[str, str]:
        """Attempt a login with the given credentials.

        Returns an empty dict on success, or a ``{"base": <error_key>}`` dict
        suitable for passing to ``async_show_form``.
        """
        try:
            async with CowayClient(
                username,
                password,
                session=async_create_clientsession(self.hass),
                skip_password_change=skip_password_change,
            ) as client:
                await client.login()
        except AuthError:
            return {"base": "invalid_auth"}
        except PasswordExpired:
            return {"base": "password_expired"}
        except CowayError:
            return {"base": "cannot_connect"}
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Unexpected error during Coway login: %s", err)
            return {"base": "unknown"}
        return {}
