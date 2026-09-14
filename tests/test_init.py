"""Tests for the Coway integration setup."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.ha_coway import async_remove_config_entry_device
from custom_components.ha_coway.const import DOMAIN

from .conftest import (
    MOCK_ENTRY_DATA,
    make_purifier,
    make_purifier_data,
    setup_coway_integration,
)


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
    from pycoway import AuthError

    mock_coordinator_client.login.side_effect = AuthError("Login failed")

    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR


async def test_setup_entry_transient_failure_retries(
    hass: HomeAssistant,
    mock_coordinator_client: AsyncMock,
) -> None:
    """A non-auth CowayError during setup leads to retry, not reauth."""
    from pycoway import CowayError

    mock_coordinator_client.login.side_effect = CowayError("Rate limited")

    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY


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


async def test_remove_device(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """A purifier the account no longer reports can be deleted, a live one not."""
    assert await async_setup_component(hass, "config", {})
    entry, _ = await setup_coway_integration(
        hass, make_purifier_data(make_purifier(device_id="ABC123"))
    )
    dev_reg = dr.async_get(hass)
    stale = dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(DOMAIN, "SOLD01")}
    )
    live = dev_reg.async_get_device_by_identifier((DOMAIN, "ABC123"), entry.entry_id)
    assert live is not None

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": "config/device_registry/remove_config_entry",
            "config_entry_id": entry.entry_id,
            "device_id": stale.id,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert dev_reg.async_get(stale.id) is None

    await client.send_json(
        {
            "id": 2,
            "type": "config/device_registry/remove_config_entry",
            "config_entry_id": entry.entry_id,
            "device_id": live.id,
        }
    )
    response = await client.receive_json()
    assert not response["success"]
    assert dev_reg.async_get(live.id) is not None


async def test_remove_device_refused_when_entry_not_loaded(
    hass: HomeAssistant,
) -> None:
    """Without a loaded entry there is nothing to check against, so refuse."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    entry.add_to_hass(hass)
    device_entry = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(DOMAIN, "ABC123")}
    )

    assert not await async_remove_config_entry_device(hass, entry, device_entry)
