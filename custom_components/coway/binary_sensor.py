"""Binary sensor platform for the Coway integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import CowayConfigEntry, CowayDataUpdateCoordinator
from .entity import CowayEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CowayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Coway binary sensor entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        CowayNetworkSensor(coordinator, device_id)
        for device_id in coordinator.data.purifiers
    )


class CowayNetworkSensor(CowayEntity, BinarySensorEntity):
    """Representation of a Coway purifier network status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = "network_status"

    def __init__(
        self,
        coordinator: CowayDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_network_status"

    @property
    def is_on(self) -> bool | None:
        """Return true if the purifier is connected to the network."""
        return self.purifier.network_status
