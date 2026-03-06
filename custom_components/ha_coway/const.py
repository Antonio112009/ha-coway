"""Constants for the Coway integration."""

from homeassistant.const import Platform

DOMAIN = "ha_coway"

CONF_SKIP_PASSWORD_CHANGE = "skip_password_change"
CONF_POLLING_INTERVAL = "polling_interval"
DEFAULT_POLLING_INTERVAL = 60

# Delay (seconds) after a command before polling cloud for updated state.
COMMAND_REFRESH_DELAY = 3
# Delay (seconds) between sequential API commands (e.g., power on + set speed).
COMMAND_CHAIN_DELAY = 2

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.FAN,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]
