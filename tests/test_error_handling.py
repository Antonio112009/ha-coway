"""Tests for command error handling and concurrency safety."""

from __future__ import annotations

import asyncio

import pytest
from pycoway import CowayError

from homeassistant.components.fan import (
    ATTR_PERCENTAGE,
    DOMAIN as FAN_DOMAIN,
    SERVICE_SET_PERCENTAGE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.components.select import (
    DOMAIN as SELECT_DOMAIN,
    SERVICE_SELECT_OPTION,
)
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_ON as SVC_TURN_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.ha_coway.const import DOMAIN

from .conftest import make_purifier, make_purifier_data, setup_coway_integration

FAN_ENTITY = "fan.living_room_purifier_purifier"
LIGHT_ENTITY = "switch.living_room_purifier_light"
TIMER_ENTITY = "select.living_room_purifier_off_timer"


# ── Error handling: API failures don't desync optimistic state ────────


async def test_fan_turn_on_api_error_does_not_change_state(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """A CowayError on turn_on must not flip is_on optimistically."""
    data = make_purifier_data(make_purifier(is_on=False))
    _, mock_client = await setup_coway_integration(hass, data)
    mock_client.async_set_power.side_effect = CowayError("boom")

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: FAN_ENTITY},
        blocking=True,
    )

    state = hass.states.get(FAN_ENTITY)
    assert state.state == "off"  # unchanged
    assert "Failed to turn on" in caplog.text


async def test_fan_turn_off_api_error_does_not_change_state(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """A CowayError on turn_off must not flip is_on optimistically."""
    data = make_purifier_data(make_purifier(is_on=True))
    _, mock_client = await setup_coway_integration(hass, data)
    mock_client.async_set_power.side_effect = CowayError("boom")

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: FAN_ENTITY},
        blocking=True,
    )

    state = hass.states.get(FAN_ENTITY)
    assert state.state == "on"  # unchanged
    assert "Failed to turn off" in caplog.text


async def test_fan_set_speed_api_error_does_not_change_state(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """A CowayError on set_fan_speed must not change percentage optimistically."""
    data = make_purifier_data(make_purifier(is_on=True, fan_speed=1))
    _, mock_client = await setup_coway_integration(hass, data)
    mock_client.async_set_fan_speed.side_effect = CowayError("boom")

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: FAN_ENTITY, ATTR_PERCENTAGE: 100},
        blocking=True,
    )

    state = hass.states.get(FAN_ENTITY)
    # fan_speed=1 -> 33%
    assert state.attributes["percentage"] == 33
    assert "Failed to set speed" in caplog.text


async def test_switch_turn_on_api_error_does_not_change_state(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """A CowayError on switch turn_on must not flip the optimistic state."""
    data = make_purifier_data(make_purifier(light_on=False))
    _, mock_client = await setup_coway_integration(hass, data)
    mock_client.async_set_light.side_effect = CowayError("boom")

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SVC_TURN_ON,
        {ATTR_ENTITY_ID: LIGHT_ENTITY},
        blocking=True,
    )

    state = hass.states.get(LIGHT_ENTITY)
    assert state.state == "off"  # unchanged
    assert "Failed to turn on" in caplog.text


async def test_select_option_api_error_does_not_change_state(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """A CowayError on select must not change current_option optimistically."""
    data = make_purifier_data(make_purifier(timer="0"))
    _, mock_client = await setup_coway_integration(hass, data)
    mock_client.async_set_timer.side_effect = CowayError("boom")

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: TIMER_ENTITY, "option": "60"},
        blocking=True,
    )

    state = hass.states.get(TIMER_ENTITY)
    assert state.state == "off"  # unchanged
    assert "Failed to set timer" in caplog.text


# ── Concurrency: lock prevents overlapping commands ───────────────────


async def test_fan_concurrent_commands_are_serialized(hass: HomeAssistant) -> None:
    """Second command issued while one is running is dropped (lock held)."""
    data = make_purifier_data(make_purifier(is_on=True, fan_speed=1))
    _, mock_client = await setup_coway_integration(hass, data)

    # Block the API call until we release it.
    release = asyncio.Event()
    call_count = 0

    async def slow_set_fan_speed(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        await release.wait()

    mock_client.async_set_fan_speed.side_effect = slow_set_fan_speed

    first = hass.async_create_task(
        hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_SET_PERCENTAGE,
            {ATTR_ENTITY_ID: FAN_ENTITY, ATTR_PERCENTAGE: 100},
            blocking=True,
        )
    )
    # Yield so first command grabs the lock.
    await asyncio.sleep(0)

    # Second command should hit the lock-held branch and return immediately.
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: FAN_ENTITY, ATTR_PERCENTAGE: 33},
        blocking=True,
    )
    assert call_count == 1  # second was dropped

    release.set()
    await first


# ── Availability: missing device in coordinator data ──────────────────


async def test_entity_unavailable_when_device_disappears(
    hass: HomeAssistant,
) -> None:
    """Entities become unavailable (not error) when a device leaves the data."""
    purifier = make_purifier()
    data = make_purifier_data(purifier)
    entry, mock_client = await setup_coway_integration(hass, data)

    # Coordinator now reports no purifiers (device disappeared upstream).
    mock_client.async_get_purifiers_data.return_value = make_purifier_data(
        make_purifier(device_id="OTHER_DEVICE")
    )
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    state = hass.states.get(FAN_ENTITY)
    assert state is not None
    assert state.state == "unavailable"


# ── Migration: v1 → v2 fan unique_id ──────────────────────────────────


async def test_v1_fan_unique_id_is_migrated(hass: HomeAssistant) -> None:
    """Pre-existing fan entity with bare device_id unique_id is migrated."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from .conftest import MOCK_ENTRY_DATA

    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA, version=1)
    entry.add_to_hass(hass)

    ent_reg = er.async_get(hass)
    # Seed an entity with the legacy unique_id format (bare device_id).
    ent_reg.async_get_or_create(
        domain=FAN_DOMAIN,
        platform=DOMAIN,
        unique_id="ABC123",
        config_entry=entry,
    )

    data = make_purifier_data(make_purifier(device_id="ABC123"))
    from unittest.mock import AsyncMock, patch

    with patch(
        "custom_components.ha_coway.coordinator.CowayClient",
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.async_get_purifiers_data = AsyncMock(return_value=data)
        mock_client_class.return_value = mock_client
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # Entity should now have the migrated unique_id.
    migrated = ent_reg.async_get_entity_id(FAN_DOMAIN, DOMAIN, "ABC123_purifier")
    assert migrated is not None
    assert ent_reg.async_get_entity_id(FAN_DOMAIN, DOMAIN, "ABC123") is None
    assert entry.version == 2
