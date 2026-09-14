"""Binary sensor platform for the Coway integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import CowayConfigEntry, CowayDataUpdateCoordinator
from .entity import CowayEntity, async_track_new_purifiers

PARALLEL_UPDATES = 0  # Read-only platform; data arrives via the coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CowayConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Coway binary sensor entities."""
    coordinator = entry.runtime_data

    @callback
    def _async_add_purifiers(device_ids: list[str]) -> None:
        async_add_entities(
            CowayNetworkSensor(coordinator, device_id) for device_id in device_ids
        )

    async_track_new_purifiers(entry, _async_add_purifiers)


class CowayNetworkSensor(CowayEntity, BinarySensorEntity):
    """Representation of a Coway purifier network status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "network_status"
    # Stay available while the purifier is offline — reporting the
    # disconnected state is this sensor's entire purpose.
    _requires_connection = False

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
