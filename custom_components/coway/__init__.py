"""The Coway integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import CONF_SKIP_PASSWORD_CHANGE, PLATFORMS
from .coordinator import CowayConfigEntry, CowayDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate config entry from older versions.

    Handles migration from RobertD502/home-assistant-iocare (versions 1-5)
    to this integration (version 6).
    """
    _LOGGER.debug("Migrating Coway config entry from version %s", entry.version)

    if entry.version < 6:
        username = entry.data.get(CONF_USERNAME, "")
        password = entry.data.get(CONF_PASSWORD, "")
        skip = entry.options.get("skip_password_change", True)

        hass.config_entries.async_update_entry(
            entry,
            version=6,
            data={
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
                CONF_SKIP_PASSWORD_CHANGE: skip,
            },
            options={},
        )
        _LOGGER.info("Migrated Coway config entry to version 6")

    return True


async def async_setup_entry(hass: HomeAssistant, entry: CowayConfigEntry) -> bool:
    """Set up Coway from a config entry."""
    coordinator = CowayDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CowayConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
