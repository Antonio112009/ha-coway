"""Switch platform for the Coway integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pycoway import CowayPurifier, DeviceAttributes

from .coordinator import CowayConfigEntry, CowayDataUpdateCoordinator
from .devices import FAMILY_250S, detect_family, uses_light_mode_select
from .entity import (
    CowayEntity,
    async_remove_stale_entities,
    async_track_new_purifiers,
)

PARALLEL_UPDATES = 1  # Serialize cloud control commands


@dataclass(frozen=True, kw_only=True)
class CowaySwitchEntityDescription(SwitchEntityDescription):
    """Describe a Coway switch entity."""

    is_on_fn: Callable[[CowayPurifier], bool | None]
    turn_on_fn: Callable[
        [CowayDataUpdateCoordinator, DeviceAttributes], Awaitable[None]
    ]
    turn_off_fn: Callable[
        [CowayDataUpdateCoordinator, DeviceAttributes], Awaitable[None]
    ]
    is_supported: Callable[[DeviceAttributes], bool] = field(default=lambda attr: True)


SWITCH_DESCRIPTIONS: tuple[CowaySwitchEntityDescription, ...] = (
    CowaySwitchEntityDescription(
        key="light",
        translation_key="light",
        is_on_fn=lambda p: p.light_on,
        turn_on_fn=lambda c, a: c.client.async_set_light(a, light_on=True),
        turn_off_fn=lambda c, a: c.client.async_set_light(a, light_on=False),
        # 250S/IconS use a multi-mode light select instead.
        is_supported=lambda attr: not uses_light_mode_select(attr),
    ),
    CowaySwitchEntityDescription(
        key="button_lock",
        translation_key="button_lock",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=lambda p: p.button_lock == 1 if p.button_lock is not None else None,
        turn_on_fn=lambda c, a: c.client.async_set_button_lock(a, value="1"),
        turn_off_fn=lambda c, a: c.client.async_set_button_lock(a, value="0"),
        is_supported=lambda attr: detect_family(attr) == FAMILY_250S,
    ),
)


def _is_switch_supported(
    description: CowaySwitchEntityDescription, purifier: CowayPurifier
) -> bool:
    """Check whether a switch description applies to the given purifier."""
    return description.is_supported(purifier.device_attr)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CowayConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Coway switch entities."""
    coordinator = entry.runtime_data

    @callback
    def _async_add_purifiers(device_ids: list[str]) -> None:
        async_add_entities(
            CowaySwitch(coordinator, device_id, description)
            for device_id in device_ids
            for description in SWITCH_DESCRIPTIONS
            if _is_switch_supported(description, coordinator.data.purifiers[device_id])
        )

    async_remove_stale_entities(
        hass,
        entry,
        "switch",
        {
            f"{device_id}_{description.key}"
            for device_id, purifier in coordinator.data.purifiers.items()
            for description in SWITCH_DESCRIPTIONS
            if _is_switch_supported(description, purifier)
        },
    )
    async_track_new_purifiers(entry, _async_add_purifiers)


class CowaySwitch(CowayEntity, SwitchEntity):
    """Representation of a Coway switch."""

    entity_description: CowaySwitchEntityDescription

    def __init__(
        self,
        coordinator: CowayDataUpdateCoordinator,
        device_id: str,
        description: CowaySwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"
        self._optimistic_state: bool | None = None

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        if self._optimistic_state is not None:
            return self._optimistic_state
        return self.entity_description.is_on_fn(self.purifier)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Clear optimistic state when coordinator provides fresh data."""
        self._optimistic_state = None
        super()._handle_coordinator_update()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        await self._async_send_command(
            "turn on",
            self.entity_description.turn_on_fn(
                self.coordinator, self.purifier.device_attr
            ),
        )
        self._optimistic_state = True
        self.async_write_ha_state()
        self._schedule_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        await self._async_send_command(
            "turn off",
            self.entity_description.turn_off_fn(
                self.coordinator, self.purifier.device_attr
            ),
        )
        self._optimistic_state = False
        self.async_write_ha_state()
        self._schedule_refresh()
