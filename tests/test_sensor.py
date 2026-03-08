"""Tests for the Coway sensor platform."""

from __future__ import annotations

import pytest

from homeassistant.core import HomeAssistant

from custom_components.ha_coway.sensor import (
    AQ_GRADE_MAP,
    _get_sensor_descriptions,
)

from .conftest import make_purifier, make_purifier_data, setup_coway_integration

SENSOR_PREFIX = "sensor.living_room_purifier"


# ── _get_sensor_descriptions unit tests ───────────────────────────────


def test_standard_model_includes_pm25() -> None:
    """Standard model with a real product_name includes PM2.5 sensor."""
    purifier = make_purifier()
    descs = _get_sensor_descriptions(purifier)
    keys = [d.key for d in descs]
    assert "pm2_5" in keys


def test_generic_airmega_excludes_pm25() -> None:
    """Generic AIRMEGA product_name excludes PM2.5 sensor."""
    purifier = make_purifier(product_name="AIRMEGA")
    descs = _get_sensor_descriptions(purifier)
    keys = [d.key for d in descs]
    assert "pm2_5" not in keys


def test_uk_eu_uses_charcoal_and_hepa_filters() -> None:
    """AP-1512HHS UK/EU models use charcoal/hepa filter names."""
    purifier = make_purifier(code="02FMG")
    descs = _get_sensor_descriptions(purifier)
    translation_keys = [d.translation_key for d in descs]
    assert "charcoal_filter" in translation_keys
    assert "hepa_filter" in translation_keys
    assert "pre_filter" not in translation_keys
    assert "max2_filter" not in translation_keys


def test_standard_model_uses_pre_and_max2_filters() -> None:
    """Standard models use pre_filter and max2_filter names."""
    purifier = make_purifier(code="100100")
    descs = _get_sensor_descriptions(purifier)
    translation_keys = [d.translation_key for d in descs]
    assert "pre_filter" in translation_keys
    assert "max2_filter" in translation_keys
    assert "charcoal_filter" not in translation_keys


def test_250s_uses_inverted_lux() -> None:
    """250S model uses inverted lux sensor (1022 - reading)."""
    purifier = make_purifier(
        model="Airmega 250S",
        model_code="250S",
        product_name="Airmega 250S",
        lux_sensor=300,
    )
    descs = _get_sensor_descriptions(purifier)
    lux_desc = next(d for d in descs if d.key == "lux")
    # Inverted: 1022 - 300 = 722
    assert lux_desc.value_fn(purifier) == 722


def test_standard_model_uses_direct_lux() -> None:
    """Non-250S models use direct lux reading."""
    purifier = make_purifier(lux_sensor=300)
    descs = _get_sensor_descriptions(purifier)
    lux_desc = next(d for d in descs if d.key == "lux")
    assert lux_desc.value_fn(purifier) == 300


def test_inverted_lux_clamps_to_zero() -> None:
    """Inverted lux never goes below zero."""
    purifier = make_purifier(
        model="Airmega 250S",
        model_code="250S",
        product_name="Airmega 250S",
        lux_sensor=2000,
    )
    descs = _get_sensor_descriptions(purifier)
    lux_desc = next(d for d in descs if d.key == "lux")
    assert lux_desc.value_fn(purifier) == 0


def test_inverted_lux_none_value() -> None:
    """Inverted lux returns None when sensor is None."""
    purifier = make_purifier(
        model="Airmega 250S",
        model_code="250S",
        product_name="Airmega 250S",
        lux_sensor=None,
    )
    descs = _get_sensor_descriptions(purifier)
    lux_desc = next(d for d in descs if d.key == "lux")
    assert lux_desc.value_fn(purifier) is None


def test_common_descriptions_always_present() -> None:
    """CO2, VOC, AQI, odor_filter, timer_remaining, indoor_aq are always included."""
    purifier = make_purifier()
    descs = _get_sensor_descriptions(purifier)
    keys = {d.key for d in descs}
    for expected in ("co2", "voc", "aqi", "odor_filter", "timer_remaining", "indoor_aq"):
        assert expected in keys, f"{expected} missing from sensor descriptions"


# ── AQ grade mapping ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("grade", "label"),
    [(1, "good"), (2, "moderate"), (3, "unhealthy"), (4, "very_unhealthy")],
)
def test_aq_grade_map(grade: int, label: str) -> None:
    """Air quality grade maps to the correct label."""
    assert AQ_GRADE_MAP[grade] == label


def test_aq_grade_unknown_returns_none() -> None:
    """Unknown AQ grade returns None."""
    assert AQ_GRADE_MAP.get(99) is None


# ── Sensor value functions ────────────────────────────────────────────


def test_sensor_value_functions_return_correct_data() -> None:
    """Each sensor value_fn returns the correct purifier attribute."""
    purifier = make_purifier(
        particulate_matter_2_5=42,
        particulate_matter_10=88,
        carbon_dioxide=600,
        volatile_organic_compounds=150,
        air_quality_index=75,
        pre_filter_pct=60,
        max2_pct=80,
        odor_filter_pct=55,
        timer_remaining=30,
        aq_grade=2,
    )
    descs = _get_sensor_descriptions(purifier)
    values = {d.key: d.value_fn(purifier) for d in descs}

    assert values["pm2_5"] == 42
    assert values["pm10"] == 88
    assert values["co2"] == 600
    assert values["voc"] == 150
    assert values["aqi"] == 75
    assert values["pre_filter"] == 60
    assert values["max2_filter"] == 80
    assert values["odor_filter"] == 55
    assert values["timer_remaining"] == 30
    assert values["indoor_aq"] == "moderate"


# ── Integration-level sensor tests ────────────────────────────────────


async def test_sensors_are_created(hass: HomeAssistant) -> None:
    """Sensors are registered when the integration is set up."""
    data = make_purifier_data(make_purifier())
    await setup_coway_integration(hass, data)

    # Check a few key sensors exist
    assert hass.states.get(f"{SENSOR_PREFIX}_pm2_5") is not None
    assert hass.states.get(f"{SENSOR_PREFIX}_pm10") is not None
    assert hass.states.get(f"{SENSOR_PREFIX}_co2") is not None


async def test_sensor_values_match_purifier_data(hass: HomeAssistant) -> None:
    """Sensor states reflect the purifier data values."""
    data = make_purifier_data(
        make_purifier(particulate_matter_2_5=42, carbon_dioxide=600)
    )
    await setup_coway_integration(hass, data)

    pm25 = hass.states.get(f"{SENSOR_PREFIX}_pm2_5")
    assert pm25 is not None
    assert pm25.state == "42"

    co2 = hass.states.get(f"{SENSOR_PREFIX}_co2")
    assert co2 is not None
    assert co2.state == "600"


async def test_sensor_with_none_value_not_created(hass: HomeAssistant) -> None:
    """Sensors whose value_fn returns None are not created."""
    data = make_purifier_data(make_purifier(carbon_dioxide=None))
    await setup_coway_integration(hass, data)

    # CO2 has None value so should not exist
    assert hass.states.get(f"{SENSOR_PREFIX}_co2") is None


async def test_indoor_aq_enum_value(hass: HomeAssistant) -> None:
    """indoor_aq sensor reports the grade label."""
    data = make_purifier_data(make_purifier(aq_grade=3))
    await setup_coway_integration(hass, data)

    state = hass.states.get(f"{SENSOR_PREFIX}_indoor_air_quality")
    assert state is not None
    assert state.state == "unhealthy"
