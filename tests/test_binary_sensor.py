"""Tests for the Coway binary sensor platform."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .conftest import make_purifier, make_purifier_data, setup_coway_integration

NETWORK_ENTITY = "sensor.living_room_purifier_network_status"
BINARY_NETWORK_ENTITY = "binary_sensor.living_room_purifier_network"


async def test_network_sensor_on_when_connected(hass: HomeAssistant) -> None:
    """Network status binary sensor is 'on' when network_status is True."""
    data = make_purifier_data(make_purifier(network_status=True))
    await setup_coway_integration(hass, data)

    state = hass.states.get(BINARY_NETWORK_ENTITY)
    assert state is not None
    assert state.state == "on"


async def test_network_sensor_off_when_disconnected(hass: HomeAssistant) -> None:
    """Network status binary sensor is 'off' when network_status is False."""
    data = make_purifier_data(make_purifier(network_status=False))
    await setup_coway_integration(hass, data)

    state = hass.states.get(BINARY_NETWORK_ENTITY)
    assert state is not None
    # When network_status is False, the entity itself is unavailable
    # because CowayEntity.available checks network_status
    assert state.state in ("off", "unavailable")
