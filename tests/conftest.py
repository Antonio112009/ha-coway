"""Fixtures for Coway integration tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from pycoway import CowayPurifier, DeviceAttributes, PurifierData

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_coway.const import CONF_SKIP_PASSWORD_CHANGE, DOMAIN

MOCK_USERNAME = "test@example.com"
MOCK_PASSWORD = "test_password"  # noqa: S105

MOCK_ENTRY_DATA = {
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PASSWORD: MOCK_PASSWORD,
    CONF_SKIP_PASSWORD_CHANGE: True,
}

MOCK_USER_INPUT = {
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PASSWORD: MOCK_PASSWORD,
    CONF_SKIP_PASSWORD_CHANGE: True,
}


def make_purifier(
    *,
    device_id: str = "ABC123",
    model: str = "AIRMEGA AP-1512HHS",
    model_code: str = "AP-1512HHS",
    code: str = "100100",
    name: str = "Living Room Purifier",
    product_name: str = "AIRMEGA AP-1512HHS",
    **overrides,
) -> CowayPurifier:
    """Create a CowayPurifier with sane defaults and optional field overrides."""
    defaults = dict(
        mcu_version="1.0.0",
        network_status=True,
        is_on=True,
        auto_mode=False,
        eco_mode=False,
        night_mode=False,
        rapid_mode=False,
        fan_speed=2,
        light_on=True,
        light_mode=0,
        button_lock=0,
        timer="0",
        timer_remaining=0,
        pre_filter_pct=85,
        max2_pct=90,
        odor_filter_pct=75,
        aq_grade=1,
        particulate_matter_2_5=15,
        particulate_matter_10=25,
        carbon_dioxide=450,
        volatile_organic_compounds=100,
        air_quality_index=50,
        lux_sensor=300,
        pre_filter_change_frequency=2,
        smart_mode_sensitivity=1,
        filters=None,
    )
    defaults.update(overrides)
    device_attr = DeviceAttributes(
        device_id=device_id,
        model=model,
        model_code=model_code,
        code=code,
        name=name,
        product_name=product_name,
        place_id="place_001",
    )
    return CowayPurifier(device_attr=device_attr, **defaults)


def make_purifier_data(*purifiers: CowayPurifier) -> PurifierData:
    """Wrap one or more purifiers in a PurifierData object."""
    if not purifiers:
        purifiers = (make_purifier(),)
    return PurifierData(purifiers={p.device_attr.device_id: p for p in purifiers})


def mock_purifier_data() -> PurifierData:
    """Create default AP-1512HHS mock purifier data (backward-compatible)."""
    return make_purifier_data(make_purifier(auto_mode=True))


async def setup_coway_integration(
    hass: HomeAssistant,
    purifier_data: PurifierData | None = None,
) -> tuple[MockConfigEntry, AsyncMock]:
    """Set up the Coway integration and return (entry, mock_client)."""
    if purifier_data is None:
        purifier_data = mock_purifier_data()

    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    entry.add_to_hass(hass)

    with patch(
        "custom_components.ha_coway.coordinator.CowayClient",
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.async_get_purifiers_data = AsyncMock(
            return_value=purifier_data,
        )
        mock_client_class.return_value = mock_client

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry, mock_client


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_coway_client():
    """Mock CowayClient used in config_flow."""
    with patch(
        "custom_components.ha_coway.config_flow.CowayClient",
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_coordinator_client():
    """Mock CowayClient used in coordinator."""
    with patch(
        "custom_components.ha_coway.coordinator.CowayClient",
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.login = AsyncMock()
        mock_client.async_get_purifiers_data = AsyncMock(
            return_value=mock_purifier_data()
        )
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_setup_entry():
    """Mock async_setup_entry to avoid full platform setup."""
    with patch(
        "custom_components.ha_coway.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock
