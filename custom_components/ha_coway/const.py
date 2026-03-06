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

# Model identification
MODEL_AP_1512HHS = "AP-1512HHS"
MODEL_250S = "Airmega 250S"
MODEL_ICONS = "Airmega IconS"
MODEL_400S = "Airmega 400S"

# AP-1512HHS UK/EU device codes — these lack a pre-filter wash setting
# and use different filter names (Charcoal / HEPA instead of Pre / MAX2).
AP_1512HHS_UK_EU_CODES: frozenset[str] = frozenset({"02FMG", "02FMF", "02FWN"})

# Models that use a multi-mode light select instead of a simple on/off switch
LIGHT_MODE_MODELS: frozenset[str] = frozenset({MODEL_250S, MODEL_ICONS})
