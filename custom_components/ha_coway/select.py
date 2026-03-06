"""Select platform for the Coway integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from pycoway import CowayPurifier, DeviceAttributes

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import CowayConfigEntry, CowayDataUpdateCoordinator
from .devices import (
    AP_1512HHS_UK_EU_CODES,
    API_TO_LIGHT_MODE,
    LIGHT_MODE_MODELS,
    LIGHT_MODE_OPTIONS_250S,
    LIGHT_MODE_OPTIONS_ICONS,
    LIGHT_MODE_TO_API,
    MODEL_250S,
)
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

# Common selects for all models
COMMON_DESCRIPTIONS: tuple[CowaySelectEntityDescription, ...] = (
    TIMER_DESCRIPTION,
    SENSITIVITY_DESCRIPTION,
)


def _get_select_descriptions(
    purifier: CowayPurifier,
) -> list[CowaySelectEntityDescription]:
    """Build model-specific select descriptions for a purifier."""
    descriptions: list[CowaySelectEntityDescription] = list(COMMON_DESCRIPTIONS)
    model = purifier.device_attr.model
    code = purifier.device_attr.code

    # Light mode select for 250S/IconS (these use multi-mode light instead of switch)
    if model in LIGHT_MODE_MODELS:
        options = (
            LIGHT_MODE_OPTIONS_250S if model == MODEL_250S else LIGHT_MODE_OPTIONS_ICONS
        )
        descriptions.append(
            CowaySelectEntityDescription(
                key="light_mode",
                translation_key="light_mode",
                options=options,
                current_fn=lambda p: (
                    API_TO_LIGHT_MODE.get(p.light_mode)
                    if p.light_mode is not None
                    else None
                ),
                select_fn=lambda c, a, v: c.client.async_set_light_mode(
                    a, light_mode=LIGHT_MODE_TO_API[v]
                ),
            )
        )

    # Pre-filter frequency: exclude AP-1512HHS UK/EU models
    if (
        purifier.pre_filter_change_frequency is not None
        and code not in AP_1512HHS_UK_EU_CODES
    ):
        descriptions.append(PRE_FILTER_FREQUENCY_DESCRIPTION)

    return descriptions


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CowayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Coway select entities."""
    coordinator = entry.runtime_data
    entities: list[CowaySelect] = []
    for device_id, purifier in coordinator.data.purifiers.items():
        for description in _get_select_descriptions(purifier):
            entities.append(CowaySelect(coordinator, device_id, description))
    async_add_entities(entities)


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
        if self._command_in_progress:
            return
        self._command_in_progress = True
        await self.entity_description.select_fn(
            self.coordinator, self.purifier.device_attr, option
        )
        self._optimistic_value = option
        self.async_write_ha_state()
        self._schedule_refresh()
