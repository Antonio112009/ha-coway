"""The Coway integration."""

from __future__ import annotations

import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import PLATFORMS
from .coordinator import CowayConfigEntry, CowayDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: CowayConfigEntry) -> bool:
    """Set up Coway from a config entry."""
    coordinator = CowayDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_options_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CowayConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_options_updated(hass: HomeAssistant, entry: CowayConfigEntry) -> None:
    """Handle options update — reload the integration."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: CowayConfigEntry) -> bool:
    """Migrate old config entries.

    v1 -> v2: fan entity unique_ids changed from ``<device_id>`` to
    ``<device_id>_purifier`` to avoid potential collisions with other
    platforms keyed off ``device_id``.
    """
    if entry.version == 1:

        @callback
        def _migrate_unique_id(
            entity_entry: er.RegistryEntry,
        ) -> dict[str, str] | None:
            if (
                entity_entry.domain == Platform.FAN
                and not entity_entry.unique_id.endswith("_purifier")
            ):
                return {"new_unique_id": f"{entity_entry.unique_id}_purifier"}
            return None

        await er.async_migrate_entries(hass, entry.entry_id, _migrate_unique_id)
        hass.config_entries.async_update_entry(entry, version=2)
        _LOGGER.info("Migrated Coway config entry %s to version 2", entry.entry_id)

    return True
