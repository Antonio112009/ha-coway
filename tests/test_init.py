"""Tests for the Coway integration setup."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_coway.const import DOMAIN

from .conftest import MOCK_ENTRY_DATA


async def test_setup_entry(
    hass: HomeAssistant,
    mock_coordinator_client: AsyncMock,
) -> None:
    """Test successful setup of a config entry."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data is not None


async def test_setup_entry_auth_failure(
    hass: HomeAssistant,
    mock_coordinator_client: AsyncMock,
) -> None:
    """Test setup fails when authentication fails."""
    from pycoway import CowayError

    mock_coordinator_client.login.side_effect = CowayError("Login failed")

    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR


async def test_unload_entry(
    hass: HomeAssistant,
    mock_coordinator_client: AsyncMock,
) -> None:
    """Test unloading a config entry."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
