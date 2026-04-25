"""Base entity for the Coway integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from pycoway import CowayPurifier

from homeassistant.core import CALLBACK_TYPE, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COMMAND_REFRESH_DELAY, DOMAIN
from .coordinator import CowayDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class CowayEntity(CoordinatorEntity[CowayDataUpdateCoordinator]):
    """Base class for Coway entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CowayDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._cancel_refresh: CALLBACK_TYPE | None = None
        self._command_lock = asyncio.Lock()
        purifier = coordinator.data.purifiers[device_id]
        self._last_purifier: CowayPurifier = purifier
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer="Coway",
            model=purifier.device_attr.model,
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
        return super().available and self.purifier.network_status

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
