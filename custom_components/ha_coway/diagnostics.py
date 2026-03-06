"""Diagnostics support for the Coway integration."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .coordinator import CowayConfigEntry

TO_REDACT = {
    CONF_PASSWORD,
    CONF_USERNAME,
    "title",
    "unique_id",
    "device_id",
    "place_id",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: CowayConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return async_redact_data(
        {
            "entry": entry.as_dict(),
            "purifiers": {
                f"purifier_{i}": asdict(purifier)
                for i, purifier in enumerate(coordinator.data.purifiers.values(), 1)
            },
        },
        TO_REDACT,
    )
