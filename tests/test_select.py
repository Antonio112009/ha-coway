"""Tests for the Coway select platform."""

from __future__ import annotations

from homeassistant.components.select import DOMAIN as SELECT_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

from custom_components.ha_coway.select import _get_select_descriptions

from .conftest import make_purifier, make_purifier_data, setup_coway_integration

SELECT_PREFIX = "select.living_room_purifier"
TIMER_ENTITY = f"{SELECT_PREFIX}_off_timer"
SENSITIVITY_ENTITY = f"{SELECT_PREFIX}_smart_mode_sensitivity"
LIGHT_MODE_ENTITY = f"{SELECT_PREFIX}_light_mode"
PRE_FILTER_FREQ_ENTITY = f"{SELECT_PREFIX}_pre_filter_wash_frequency"


# ── _get_select_descriptions unit tests ───────────────────────────────


def test_common_selects_always_present() -> None:
    """Timer and sensitivity selects are available for all models."""
    purifier = make_purifier()
    descs = _get_select_descriptions(purifier)
    keys = [d.key for d in descs]
    assert "timer" in keys
    assert "sensitivity" in keys


def test_light_mode_present_for_250s() -> None:
    """250S model gets a light_mode select."""
    purifier = make_purifier(
        model="Airmega 250S", model_code="250S", product_name="Airmega 250S"
    )
    descs = _get_select_descriptions(purifier)
    keys = [d.key for d in descs]
    assert "light_mode" in keys


def test_light_mode_present_for_icons() -> None:
    """IconS model gets a light_mode select."""
    purifier = make_purifier(
        model="Airmega IconS", model_code="IconS", product_name="Airmega IconS"
    )
    descs = _get_select_descriptions(purifier)
    keys = [d.key for d in descs]
    assert "light_mode" in keys


def test_light_mode_absent_for_ap1512hhs() -> None:
    """AP-1512HHS does NOT get a light_mode select (uses light switch)."""
    purifier = make_purifier()
    descs = _get_select_descriptions(purifier)
    keys = [d.key for d in descs]
    assert "light_mode" not in keys


def test_250s_light_mode_options() -> None:
    """250S light_mode has on/off/aqi_off options (no half_off)."""
    purifier = make_purifier(
        model="Airmega 250S", model_code="250S", product_name="Airmega 250S"
    )
    descs = _get_select_descriptions(purifier)
    light_desc = next(d for d in descs if d.key == "light_mode")
    assert light_desc.options == ["on", "off", "aqi_off"]


def test_icons_light_mode_options() -> None:
    """IconS light_mode has on/off/aqi_off/half_off options."""
    purifier = make_purifier(
        model="Airmega IconS", model_code="IconS", product_name="Airmega IconS"
    )
    descs = _get_select_descriptions(purifier)
    light_desc = next(d for d in descs if d.key == "light_mode")
    assert light_desc.options == ["on", "off", "aqi_off", "half_off"]


def test_pre_filter_frequency_present_for_standard() -> None:
    """Standard models with pre_filter_change_frequency get the select."""
    purifier = make_purifier(pre_filter_change_frequency=2)
    descs = _get_select_descriptions(purifier)
    keys = [d.key for d in descs]
    assert "pre_filter_frequency" in keys


def test_pre_filter_frequency_excluded_for_uk_eu() -> None:
    """UK/EU AP-1512HHS models do NOT get pre_filter_frequency select."""
    purifier = make_purifier(code="02FMG", pre_filter_change_frequency=2)
    descs = _get_select_descriptions(purifier)
    keys = [d.key for d in descs]
    assert "pre_filter_frequency" not in keys


def test_pre_filter_frequency_excluded_when_none() -> None:
    """pre_filter_frequency excluded when the purifier reports None."""
    purifier = make_purifier(pre_filter_change_frequency=None)
    descs = _get_select_descriptions(purifier)
    keys = [d.key for d in descs]
    assert "pre_filter_frequency" not in keys


# ── Select current_fn unit tests ──────────────────────────────────────


def test_timer_current_fn_off() -> None:
    """Timer returns 'off' when timer value is '0'."""
    purifier = make_purifier(timer="0")
    descs = _get_select_descriptions(purifier)
    timer_desc = next(d for d in descs if d.key == "timer")
    assert timer_desc.current_fn(purifier) == "off"


def test_timer_current_fn_active() -> None:
    """Timer returns the raw value when timer is set."""
    purifier = make_purifier(timer="120")
    descs = _get_select_descriptions(purifier)
    timer_desc = next(d for d in descs if d.key == "timer")
    assert timer_desc.current_fn(purifier) == "120"


def test_timer_current_fn_none() -> None:
    """Timer returns None when timer value is None."""
    purifier = make_purifier(timer=None)
    descs = _get_select_descriptions(purifier)
    timer_desc = next(d for d in descs if d.key == "timer")
    assert timer_desc.current_fn(purifier) is None


def test_sensitivity_current_fn() -> None:
    """Sensitivity maps API int to human label."""
    purifier = make_purifier(smart_mode_sensitivity=2)
    descs = _get_select_descriptions(purifier)
    sens_desc = next(d for d in descs if d.key == "sensitivity")
    assert sens_desc.current_fn(purifier) == "moderate"


def test_sensitivity_current_fn_none() -> None:
    """Sensitivity returns None when value is None."""
    purifier = make_purifier(smart_mode_sensitivity=None)
    descs = _get_select_descriptions(purifier)
    sens_desc = next(d for d in descs if d.key == "sensitivity")
    assert sens_desc.current_fn(purifier) is None


def test_light_mode_current_fn() -> None:
    """Light mode maps API int to label."""
    purifier = make_purifier(
        model="Airmega 250S",
        model_code="250S",
        product_name="Airmega 250S",
        light_mode=2,
    )
    descs = _get_select_descriptions(purifier)
    lm_desc = next(d for d in descs if d.key == "light_mode")
    assert lm_desc.current_fn(purifier) == "off"


# ── Integration-level select tests ────────────────────────────────────


async def test_timer_select_exists(hass: HomeAssistant) -> None:
    """Timer select entity is created."""
    await setup_coway_integration(hass)

    state = hass.states.get(TIMER_ENTITY)
    assert state is not None
    assert state.state == "off"  # timer="0" maps to "off"


async def test_sensitivity_select_value(hass: HomeAssistant) -> None:
    """Sensitivity select shows the correct mapped value."""
    data = make_purifier_data(make_purifier(smart_mode_sensitivity=1))
    await setup_coway_integration(hass, data)

    state = hass.states.get(SENSITIVITY_ENTITY)
    assert state is not None
    assert state.state == "sensitive"


async def test_light_mode_select_for_250s(hass: HomeAssistant) -> None:
    """250S has a light_mode select with correct options."""
    data = make_purifier_data(
        make_purifier(
            model="Airmega 250S",
            model_code="250S",
            product_name="Airmega 250S",
            light_mode=0,
        )
    )
    await setup_coway_integration(hass, data)

    state = hass.states.get(LIGHT_MODE_ENTITY)
    assert state is not None
    assert state.state == "on"  # light_mode=0 → "on"


async def test_select_option_calls_api(hass: HomeAssistant) -> None:
    """Selecting a timer option calls the API."""
    data = make_purifier_data(make_purifier())
    entry, mock_client = await setup_coway_integration(hass, data)

    await hass.services.async_call(
        SELECT_DOMAIN,
        "select_option",
        {ATTR_ENTITY_ID: TIMER_ENTITY, "option": "120"},
        blocking=True,
    )

    mock_client.async_set_timer.assert_awaited_once()


async def test_select_optimistic_value(hass: HomeAssistant) -> None:
    """After selecting an option, the optimistic value is reflected immediately."""
    data = make_purifier_data(make_purifier(timer="0"))
    entry, mock_client = await setup_coway_integration(hass, data)

    await hass.services.async_call(
        SELECT_DOMAIN,
        "select_option",
        {ATTR_ENTITY_ID: TIMER_ENTITY, "option": "240"},
        blocking=True,
    )

    state = hass.states.get(TIMER_ENTITY)
    assert state.state == "240"
