"""Model-specific device configuration for Coway purifiers."""

from pycoway import LightMode

# ── Model identification ──────────────────────────────────────────────

MODEL_AP_1512HHS = "AP-1512HHS"
MODEL_250S = "Airmega 250S"
MODEL_ICONS = "Airmega IconS"
MODEL_400S = "Airmega 400S"

# AP-1512HHS UK/EU device codes — these lack a pre-filter wash setting
# and use different filter names (Charcoal / HEPA instead of Pre / MAX2).
AP_1512HHS_UK_EU_CODES: frozenset[str] = frozenset({"02FMG", "02FMF", "02FWN"})

# Models that use a multi-mode light select instead of a simple on/off switch.
LIGHT_MODE_MODELS: frozenset[str] = frozenset({MODEL_250S, MODEL_ICONS})

# ── Fan preset modes ─────────────────────────────────────────────────

PRESET_AUTO = "auto"
PRESET_ECO = "eco"
PRESET_NIGHT = "night"
PRESET_RAPID = "rapid"
PRESET_AUTO_ECO = "auto_eco"

# Base preset modes per model (dynamic modes like auto_eco added at runtime).
AP_1512HHS_PRESET_MODES: list[str] = [PRESET_AUTO, PRESET_ECO]
MODEL_250S_PRESET_MODES: list[str] = [PRESET_AUTO, PRESET_NIGHT, PRESET_RAPID]
DEFAULT_PRESET_MODES: list[str] = [PRESET_AUTO, PRESET_NIGHT]

# 250S fan speeds that are not user-selectable (rapid=5, smart eco=9).
MODEL_250S_HIDDEN_SPEEDS: frozenset[int] = frozenset({5, 9})
MODEL_250S_AUTO_ECO_SPEED: int = 9

# ── Light mode configuration ─────────────────────────────────────────

LIGHT_MODE_OPTIONS_250S: list[str] = ["on", "off", "aqi_off"]
LIGHT_MODE_OPTIONS_ICONS: list[str] = ["on", "off", "aqi_off", "half_off"]

LIGHT_MODE_TO_API: dict[str, LightMode] = {
    "on": LightMode.ON,
    "off": LightMode.OFF,
    "aqi_off": LightMode.AQI_OFF,
    "half_off": LightMode.HALF_OFF,
}

API_TO_LIGHT_MODE: dict[int, str] = {
    0: "on",
    1: "aqi_off",
    2: "off",
    3: "half_off",
}
