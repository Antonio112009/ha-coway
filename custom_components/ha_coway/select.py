"""Select platform for the Coway integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from pycoway import CowayPurifier, DeviceAttributes

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import CowayConfigEntry, CowayDataUpdateCoordinator
from .entity import CowayEntity

TIMER_OPTIONS = ["off", "60", "120", "240", "480"]
SENSITIVITY_OPTIONS = ["sensitive", "moderate", "insensitive"]
PRE_FILTER_FREQUENCY_OPTIONS = ["2", "3", "4"]
_SENSITIVITY_TO_API = {"sensitive": "1", "moderate": "2", "insensitive": "3"}
_API_TO_SENSITIVITY = {1: "sensitive", 2: "moderate", 3: "insensitive"}


@dataclass(frozen=True, kw_only=True)
class CowaySelectEntityDescription(SelectEntityDescription):
    """Describe a Coway select entity."""

    current_fn: Callable[[CowayPurifier], str | None]
    select_fn: Callable[
        [CowayDataUpdateCoordinator, DeviceAttributes, str], Awaitable[None]
    ]


TIMER_DESCRIPTION = CowaySelectEntityDescription(
    key="timer",
    translation_key="timer",
    options=TIMER_OPTIONS,
    current_fn=lambda p: (
        ("off" if p.timer == "0" else p.timer) if p.timer is not None else None
    ),
    select_fn=lambda c, a, v: c.client.async_set_timer(
        a, time="0" if v == "off" else v
    ),
)

SENSITIVITY_DESCRIPTION = CowaySelectEntityDescription(
    key="sensitivity",
    translation_key="sensitivity",
    options=SENSITIVITY_OPTIONS,
    current_fn=lambda p: (
        _API_TO_SENSITIVITY.get(p.smart_mode_sensitivity)
        if p.smart_mode_sensitivity is not None
        else None
    ),
    select_fn=lambda c, a, v: c.client.async_set_smart_mode_sensitivity(
        a, sensitivity=_SENSITIVITY_TO_API[v]
    ),
)

PRE_FILTER_FREQUENCY_DESCRIPTION = CowaySelectEntityDescription(
    key="pre_filter_frequency",
    translation_key="pre_filter_frequency",
    options=PRE_FILTER_FREQUENCY_OPTIONS,
    current_fn=lambda p: (
        str(p.pre_filter_change_frequency)
        if p.pre_filter_change_frequency is not None
        else None
    ),
    select_fn=lambda c, a, v: c.client.async_change_prefilter_setting(a, int(v)),
)

SELECT_DESCRIPTIONS: tuple[CowaySelectEntityDescription, ...] = (
    TIMER_DESCRIPTION,
    SENSITIVITY_DESCRIPTION,
    PRE_FILTER_FREQUENCY_DESCRIPTION,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CowayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Coway select entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        CowaySelect(coordinator, device_id, description)
        for device_id in coordinator.data.purifiers
        for description in SELECT_DESCRIPTIONS
    )


class CowaySelect(CowayEntity, SelectEntity):
    """Representation of a Coway select."""

    entity_description: CowaySelectEntityDescription

    def __init__(
        self,
        coordinator: CowayDataUpdateCoordinator,
        device_id: str,
        description: CowaySelectEntityDescription,
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"
        self._optimistic_value: str | None = None

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if self._optimistic_value is not None:
            return self._optimistic_value
        return self.entity_description.current_fn(self.purifier)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Clear optimistic value when coordinator provides fresh data."""
        self._optimistic_value = None
        super()._handle_coordinator_update()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.entity_description.select_fn(
            self.coordinator, self.purifier.device_attr, option
        )
        self._optimistic_value = option
        self.async_write_ha_state()
