"""Constants for the Coway integration."""

from homeassistant.const import Platform

DOMAIN = "ha_coway"

CONF_SKIP_PASSWORD_CHANGE = "skip_password_change"
CONF_POLLING_INTERVAL = "polling_interval"
DEFAULT_POLLING_INTERVAL = 60

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.FAN,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]
