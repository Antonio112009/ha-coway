"""DataUpdateCoordinator for the Coway integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from pycoway import CowayClient, CowayError, PurifierData

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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
            skip_password_change=entry.data.get(CONF_SKIP_PASSWORD_CHANGE, True),
        )

    async def _async_setup(self) -> None:
        """Authenticate with the Coway API."""
        try:
            await self.client.login()
        except CowayError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
            ) from err

    async def _async_update_data(self) -> PurifierData:
        """Fetch the latest purifier data."""
        try:
            return await self.client.async_get_purifiers_data()
        except CowayError as err:
            raise UpdateFailed(f"Error fetching purifier data: {err}") from err

    async def async_shutdown(self) -> None:
        """Close the API client session."""
        await super().async_shutdown()
        await self.client.close()
