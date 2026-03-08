"""Tests for the Coway fan platform."""

from __future__ import annotations

import pytest

from homeassistant.components.fan import (
    ATTR_PERCENTAGE,
    ATTR_PRESET_MODE,
    DOMAIN as FAN_DOMAIN,
    SERVICE_SET_PERCENTAGE,
    SERVICE_SET_PRESET_MODE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

from .conftest import make_purifier, make_purifier_data, setup_coway_integration

ENTITY_ID = "fan.living_room_purifier_purifier"


# ── Preset modes per model ────────────────────────────────────────────


async def test_preset_modes_ap1512hhs(hass: HomeAssistant) -> None:
    """AP-1512HHS always offers auto and eco presets."""
    data = make_purifier_data(make_purifier(model_code="AP-1512HHS"))
    entry, _ = await setup_coway_integration(hass, data)

    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert set(state.attributes["preset_modes"]) == {"auto", "eco"}


async def test_preset_modes_250s_without_auto_eco(hass: HomeAssistant) -> None:
    """250S shows auto/night/rapid but NOT auto_eco when fan_speed != 9."""
    data = make_purifier_data(
        make_purifier(
            model="Airmega 250S",
            model_code="250S",
            product_name="Airmega 250S",
            fan_speed=2,
        )
    )
    entry, _ = await setup_coway_integration(hass, data)

    state = hass.states.get(ENTITY_ID)
    modes = state.attributes["preset_modes"]
    assert "auto_eco" not in modes
    assert set(modes) == {"auto", "night", "rapid"}


async def test_preset_modes_250s_with_auto_eco(hass: HomeAssistant) -> None:
    """250S adds auto_eco when fan_speed == 9 (smart eco)."""
    data = make_purifier_data(
        make_purifier(
            model="Airmega 250S",
            model_code="250S",
            product_name="Airmega 250S",
            fan_speed=9,
        )
    )
    entry, _ = await setup_coway_integration(hass, data)

    state = hass.states.get(ENTITY_ID)
    modes = state.attributes["preset_modes"]
    assert "auto_eco" in modes


async def test_preset_modes_default_without_eco(hass: HomeAssistant) -> None:
    """Default model (400S/IconS) shows auto/night without auto_eco when eco_mode=False."""
    data = make_purifier_data(
        make_purifier(
            model="Airmega 400S",
            model_code="400S",
            product_name="Airmega 400S",
            eco_mode=False,
        )
    )
    entry, _ = await setup_coway_integration(hass, data)

    state = hass.states.get(ENTITY_ID)
    modes = state.attributes["preset_modes"]
    assert set(modes) == {"auto", "night"}


async def test_preset_modes_default_with_eco(hass: HomeAssistant) -> None:
    """Default model adds auto_eco when eco_mode=True."""
    data = make_purifier_data(
        make_purifier(
            model="Airmega 400S",
            model_code="400S",
            product_name="Airmega 400S",
            eco_mode=True,
        )
    )
    entry, _ = await setup_coway_integration(hass, data)

    state = hass.states.get(ENTITY_ID)
    modes = state.attributes["preset_modes"]
    assert "auto_eco" in modes


# ── Active preset mode detection ──────────────────────────────────────


async def test_preset_mode_ap1512hhs_auto(hass: HomeAssistant) -> None:
    """AP-1512HHS reports 'auto' when auto_mode is True."""
    data = make_purifier_data(
        make_purifier(model_code="AP-1512HHS", auto_mode=True)
    )
    entry, _ = await setup_coway_integration(hass, data)

    state = hass.states.get(ENTITY_ID)
    assert state.attributes.get("preset_mode") == "auto"


async def test_preset_mode_ap1512hhs_eco(hass: HomeAssistant) -> None:
    """AP-1512HHS reports 'eco' when eco_mode is True."""
    data = make_purifier_data(
        make_purifier(model_code="AP-1512HHS", eco_mode=True)
    )
    entry, _ = await setup_coway_integration(hass, data)

    state = hass.states.get(ENTITY_ID)
    assert state.attributes.get("preset_mode") == "eco"


async def test_preset_mode_250s_auto_eco(hass: HomeAssistant) -> None:
    """250S reports 'auto_eco' when fan_speed == 9."""
    data = make_purifier_data(
        make_purifier(
            model="Airmega 250S",
            model_code="250S",
            product_name="Airmega 250S",
            fan_speed=9,
        )
    )
    entry, _ = await setup_coway_integration(hass, data)

    state = hass.states.get(ENTITY_ID)
    assert state.attributes.get("preset_mode") == "auto_eco"


async def test_preset_mode_default_auto_eco(hass: HomeAssistant) -> None:
    """Default model reports 'auto_eco' when eco_mode is True."""
    data = make_purifier_data(
        make_purifier(
            model="Airmega 400S",
            model_code="400S",
            product_name="Airmega 400S",
            eco_mode=True,
        )
    )
    entry, _ = await setup_coway_integration(hass, data)

    state = hass.states.get(ENTITY_ID)
    assert state.attributes.get("preset_mode") == "auto_eco"


async def test_preset_mode_none_when_manual(hass: HomeAssistant) -> None:
    """preset_mode is None when purifier is in manual speed mode."""
    data = make_purifier_data(
        make_purifier(
            auto_mode=False,
            eco_mode=False,
            night_mode=False,
            fan_speed=2,
        )
    )
    entry, _ = await setup_coway_integration(hass, data)

    state = hass.states.get(ENTITY_ID)
    assert state.attributes.get("preset_mode") is None


# ── Speed percentage ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("fan_speed", "expected_pct"),
    [(1, 33), (2, 66), (3, 100)],
)
async def test_speed_percentage_mapping(
    hass: HomeAssistant,
    fan_speed: int,
    expected_pct: int,
) -> None:
    """Fan speed 1-3 maps to 33%-67%-100%."""
    data = make_purifier_data(make_purifier(fan_speed=fan_speed))
    entry, _ = await setup_coway_integration(hass, data)

    state = hass.states.get(ENTITY_ID)
    assert state.attributes["percentage"] == expected_pct


async def test_percentage_zero_when_off(hass: HomeAssistant) -> None:
    """Percentage is 0 when purifier is off."""
    data = make_purifier_data(make_purifier(is_on=False, fan_speed=2))
    entry, _ = await setup_coway_integration(hass, data)

    state = hass.states.get(ENTITY_ID)
    assert state.attributes["percentage"] == 0


async def test_percentage_zero_in_auto_eco(hass: HomeAssistant) -> None:
    """Percentage is 0 when in auto_eco mode (no meaningful speed)."""
    data = make_purifier_data(
        make_purifier(
            model="Airmega 400S",
            model_code="400S",
            product_name="Airmega 400S",
            eco_mode=True,
            fan_speed=0,
        )
    )
    entry, _ = await setup_coway_integration(hass, data)

    state = hass.states.get(ENTITY_ID)
    assert state.attributes["percentage"] == 0


@pytest.mark.parametrize("hidden_speed", [5, 9])
async def test_250s_hidden_speeds_show_zero_percent(
    hass: HomeAssistant,
    hidden_speed: int,
) -> None:
    """250S hidden speeds (rapid=5, smart eco=9) report 0%."""
    data = make_purifier_data(
        make_purifier(
            model="Airmega 250S",
            model_code="250S",
            product_name="Airmega 250S",
            fan_speed=hidden_speed,
        )
    )
    entry, _ = await setup_coway_integration(hass, data)

    state = hass.states.get(ENTITY_ID)
    assert state.attributes["percentage"] == 0


# ── Turn on / turn off ────────────────────────────────────────────────


async def test_turn_on_calls_api(hass: HomeAssistant) -> None:
    """Turning on calls async_set_power with is_on=True."""
    data = make_purifier_data(make_purifier(is_on=False))
    entry, mock_client = await setup_coway_integration(hass, data)

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    mock_client.async_set_power.assert_awaited_once()
    call_kwargs = mock_client.async_set_power.call_args
    assert call_kwargs.kwargs["is_on"] is True


async def test_turn_off_calls_api(hass: HomeAssistant) -> None:
    """Turning off calls async_set_power with is_on=False."""
    data = make_purifier_data(make_purifier(is_on=True))
    entry, mock_client = await setup_coway_integration(hass, data)

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    mock_client.async_set_power.assert_awaited_once()
    call_kwargs = mock_client.async_set_power.call_args
    assert call_kwargs.kwargs["is_on"] is False


async def test_turn_off_optimistic_state(hass: HomeAssistant) -> None:
    """Turning off optimistically sets is_on=False and light_on=False."""
    data = make_purifier_data(make_purifier(is_on=True, light_on=True))
    entry, mock_client = await setup_coway_integration(hass, data)

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    state = hass.states.get(ENTITY_ID)
    assert state.state == "off"


# ── Set speed percentage ──────────────────────────────────────────────


async def test_set_percentage_calls_api(hass: HomeAssistant) -> None:
    """Setting percentage sends the correct fan speed."""
    data = make_purifier_data(make_purifier(is_on=True, fan_speed=1))
    entry, mock_client = await setup_coway_integration(hass, data)

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PERCENTAGE: 100},
        blocking=True,
    )

    mock_client.async_set_fan_speed.assert_awaited_once()
    call_kwargs = mock_client.async_set_fan_speed.call_args
    assert call_kwargs.kwargs["speed"] == "3"


async def test_set_percentage_zero_turns_off(hass: HomeAssistant) -> None:
    """Setting percentage to 0 turns the purifier off."""
    data = make_purifier_data(make_purifier(is_on=True, fan_speed=2))
    entry, mock_client = await setup_coway_integration(hass, data)

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PERCENTAGE: 0},
        blocking=True,
    )

    mock_client.async_set_power.assert_awaited_once()
    call_kwargs = mock_client.async_set_power.call_args
    assert call_kwargs.kwargs["is_on"] is False


async def test_set_percentage_clears_mode_flags(hass: HomeAssistant) -> None:
    """Setting speed clears auto/night/eco mode flags optimistically."""
    data = make_purifier_data(
        make_purifier(is_on=True, auto_mode=True, eco_mode=True, night_mode=True)
    )
    entry, mock_client = await setup_coway_integration(hass, data)

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PERCENTAGE: 67},
        blocking=True,
    )

    # After setting speed, preset_mode should be None (all modes cleared)
    state = hass.states.get(ENTITY_ID)
    assert state.attributes.get("preset_mode") is None


# ── Set preset mode ───────────────────────────────────────────────────


async def test_set_preset_auto_calls_api(hass: HomeAssistant) -> None:
    """Setting preset 'auto' calls async_set_auto_mode."""
    data = make_purifier_data(make_purifier(is_on=True))
    entry, mock_client = await setup_coway_integration(hass, data)

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: "auto"},
        blocking=True,
    )

    mock_client.async_set_auto_mode.assert_awaited_once()


async def test_set_preset_eco_calls_api(hass: HomeAssistant) -> None:
    """Setting preset 'eco' calls async_set_eco_mode (AP-1512HHS)."""
    data = make_purifier_data(
        make_purifier(model_code="AP-1512HHS", is_on=True)
    )
    entry, mock_client = await setup_coway_integration(hass, data)

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: "eco"},
        blocking=True,
    )

    mock_client.async_set_eco_mode.assert_awaited_once()


async def test_set_preset_auto_eco_calls_eco_api(hass: HomeAssistant) -> None:
    """Setting preset 'auto_eco' calls async_set_eco_mode (same API as eco)."""
    data = make_purifier_data(
        make_purifier(
            model="Airmega 400S",
            model_code="400S",
            product_name="Airmega 400S",
            is_on=True,
            eco_mode=True,  # so auto_eco appears in preset_modes
        )
    )
    entry, mock_client = await setup_coway_integration(hass, data)

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: "auto_eco"},
        blocking=True,
    )

    mock_client.async_set_eco_mode.assert_awaited_once()


async def test_set_preset_night_calls_api(hass: HomeAssistant) -> None:
    """Setting preset 'night' calls async_set_night_mode."""
    data = make_purifier_data(
        make_purifier(
            model="Airmega 400S",
            model_code="400S",
            product_name="Airmega 400S",
            is_on=True,
        )
    )
    entry, mock_client = await setup_coway_integration(hass, data)

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: "night"},
        blocking=True,
    )

    mock_client.async_set_night_mode.assert_awaited_once()


async def test_set_preset_rapid_calls_api(hass: HomeAssistant) -> None:
    """Setting preset 'rapid' calls async_set_rapid_mode (250S)."""
    data = make_purifier_data(
        make_purifier(
            model="Airmega 250S",
            model_code="250S",
            product_name="Airmega 250S",
            is_on=True,
        )
    )
    entry, mock_client = await setup_coway_integration(hass, data)

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: "rapid"},
        blocking=True,
    )

    mock_client.async_set_rapid_mode.assert_awaited_once()


async def test_set_preset_auto_optimistic_state(hass: HomeAssistant) -> None:
    """Setting 'auto' optimistically sets auto_mode=True and fan_speed=1."""
    data = make_purifier_data(make_purifier(is_on=True, fan_speed=3))
    entry, mock_client = await setup_coway_integration(hass, data)

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: "auto"},
        blocking=True,
    )

    state = hass.states.get(ENTITY_ID)
    assert state.attributes.get("preset_mode") == "auto"
    # fan_speed=1 → 33%
    assert state.attributes["percentage"] == 33


async def test_set_preset_eco_optimistic_state(hass: HomeAssistant) -> None:
    """Setting 'eco' optimistically sets eco_mode=True and fan_speed=0."""
    data = make_purifier_data(
        make_purifier(model_code="AP-1512HHS", is_on=True, fan_speed=2)
    )
    entry, mock_client = await setup_coway_integration(hass, data)

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: "eco"},
        blocking=True,
    )

    state = hass.states.get(ENTITY_ID)
    assert state.attributes.get("preset_mode") == "eco"


# ── Availability ──────────────────────────────────────────────────────


async def test_fan_unavailable_when_network_down(hass: HomeAssistant) -> None:
    """Fan entity is unavailable when purifier network_status is False."""
    data = make_purifier_data(make_purifier(network_status=False))
    entry, _ = await setup_coway_integration(hass, data)

    state = hass.states.get(ENTITY_ID)
    assert state.state == "unavailable"
