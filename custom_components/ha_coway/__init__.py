"""The Coway integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, PLATFORMS
from .coordinator import CowayConfigEntry, CowayDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


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


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: CowayConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Allow deleting a purifier the Coway account no longer reports.

    Purifiers missing from an update are kept on purpose, since they may
    only be unreachable, so this is how a sold or unpaired one is removed.
    Without a loaded entry there is no device list to check against, so
    removal is refused rather than guessed.
    """
    if entry.state is not ConfigEntryState.LOADED:
        return False
    purifiers = entry.runtime_data.data.purifiers
    return not any(
        domain == DOMAIN and device_id in purifiers
        for domain, device_id in device_entry.identifiers
    )


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
