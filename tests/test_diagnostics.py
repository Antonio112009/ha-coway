"""Tests for the Coway diagnostics."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_coway.const import DOMAIN
from custom_components.ha_coway.diagnostics import async_get_config_entry_diagnostics

from .conftest import MOCK_ENTRY_DATA


async def test_diagnostics_redacts_sensitive_data(
    hass: HomeAssistant,
    mock_coordinator_client: AsyncMock,
) -> None:
    """Test that diagnostics redacts sensitive fields."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    # Verify sensitive entry data is redacted
    entry_data = diagnostics["entry"]["data"]
    assert entry_data["username"] == "**REDACTED**"
    assert entry_data["password"] == "**REDACTED**"

    # Verify purifier data is present
    assert "purifiers" in diagnostics
    assert "purifier_1" in diagnostics["purifiers"]

    # Verify device_id and place_id are redacted in purifier data
    purifier = diagnostics["purifiers"]["purifier_1"]
    assert purifier["device_attr"]["device_id"] == "**REDACTED**"
    assert purifier["device_attr"]["place_id"] == "**REDACTED**"
