"""Tests for the Coway switch platform."""

from __future__ import annotations

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.core import HomeAssistant

from custom_components.ha_coway.switch import _is_switch_supported, SWITCH_DESCRIPTIONS

from .conftest import make_purifier, make_purifier_data, setup_coway_integration

LIGHT_ENTITY = "switch.living_room_purifier_light"
LOCK_ENTITY = "switch.living_room_purifier_button_lock"


# ── _is_switch_supported unit tests ───────────────────────────────────


def test_light_switch_supported_for_ap1512hhs() -> None:
    """Light switch is available for AP-1512HHS."""
    purifier = make_purifier(model_code="AP-1512HHS")
    light_desc = SWITCH_DESCRIPTIONS[0]  # light
    assert _is_switch_supported(light_desc, purifier) is True


def test_light_switch_excluded_for_250s() -> None:
    """Light switch is excluded for 250S (uses light_mode select instead)."""
    purifier = make_purifier(
        model="Airmega 250S", model_code="250S", product_name="Airmega 250S"
    )
    light_desc = SWITCH_DESCRIPTIONS[0]
    assert _is_switch_supported(light_desc, purifier) is False


def test_light_switch_excluded_for_icons() -> None:
    """Light switch is excluded for IconS (uses light_mode select instead)."""
    purifier = make_purifier(
        model="Airmega IconS", model_code="IconS", product_name="Airmega IconS"
    )
    light_desc = SWITCH_DESCRIPTIONS[0]
    assert _is_switch_supported(light_desc, purifier) is False


def test_button_lock_supported_for_250s() -> None:
    """Button lock switch is available for 250S."""
    purifier = make_purifier(
        model="Airmega 250S", model_code="250S", product_name="Airmega 250S"
    )
    lock_desc = SWITCH_DESCRIPTIONS[1]  # button_lock
    assert _is_switch_supported(lock_desc, purifier) is True


def test_button_lock_not_supported_for_others() -> None:
    """Button lock switch is not available for AP-1512HHS."""
    purifier = make_purifier(model_code="AP-1512HHS")
    lock_desc = SWITCH_DESCRIPTIONS[1]
    assert _is_switch_supported(lock_desc, purifier) is False


def test_button_lock_not_supported_for_400s() -> None:
    """Button lock switch is not available for 400S."""
    purifier = make_purifier(
        model="Airmega 400S", model_code="400S", product_name="Airmega 400S"
    )
    lock_desc = SWITCH_DESCRIPTIONS[1]
    assert _is_switch_supported(lock_desc, purifier) is False


# ── Integration-level switch tests ────────────────────────────────────


async def test_ap1512hhs_has_light_no_lock(hass: HomeAssistant) -> None:
    """AP-1512HHS should have light switch but NOT button lock."""
    data = make_purifier_data(make_purifier())
    await setup_coway_integration(hass, data)

    assert hass.states.get(LIGHT_ENTITY) is not None
    assert hass.states.get(LOCK_ENTITY) is None


async def test_250s_has_lock_no_light(hass: HomeAssistant) -> None:
    """250S should have button lock but NOT light switch (uses select)."""
    data = make_purifier_data(
        make_purifier(
            model="Airmega 250S",
            model_code="250S",
            product_name="Airmega 250S",
        )
    )
    await setup_coway_integration(hass, data)

    assert hass.states.get(LOCK_ENTITY) is not None
    assert hass.states.get(LIGHT_ENTITY) is None


async def test_light_switch_on_calls_api(hass: HomeAssistant) -> None:
    """Turning on the light switch calls async_set_light(light_on=True)."""
    data = make_purifier_data(make_purifier(light_on=False))
    entry, mock_client = await setup_coway_integration(hass, data)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: LIGHT_ENTITY},
        blocking=True,
    )

    mock_client.async_set_light.assert_awaited_once()
    call_kwargs = mock_client.async_set_light.call_args
    assert call_kwargs.kwargs["light_on"] is True


async def test_light_switch_off_calls_api(hass: HomeAssistant) -> None:
    """Turning off the light switch calls async_set_light(light_on=False)."""
    data = make_purifier_data(make_purifier(light_on=True))
    entry, mock_client = await setup_coway_integration(hass, data)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: LIGHT_ENTITY},
        blocking=True,
    )

    mock_client.async_set_light.assert_awaited_once()
    call_kwargs = mock_client.async_set_light.call_args
    assert call_kwargs.kwargs["light_on"] is False


async def test_light_switch_state_reflects_data(hass: HomeAssistant) -> None:
    """Light switch state matches purifier.light_on."""
    data = make_purifier_data(make_purifier(light_on=True))
    await setup_coway_integration(hass, data)

    state = hass.states.get(LIGHT_ENTITY)
    assert state.state == "on"


async def test_button_lock_state_on(hass: HomeAssistant) -> None:
    """Button lock reads as 'on' when button_lock == 1."""
    data = make_purifier_data(
        make_purifier(
            model="Airmega 250S",
            model_code="250S",
            product_name="Airmega 250S",
            button_lock=1,
        )
    )
    await setup_coway_integration(hass, data)

    state = hass.states.get(LOCK_ENTITY)
    assert state.state == "on"


async def test_button_lock_state_off(hass: HomeAssistant) -> None:
    """Button lock reads as 'off' when button_lock == 0."""
    data = make_purifier_data(
        make_purifier(
            model="Airmega 250S",
            model_code="250S",
            product_name="Airmega 250S",
            button_lock=0,
        )
    )
    await setup_coway_integration(hass, data)

    state = hass.states.get(LOCK_ENTITY)
    assert state.state == "off"
