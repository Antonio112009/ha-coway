"""Config flow for Coway integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from pycoway import AuthError, CowayClient, CowayError

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .const import CONF_SKIP_PASSWORD_CHANGE, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_SKIP_PASSWORD_CHANGE, default=True): bool,
    }
)


class CowayConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Coway."""

    VERSION = 1

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
                    skip_password_change=user_input[CONF_SKIP_PASSWORD_CHANGE],
                ) as client:
                    await client.login()
            except AuthError:
                errors["base"] = "invalid_auth"
            except CowayError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
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
