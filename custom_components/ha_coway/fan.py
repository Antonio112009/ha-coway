"""Fan platform for the Coway integration."""

from __future__ import annotations

import asyncio
import math
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from .const import COMMAND_CHAIN_DELAY
from .coordinator import CowayConfigEntry, CowayDataUpdateCoordinator
from .devices import (
    AP_1512HHS_PRESET_MODES,
    DEFAULT_PRESET_MODES,
    MODEL_250S,
    MODEL_250S_HIDDEN_SPEEDS,
    MODEL_250S_PRESET_MODES,
    MODEL_AP_1512HHS,
)
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
    def preset_modes(self) -> list[str]:
        """Return the available preset modes based on purifier model."""
        purifier = self.purifier
        model_code = purifier.device_attr.model_code
        model = purifier.device_attr.model

        if model_code == MODEL_AP_1512HHS:
            return list(AP_1512HHS_PRESET_MODES)
        if model == MODEL_250S:
            modes = list(MODEL_250S_PRESET_MODES)
            if purifier.fan_speed == 9:
                modes.insert(1, "auto_eco")
            return modes
        # Default (400S, IconS, others)
        modes = list(DEFAULT_PRESET_MODES)
        if purifier.eco_mode:
            modes.insert(1, "auto_eco")
        return modes

    @property
    def is_on(self) -> bool | None:
        """Return true if the purifier is on."""
        return self.purifier.is_on

    @property
    def percentage(self) -> int | None:
        """Return the current speed as a percentage."""
        if not self.is_on or self.purifier.fan_speed is None:
            return 0
        # 250S reports speed 5 (rapid) and 9 (smart eco) which are not
        # user-selectable speeds — show 0% to match the IoCare app.
        if self.purifier.device_attr.model == MODEL_250S:
            if self.purifier.fan_speed in MODEL_250S_HIDDEN_SPEEDS:
                return 0
        # Auto eco mode has no meaningful speed level
        if self.preset_mode == "auto_eco":
            return 0
        return ranged_value_to_percentage(SPEED_RANGE, self.purifier.fan_speed)

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        purifier = self.purifier
        model_code = purifier.device_attr.model_code
        model = purifier.device_attr.model

        if model_code == MODEL_AP_1512HHS:
            if purifier.auto_mode:
                return "auto"
            if purifier.eco_mode:
                return "eco"
        elif model == MODEL_250S:
            if purifier.fan_speed == 9:
                return "auto_eco"
            if purifier.auto_mode:
                return "auto"
            if purifier.night_mode:
                return "night"
            if purifier.rapid_mode:
                return "rapid"
        else:
            if purifier.eco_mode:
                return "auto_eco"
            if purifier.auto_mode:
                return "auto"
            if purifier.night_mode:
                return "night"
        return None

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the purifier."""
        if self._command_in_progress:
            return
        self._command_in_progress = True
        await self.coordinator.client.async_set_power(
            self.purifier.device_attr, is_on=True
        )
        self.purifier.is_on = True
        self.purifier.light_on = True
        if preset_mode is not None:
            await asyncio.sleep(COMMAND_CHAIN_DELAY)
            await self._apply_preset_mode(preset_mode)
            return
        if percentage is not None:
            await asyncio.sleep(COMMAND_CHAIN_DELAY)
            await self._apply_speed(percentage)
            return
        self.async_write_ha_state()
        self._schedule_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the purifier."""
        if self._command_in_progress:
            return
        self._command_in_progress = True
        await self.coordinator.client.async_set_power(
            self.purifier.device_attr, is_on=False
        )
        self.purifier.is_on = False
        self.purifier.light_on = False
        self.async_write_ha_state()
        self._schedule_refresh()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the fan speed percentage."""
        if percentage == 0:
            await self.async_turn_off()
            return
        if self._command_in_progress:
            return
        self._command_in_progress = True
        if not self.is_on:
            await self.coordinator.client.async_set_power(
                self.purifier.device_attr, is_on=True
            )
            self.purifier.is_on = True
            self.purifier.light_on = True
            await asyncio.sleep(COMMAND_CHAIN_DELAY)
        await self._apply_speed(percentage)

    async def _apply_speed(self, percentage: int) -> None:
        """Send the speed command and update optimistic state."""
        speed = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
        await self.coordinator.client.async_set_fan_speed(
            self.purifier.device_attr, speed=str(speed)
        )
        self.purifier.fan_speed = speed
        self.purifier.auto_mode = False
        self.purifier.night_mode = False
        self.purifier.eco_mode = False
        self.async_write_ha_state()
        self._schedule_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode."""
        if self._command_in_progress:
            return
        self._command_in_progress = True
        if not self.is_on:
            await self.coordinator.client.async_set_power(
                self.purifier.device_attr, is_on=True
            )
            self.purifier.is_on = True
            self.purifier.light_on = True
            await asyncio.sleep(COMMAND_CHAIN_DELAY)
        await self._apply_preset_mode(preset_mode)

    async def _apply_preset_mode(self, preset_mode: str) -> None:
        """Send the preset mode command and update optimistic state."""
        attr = self.purifier.device_attr
        client = self.coordinator.client
        purifier = self.purifier

        if preset_mode == "auto":
            await client.async_set_auto_mode(attr)
            purifier.auto_mode = True
            purifier.eco_mode = False
            purifier.night_mode = False
            purifier.rapid_mode = False
            purifier.fan_speed = 1
        elif preset_mode == "auto_eco":
            await client.async_set_eco_mode(attr)
            purifier.eco_mode = True
            purifier.auto_mode = False
            purifier.night_mode = False
            purifier.rapid_mode = False
            purifier.fan_speed = 0
        elif preset_mode == "night":
            await client.async_set_night_mode(attr)
            purifier.night_mode = True
            purifier.auto_mode = False
            purifier.eco_mode = False
            purifier.rapid_mode = False
            purifier.fan_speed = 0
        elif preset_mode == "eco":
            await client.async_set_eco_mode(attr)
            purifier.eco_mode = True
            purifier.auto_mode = False
            purifier.night_mode = False
            purifier.rapid_mode = False
            purifier.fan_speed = 0
        elif preset_mode == "rapid":
            await client.async_set_rapid_mode(attr)
            purifier.rapid_mode = True
            purifier.auto_mode = False
            purifier.eco_mode = False
            purifier.night_mode = False
            purifier.fan_speed = 0

        self.async_write_ha_state()
        self._schedule_refresh()
