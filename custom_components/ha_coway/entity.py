"""Base entity for the Coway integration."""

from __future__ import annotations

from typing import Any

from pycoway import CowayPurifier

from homeassistant.core import CALLBACK_TYPE, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COMMAND_REFRESH_DELAY, DOMAIN
from .coordinator import CowayDataUpdateCoordinator


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
        self._command_in_progress = False
        purifier = self.purifier
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer="Coway",
            model=purifier.device_attr.model,
            name=purifier.device_attr.name,
            sw_version=purifier.mcu_version,
        )

    @property
    def purifier(self) -> CowayPurifier:
        """Return the purifier data for this device."""
        return self.coordinator.data.purifiers[self._device_id]

    @property
    def available(self) -> bool:
        """Return True when the purifier is connected to Coway servers."""
        return super().available and self.purifier.network_status

    @callback
    def _schedule_refresh(self) -> None:
        """Schedule a non-blocking delayed coordinator refresh."""
        if self._cancel_refresh is not None:
            self._cancel_refresh()

        async def _refresh(_now: Any) -> None:
            self._cancel_refresh = None
            self._command_in_progress = False
            await self.coordinator.async_request_refresh()

        self._cancel_refresh = async_call_later(
            self.hass, COMMAND_REFRESH_DELAY, _refresh
        )

    async def async_will_remove_from_hass(self) -> None:
        """Cancel any pending refresh."""
        if self._cancel_refresh is not None:
            self._cancel_refresh()
            self._cancel_refresh = None
        self._command_in_progress = False
