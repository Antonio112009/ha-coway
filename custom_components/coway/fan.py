"""Fan platform for the Coway integration."""

from __future__ import annotations

import math
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from .coordinator import CowayConfigEntry, CowayDataUpdateCoordinator
from .entity import CowayEntity

SPEED_RANGE = (1, 3)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CowayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Coway fan entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        CowayFan(coordinator, device_id) for device_id in coordinator.data.purifiers
    )


class CowayFan(CowayEntity, FanEntity):
    """Representation of a Coway air purifier as a fan."""

    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.PRESET_MODE
    )
    _attr_speed_count = int_states_in_range = 3
    _attr_preset_modes = ["auto", "night", "eco", "rapid"]
    _attr_translation_key = "purifier"

    def __init__(
        self,
        coordinator: CowayDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the fan."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = device_id

    @property
    def is_on(self) -> bool | None:
        """Return true if the purifier is on."""
        return self.purifier.is_on

    @property
    def percentage(self) -> int | None:
        """Return the current speed as a percentage."""
        if not self.is_on or self.purifier.fan_speed is None:
            return 0
        return ranged_value_to_percentage(SPEED_RANGE, self.purifier.fan_speed)

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        purifier = self.purifier
        if purifier.auto_mode:
            return "auto"
        if purifier.night_mode:
            return "night"
        if purifier.eco_mode:
            return "eco"
        if purifier.rapid_mode:
            return "rapid"
        return None

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the purifier."""
        await self.coordinator.client.async_set_power(
            self.purifier.device_attr, is_on=True
        )
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
        elif percentage is not None:
            await self.async_set_percentage(percentage)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the purifier."""
        await self.coordinator.client.async_set_power(
            self.purifier.device_attr, is_on=False
        )
        await self.coordinator.async_request_refresh()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the fan speed percentage."""
        if percentage == 0:
            await self.async_turn_off()
            return
        speed = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
        await self.coordinator.client.async_set_fan_speed(
            self.purifier.device_attr, speed=str(speed)
        )
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode."""
        attr = self.purifier.device_attr
        client = self.coordinator.client
        if preset_mode == "auto":
            await client.async_set_auto_mode(attr)
        elif preset_mode == "night":
            await client.async_set_night_mode(attr)
        elif preset_mode == "eco":
            await client.async_set_eco_mode(attr)
        elif preset_mode == "rapid":
            await client.async_set_rapid_mode(attr)
        await self.coordinator.async_request_refresh()
