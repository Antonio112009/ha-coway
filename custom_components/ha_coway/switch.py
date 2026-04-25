"""Switch platform for the Coway integration."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from pycoway import CowayError, CowayPurifier, DeviceAttributes

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import CowayConfigEntry, CowayDataUpdateCoordinator
from .devices import LIGHT_MODE_MODELS, MODEL_250S
from .entity import CowayEntity

_LOGGER = logging.getLogger(__name__)


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
    supported_models: frozenset[str] | None = field(default=None)
    excluded_models: frozenset[str] | None = field(default=None)


SWITCH_DESCRIPTIONS: tuple[CowaySwitchEntityDescription, ...] = (
    CowaySwitchEntityDescription(
        key="light",
        translation_key="light",
        is_on_fn=lambda p: p.light_on,
        turn_on_fn=lambda c, a: c.client.async_set_light(a, light_on=True),
        turn_off_fn=lambda c, a: c.client.async_set_light(a, light_on=False),
        excluded_models=LIGHT_MODE_MODELS,
    ),
    CowaySwitchEntityDescription(
        key="button_lock",
        translation_key="button_lock",
        is_on_fn=lambda p: p.button_lock == 1 if p.button_lock is not None else None,
        turn_on_fn=lambda c, a: c.client.async_set_button_lock(a, value="1"),
        turn_off_fn=lambda c, a: c.client.async_set_button_lock(a, value="0"),
        supported_models=frozenset({MODEL_250S}),
    ),
)


def _is_switch_supported(
    description: CowaySwitchEntityDescription, purifier: CowayPurifier
) -> bool:
    """Check whether a switch description applies to the given purifier."""
    model = purifier.device_attr.model
    if description.supported_models is not None:
        return model in description.supported_models
    if description.excluded_models is not None:
        return model not in description.excluded_models
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CowayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Coway switch entities."""
    coordinator = entry.runtime_data
    entities: list[CowaySwitch] = []
    valid_unique_ids: set[str] = set()
    for device_id, purifier in coordinator.data.purifiers.items():
        for description in SWITCH_DESCRIPTIONS:
            if not _is_switch_supported(description, purifier):
                continue
            unique_id = f"{device_id}_{description.key}"
            valid_unique_ids.add(unique_id)
            entities.append(CowaySwitch(coordinator, device_id, description))

    # Remove stale switch entities that are no longer provided
    ent_reg = er.async_get(hass)
    for ent_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if ent_entry.domain == "switch" and ent_entry.unique_id not in valid_unique_ids:
            ent_reg.async_remove(ent_entry.entity_id)

    async_add_entities(entities)


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
        if self._command_lock.locked():
            return
        async with self._command_lock:
            try:
                await self.entity_description.turn_on_fn(
                    self.coordinator, self.purifier.device_attr
                )
            except CowayError as err:
                _LOGGER.error("Failed to turn on %s: %s", self.entity_id, err)
                self._schedule_refresh()
                return
            self._optimistic_state = True
            self.async_write_ha_state()
            self._schedule_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        if self._command_lock.locked():
            return
        async with self._command_lock:
            try:
                await self.entity_description.turn_off_fn(
                    self.coordinator, self.purifier.device_attr
                )
            except CowayError as err:
                _LOGGER.error("Failed to turn off %s: %s", self.entity_id, err)
                self._schedule_refresh()
                return
            self._optimistic_state = False
            self.async_write_ha_state()
            self._schedule_refresh()
