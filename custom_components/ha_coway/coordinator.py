"""DataUpdateCoordinator for the Coway integration."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pycoway import AuthError, CowayClient, CowayError, PasswordExpired, PurifierData

from .const import (
    CONF_POLLING_INTERVAL,
    CONF_SKIP_PASSWORD_CHANGE,
    DEFAULT_POLLING_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

type CowayConfigEntry = ConfigEntry[CowayDataUpdateCoordinator]


class CowayDataUpdateCoordinator(DataUpdateCoordinator[PurifierData]):
    """Coordinator that fetches purifier data from the Coway API."""

    config_entry: CowayConfigEntry

    def __init__(self, hass: HomeAssistant, entry: CowayConfigEntry) -> None:
        """Initialize the coordinator."""
        polling_interval = entry.options.get(
            CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=polling_interval),
            config_entry=entry,
        )
        self.client = CowayClient(
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
            session=async_create_clientsession(hass),
            skip_password_change=entry.data.get(CONF_SKIP_PASSWORD_CHANGE, True),
        )
        # pycoway's async_get_purifiers_data() temporarily disables the
        # client's token check for the duration of the batch, so control
        # commands must never overlap a poll on the shared client.
        self._client_lock = asyncio.Lock()

    async def async_run_command(self, command: Awaitable[None]) -> None:
        """Run a control command serialized against polling."""
        async with self._client_lock:
            await command

    async def _async_setup(self) -> None:
        """Authenticate with the Coway API.

        Only genuine credential problems raise ConfigEntryAuthFailed;
        transient failures (connection issues, rate limiting, server
        maintenance) raise UpdateFailed so setup is retried instead of
        prompting the user to re-authenticate.
        """
        try:
            await self.client.login()
        except PasswordExpired as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="password_expired",
            ) from err
        except AuthError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
            ) from err
        except CowayError as err:
            raise UpdateFailed(f"Error connecting to the Coway API: {err}") from err

    async def _async_update_data(self) -> PurifierData:
        """Fetch the latest purifier data."""
        try:
            async with self._client_lock:
                return await self.client.async_get_purifiers_data()
        except PasswordExpired as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="password_expired",
            ) from err
        except AuthError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
            ) from err
        except CowayError as err:
            raise UpdateFailed(f"Error fetching purifier data: {err}") from err
