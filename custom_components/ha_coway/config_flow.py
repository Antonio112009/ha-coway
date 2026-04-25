"""Config flow for Coway integration."""

from __future__ import annotations

import logging
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
            try:
                async with CowayClient(
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                    session=async_create_clientsession(self.hass),
                    skip_password_change=user_input[CONF_SKIP_PASSWORD_CHANGE],
                ) as client:
                    await client.login()
            except AuthError:
                errors["base"] = "invalid_auth"
            except PasswordExpired:
                errors["base"] = "password_expired"
            except CowayError:
                errors["base"] = "cannot_connect"
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("Unexpected error during Coway login: %s", err)
                errors["base"] = "unknown"
            else:
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
