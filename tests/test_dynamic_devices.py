"""A purifier paired after setup shows up without a reload."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .conftest import make_purifier, make_purifier_data, setup_coway_integration

NEW_DEVICE_ENTITIES = (
    "fan.bedroom_purifier",
    "binary_sensor.bedroom_purifier_network",
    "sensor.bedroom_purifier_pm10",
    "select.bedroom_purifier_off_timer",
    "switch.bedroom_purifier_light",
)


async def test_new_purifier_is_added_on_next_poll(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Entities for a purifier that appears in a later update are created."""
    living_room = make_purifier(device_id="ABC123", name="Living Room Purifier")
    entry, mock_client = await setup_coway_integration(
        hass, make_purifier_data(living_room)
    )
    for entity_id in NEW_DEVICE_ENTITIES:
        assert hass.states.get(entity_id) is None

    bedroom = make_purifier(device_id="XYZ789", name="Bedroom Purifier")
    mock_client.async_get_purifiers_data.return_value = make_purifier_data(
        living_room, bedroom
    )
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    for entity_id in NEW_DEVICE_ENTITIES:
        assert hass.states.get(entity_id) is not None, entity_id

    # A further poll with the same purifiers must not create duplicates.
    ent_reg = er.async_get(hass)
    count = len(er.async_entries_for_config_entry(ent_reg, entry.entry_id))
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert len(er.async_entries_for_config_entry(ent_reg, entry.entry_id)) == count
    assert "already exists" not in caplog.text
