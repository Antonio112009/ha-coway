"""Constants for the Coway integration."""

from homeassistant.const import Platform

DOMAIN = "coway"

CONF_SKIP_PASSWORD_CHANGE = "skip_password_change"

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.FAN,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]
