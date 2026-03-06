"""Base entity for the Coway integration."""

from __future__ import annotations

from pycoway import CowayPurifier

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
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
