"""Base entity for the Coway integration."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import datetime

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from pycoway import CowayError, CowayPurifier

from .const import COMMAND_REFRESH_DELAY, DOMAIN
from .coordinator import CowayConfigEntry, CowayDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class CowayEntity(CoordinatorEntity[CowayDataUpdateCoordinator]):
    """Base class for Coway entities."""

    _attr_has_entity_name = True
    # Most entities are meaningless while the purifier is offline. The
    # connectivity binary sensor overrides this so it can report
    # "disconnected" instead of going unavailable.
    _requires_connection = True

    def __init__(
        self,
        coordinator: CowayDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._cancel_refresh: CALLBACK_TYPE | None = None
        purifier = coordinator.data.purifiers[device_id]
        self._last_purifier: CowayPurifier = purifier
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer="Coway",
            # pycoway leaves ``model`` unset on the IoT path; fall back to
            # the other identity fields so the device registry shows something.
            model=(
                purifier.device_attr.model
                or purifier.device_attr.prod_name_full
                or purifier.device_attr.model_code
            ),
            name=purifier.device_attr.name,
            sw_version=purifier.mcu_version,
        )

    @property
    def purifier(self) -> CowayPurifier:
        """Return the latest purifier data, or the last-seen snapshot.

        When the device temporarily disappears from coordinator data we still
        need to return *something* sensible because Home Assistant reads
        capability properties (e.g. ``preset_modes``) even while the entity is
        marked unavailable.
        """
        purifier = self.coordinator.data.purifiers.get(self._device_id)
        if purifier is None:
            return self._last_purifier
        self._last_purifier = purifier
        return purifier

    @property
    def available(self) -> bool:
        """Return True when the purifier is connected to Coway servers."""
        if self._device_id not in self.coordinator.data.purifiers:
            return False
        if not super().available:
            return False
        return not self._requires_connection or bool(self.purifier.network_status)

    async def _async_send_command(self, action: str, command: Awaitable[None]) -> None:
        """Send a control command, surfacing failures in the UI.

        On failure a coordinator refresh is scheduled so optimistic state
        gets reverted, then the error is raised for Home Assistant to show.
        """
        try:
            await self.coordinator.async_run_command(command)
        except CowayError as err:
            _LOGGER.error("Failed to %s for %s: %s", action, self.entity_id, err)
            self._schedule_refresh()
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="command_failed",
                translation_placeholders={"action": action, "error": str(err)},
            ) from err

    @callback
    def _schedule_refresh(self) -> None:
        """Schedule a non-blocking delayed coordinator refresh."""
        if self._cancel_refresh is not None:
            self._cancel_refresh()

        async def _refresh(_now: datetime) -> None:
            self._cancel_refresh = None
            await self.coordinator.async_request_refresh()

        self._cancel_refresh = async_call_later(
            self.hass, COMMAND_REFRESH_DELAY, _refresh
        )

    async def async_will_remove_from_hass(self) -> None:
        """Cancel any pending refresh."""
        if self._cancel_refresh is not None:
            self._cancel_refresh()
            self._cancel_refresh = None


@callback
def async_track_new_purifiers(
    entry: CowayConfigEntry,
    async_add_purifiers: Callable[[list[str]], None],
) -> None:
    """Create entities for every purifier, now and whenever a new one appears.

    ``async_add_purifiers`` receives the ids of purifiers not seen before:
    all of them right away, then the new ones after each coordinator update.
    A purifier paired in the Coway app after setup thus shows up on the next
    poll without a reload.
    """
    coordinator = entry.runtime_data
    known: set[str] = set()

    @callback
    def _async_check_new_purifiers() -> None:
        new_ids = [
            device_id
            for device_id in coordinator.data.purifiers
            if device_id not in known
        ]
        if not new_ids:
            return
        known.update(new_ids)
        async_add_purifiers(new_ids)

    _async_check_new_purifiers()
    entry.async_on_unload(coordinator.async_add_listener(_async_check_new_purifiers))


@callback
def async_remove_stale_entities(
    hass: HomeAssistant,
    entry: CowayConfigEntry,
    domain: str,
    valid_unique_ids: set[str],
) -> None:
    """Remove registry entries of *current* purifiers that no longer apply.

    Descriptions can change between releases (renamed keys, model-specific
    entities). Entities of purifiers missing from this update are left
    untouched in case the device is only temporarily unreachable.
    """
    ent_reg = er.async_get(hass)
    current_device_ids = set(entry.runtime_data.data.purifiers)
    for ent_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if ent_entry.domain != domain or ent_entry.unique_id in valid_unique_ids:
            continue
        if not any(
            ent_entry.unique_id.startswith(f"{device_id}_")
            for device_id in current_device_ids
        ):
            continue
        ent_reg.async_remove(ent_entry.entity_id)
