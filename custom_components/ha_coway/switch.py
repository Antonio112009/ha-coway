"""Switch platform for the Coway integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from pycoway import CowayPurifier, DeviceAttributes

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import CowayConfigEntry, CowayDataUpdateCoordinator
from .entity import CowayEntity


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


SWITCH_DESCRIPTIONS: tuple[CowaySwitchEntityDescription, ...] = (
    CowaySwitchEntityDescription(
        key="light",
        translation_key="light",
        is_on_fn=lambda p: p.light_on,
        turn_on_fn=lambda c, a: c.client.async_set_light(a, light_on=True),
        turn_off_fn=lambda c, a: c.client.async_set_light(a, light_on=False),
    ),
    CowaySwitchEntityDescription(
        key="button_lock",
        translation_key="button_lock",
        is_on_fn=lambda p: p.button_lock == 1 if p.button_lock is not None else None,
        turn_on_fn=lambda c, a: c.client.async_set_button_lock(a, value="1"),
        turn_off_fn=lambda c, a: c.client.async_set_button_lock(a, value="0"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CowayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Coway switch entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        CowaySwitch(coordinator, device_id, description)
        for device_id in coordinator.data.purifiers
        for description in SWITCH_DESCRIPTIONS
    )


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
        await self.entity_description.turn_on_fn(
            self.coordinator, self.purifier.device_attr
        )
        self._optimistic_state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        await self.entity_description.turn_off_fn(
            self.coordinator, self.purifier.device_attr
        )
        self._optimistic_state = False
        self.async_write_ha_state()
