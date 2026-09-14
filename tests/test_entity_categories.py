"""Entity categories: configuration and diagnostic entities are classified."""

from __future__ import annotations

import pytest
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .conftest import make_purifier, make_purifier_data, setup_coway_integration


@pytest.mark.parametrize(
    ("entity_id", "category"),
    [
        ("fan.living_room_purifier", None),
        ("switch.living_room_purifier_button_lock", EntityCategory.CONFIG),
        ("select.living_room_purifier_smart_mode_sensitivity", EntityCategory.CONFIG),
        (
            "select.living_room_purifier_pre_filter_wash_frequency",
            EntityCategory.CONFIG,
        ),
        ("select.living_room_purifier_off_timer", None),
        ("select.living_room_purifier_light_mode", None),
        ("sensor.living_room_purifier_pre_filter", EntityCategory.DIAGNOSTIC),
        ("sensor.living_room_purifier_max2_filter", EntityCategory.DIAGNOSTIC),
        ("sensor.living_room_purifier_odor_filter", EntityCategory.DIAGNOSTIC),
        ("sensor.living_room_purifier_pm10", None),
        ("binary_sensor.living_room_purifier_network", EntityCategory.DIAGNOSTIC),
    ],
)
async def test_entity_category(
    hass: HomeAssistant, entity_id: str, category: EntityCategory | None
) -> None:
    """Config and diagnostic entities carry the matching category."""
    purifier = make_purifier(
        model="Airmega 250S", model_code="250S", product_name="AIRMEGA 250S"
    )
    await setup_coway_integration(hass, make_purifier_data(purifier))

    entry = er.async_get(hass).async_get(entity_id)
    assert entry is not None, entity_id
    assert entry.entity_category == category
