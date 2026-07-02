"""Model-specific device configuration for Coway purifiers."""

from pycoway import DeviceAttributes, LightMode

# ── Model identification ──────────────────────────────────────────────
#
# pycoway's IoT path never populates ``DeviceAttributes.model``, and which
# of the remaining identity fields carries a recognisable model name varies
# by API response. Families are therefore detected by scanning every
# identity field for a distinctive fragment.

FAMILY_AP_1512HHS = "ap_1512hhs"
FAMILY_250S = "250s"
FAMILY_ICONS = "icons"

_FAMILY_PATTERNS: tuple[tuple[str, str], ...] = (
    ("1512", FAMILY_AP_1512HHS),
    ("250", FAMILY_250S),
    ("icon", FAMILY_ICONS),
)


def detect_family(attr: DeviceAttributes) -> str | None:
    """Return the model family, or None for models with default behavior."""
    for value in (attr.model, attr.model_code, attr.product_name, attr.prod_name_full):
        if not value:
            continue
        lowered = value.lower()
        for pattern, family in _FAMILY_PATTERNS:
            if pattern in lowered:
                return family
    return None


def uses_light_mode_select(attr: DeviceAttributes) -> bool:
    """Multi-mode light models get a select instead of an on/off switch."""
    return detect_family(attr) in (FAMILY_250S, FAMILY_ICONS)


# AP-1512HHS UK/EU device codes — these lack a pre-filter wash setting
# and use different filter names (Charcoal / HEPA instead of Pre / MAX2).
AP_1512HHS_UK_EU_CODES: frozenset[str] = frozenset({"02FMG", "02FMF", "02FWN"})

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
