"""Tests for the Coway coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from pycoway import CowayError, PasswordExpired

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_coway.const import DOMAIN
from custom_components.ha_coway.coordinator import CowayDataUpdateCoordinator

from .conftest import MOCK_ENTRY_DATA


async def test_coordinator_setup_success(
    hass: HomeAssistant,
    mock_coordinator_client: AsyncMock,
) -> None:
    """Test coordinator authenticates and fetches data successfully."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    entry.add_to_hass(hass)

    coordinator = CowayDataUpdateCoordinator(hass, entry)
    await coordinator._async_setup()

    mock_coordinator_client.login.assert_awaited_once()


async def test_coordinator_setup_auth_failed(
    hass: HomeAssistant,
    mock_coordinator_client: AsyncMock,
) -> None:
    """Test coordinator raises ConfigEntryAuthFailed on CowayError during login."""
    mock_coordinator_client.login.side_effect = CowayError("Login failed")

    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    entry.add_to_hass(hass)

    coordinator = CowayDataUpdateCoordinator(hass, entry)

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_setup()


async def test_coordinator_setup_password_expired(
    hass: HomeAssistant,
    mock_coordinator_client: AsyncMock,
) -> None:
    """Test coordinator raises ConfigEntryAuthFailed on PasswordExpired."""
    mock_coordinator_client.login.side_effect = PasswordExpired("Password expired")

    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    entry.add_to_hass(hass)

    coordinator = CowayDataUpdateCoordinator(hass, entry)

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_setup()


async def test_coordinator_update_success(
    hass: HomeAssistant,
    mock_coordinator_client: AsyncMock,
) -> None:
    """Test coordinator fetches purifier data successfully."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    entry.add_to_hass(hass)

    coordinator = CowayDataUpdateCoordinator(hass, entry)
    data = await coordinator._async_update_data()

    assert data is not None
    assert "ABC123" in data.purifiers
    assert data.purifiers["ABC123"].is_on is True
    mock_coordinator_client.async_get_purifiers_data.assert_awaited_once()


async def test_coordinator_update_failure(
    hass: HomeAssistant,
    mock_coordinator_client: AsyncMock,
) -> None:
    """Test coordinator raises UpdateFailed on CowayError during data fetch."""
    mock_coordinator_client.async_get_purifiers_data.side_effect = CowayError(
        "API error"
    )

    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    entry.add_to_hass(hass)

    coordinator = CowayDataUpdateCoordinator(hass, entry)

    with pytest.raises(UpdateFailed, match="Error fetching purifier data"):
        await coordinator._async_update_data()


async def test_coordinator_default_polling_interval(
    hass: HomeAssistant,
    mock_coordinator_client: AsyncMock,
) -> None:
    """Test coordinator uses default polling interval when not configured."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    entry.add_to_hass(hass)

    coordinator = CowayDataUpdateCoordinator(hass, entry)

    assert coordinator.update_interval.total_seconds() == 60


async def test_coordinator_custom_polling_interval(
    hass: HomeAssistant,
    mock_coordinator_client: AsyncMock,
) -> None:
    """Test coordinator uses custom polling interval from options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_ENTRY_DATA,
        options={"polling_interval": 120},
    )
    entry.add_to_hass(hass)

    coordinator = CowayDataUpdateCoordinator(hass, entry)

    assert coordinator.update_interval.total_seconds() == 120


async def test_coordinator_skip_password_change_default(
    hass: HomeAssistant,
) -> None:
    """Test coordinator defaults skip_password_change to True when not in data."""
    entry_data = {
        "username": "test@example.com",
        "password": "test_pass",
    }
    entry = MockConfigEntry(domain=DOMAIN, data=entry_data)
    entry.add_to_hass(hass)

    with patch(
        "custom_components.ha_coway.coordinator.CowayClient",
    ) as mock_client_class:
        CowayDataUpdateCoordinator(hass, entry)
        mock_client_class.assert_called_once()
        call_kwargs = mock_client_class.call_args
        assert call_kwargs.kwargs["skip_password_change"] is True
