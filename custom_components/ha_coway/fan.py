"""Fan platform for the Coway integration."""

from __future__ import annotations

import asyncio
import logging
import math
from typing import Any

from pycoway import CowayError

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

_LOGGER = logging.getLogger(__name__)

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
    _attr_speed_count = 3
    _attr_translation_key = "purifier"

    def __init__(
        self,
        coordinator: CowayDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the fan."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_purifier"

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

    async def _run_command(self, action: str, coro: Any) -> bool:
        """Await an API coroutine, logging and swallowing CowayError.

        Returns True on success, False on failure. On failure an immediate
        coordinator refresh is scheduled so optimistic state is reverted.
        """
        try:
            await coro
        except CowayError as err:
            _LOGGER.error("Failed to %s for %s: %s", action, self.entity_id, err)
            self._schedule_refresh()
            return False
        return True

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the purifier."""
        if self._command_lock.locked():
            return
        async with self._command_lock:
            client = self.coordinator.client
            attr = self.purifier.device_attr
            if not await self._run_command(
                "turn on", client.async_set_power(attr, is_on=True)
            ):
                return
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
        if self._command_lock.locked():
            return
        async with self._command_lock:
            client = self.coordinator.client
            attr = self.purifier.device_attr
            if not await self._run_command(
                "turn off", client.async_set_power(attr, is_on=False)
            ):
                return
            self.purifier.is_on = False
            self.purifier.light_on = False
            self.async_write_ha_state()
            self._schedule_refresh()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the fan speed percentage."""
        if percentage == 0:
            await self.async_turn_off()
            return
        if self._command_lock.locked():
            return
        async with self._command_lock:
            if not self.is_on:
                client = self.coordinator.client
                attr = self.purifier.device_attr
                if not await self._run_command(
                    "power on", client.async_set_power(attr, is_on=True)
                ):
                    return
                self.purifier.is_on = True
                self.purifier.light_on = True
                await asyncio.sleep(COMMAND_CHAIN_DELAY)
            await self._apply_speed(percentage)

    async def _apply_speed(self, percentage: int) -> None:
        """Send the speed command and update optimistic state."""
        speed = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
        if not await self._run_command(
            "set speed",
            self.coordinator.client.async_set_fan_speed(
                self.purifier.device_attr, speed=str(speed)
            ),
        ):
            return
        self.purifier.fan_speed = speed
        self.purifier.auto_mode = False
        self.purifier.night_mode = False
        self.purifier.eco_mode = False
        self.async_write_ha_state()
        self._schedule_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode."""
        if self._command_lock.locked():
            return
        async with self._command_lock:
            if not self.is_on:
                client = self.coordinator.client
                attr = self.purifier.device_attr
                if not await self._run_command(
                    "power on", client.async_set_power(attr, is_on=True)
                ):
                    return
                self.purifier.is_on = True
                self.purifier.light_on = True
                await asyncio.sleep(COMMAND_CHAIN_DELAY)
            await self._apply_preset_mode(preset_mode)

    async def _apply_preset_mode(self, preset_mode: str) -> None:
        """Send the preset mode command and update optimistic state."""
        attr = self.purifier.device_attr
        client = self.coordinator.client
        purifier = self.purifier

        # mode -> (api method, (auto, eco, night, rapid), fan_speed)
        mode_map: dict[str, tuple[Any, tuple[bool, bool, bool, bool], int]] = {
            "auto": (client.async_set_auto_mode, (True, False, False, False), 1),
            "auto_eco": (client.async_set_eco_mode, (False, True, False, False), 0),
            "night": (client.async_set_night_mode, (False, False, True, False), 0),
            "eco": (client.async_set_eco_mode, (False, True, False, False), 0),
            "rapid": (client.async_set_rapid_mode, (False, False, False, True), 0),
        }
        spec = mode_map.get(preset_mode)
        if spec is None:
            _LOGGER.warning(
                "Unsupported preset mode '%s' for %s", preset_mode, self.entity_id
            )
            return
        api_call, (auto, eco, night, rapid), fan_speed = spec

        if not await self._run_command(f"set preset {preset_mode}", api_call(attr)):
            return
        purifier.auto_mode = auto
        purifier.eco_mode = eco
        purifier.night_mode = night
        purifier.rapid_mode = rapid
        purifier.fan_speed = fan_speed

        self.async_write_ha_state()
        self._schedule_refresh()
