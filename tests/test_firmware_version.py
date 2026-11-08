"""The device registry follows the purifier's firmware version."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from custom_components.ha_coway.const import DOMAIN

from .conftest import make_purifier, make_purifier_data, setup_coway_integration


async def test_firmware_version_follows_updates(hass: HomeAssistant) -> None:
    """A new version is stored; an unknown one keeps the last known."""
    entry, mock_client = await setup_coway_integration(
        hass, make_purifier_data(make_purifier(mcu_version="1.0.0"))
    )
    dev_reg = dr.async_get(hass)

    def sw_version() -> str | None:
        device = dev_reg.async_get_device_by_identifier(
            (DOMAIN, "ABC123"), entry.entry_id
        )
        assert device is not None
        return device.sw_version

    assert sw_version() == "1.0.0"

    mock_client.async_get_purifiers_data.return_value = make_purifier_data(
        make_purifier(mcu_version="1.1.0")
    )
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert sw_version() == "1.1.0"

    mock_client.async_get_purifiers_data.return_value = make_purifier_data(
        make_purifier(mcu_version=None)
    )
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert sw_version() == "1.1.0"


async def test_firmware_version_filled_in_after_failed_first_scrape(
    hass: HomeAssistant,
) -> None:
    """A version missing at setup appears once a poll reports it."""
    entry, mock_client = await setup_coway_integration(
        hass, make_purifier_data(make_purifier(mcu_version=None))
    )
    mock_client.async_get_purifiers_data.return_value = make_purifier_data(
        make_purifier(mcu_version="2.0.0")
    )
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, "ABC123"), entry.entry_id
    )
    assert device is not None
    assert device.sw_version == "2.0.0"
