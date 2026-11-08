"""Home Assistant's timezone is handed to pycoway.

Without it pycoway detects the system timezone by reading files, which
would be blocking I/O inside the event loop.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_coway.const import DOMAIN

from .conftest import MOCK_ENTRY_DATA, MOCK_USER_INPUT, mock_purifier_data


async def test_coordinator_passes_ha_timezone(hass: HomeAssistant) -> None:
    """The coordinator's client uses the timezone configured in HA."""
    await hass.config.async_set_time_zone("Europe/London")
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    entry.add_to_hass(hass)
    with patch("custom_components.ha_coway.coordinator.CowayClient") as client_class:
        client_class.return_value.async_get_purifiers_data = AsyncMock(
            return_value=mock_purifier_data()
        )
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert client_class.call_args.kwargs["timezone"] == "Europe/London"


async def test_config_flow_passes_ha_timezone(hass: HomeAssistant) -> None:
    """The client that validates credentials uses HA's timezone too."""
    await hass.config.async_set_time_zone("Asia/Seoul")
    with (
        patch("custom_components.ha_coway.config_flow.CowayClient") as client_class,
        patch("custom_components.ha_coway.async_setup_entry", return_value=True),
    ):
        client = client_class.return_value
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_INPUT
        )

    assert client_class.call_args.kwargs["timezone"] == "Asia/Seoul"
