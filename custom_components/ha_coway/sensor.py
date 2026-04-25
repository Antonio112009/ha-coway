"""Sensor platform for the Coway integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from pycoway import CowayPurifier

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
    LIGHT_LUX,
    PERCENTAGE,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import CowayConfigEntry, CowayDataUpdateCoordinator
from .devices import AP_1512HHS_UK_EU_CODES, MODEL_250S
from .entity import CowayEntity

AQ_GRADE_MAP = {
    1: "good",
    2: "moderate",
    3: "unhealthy",
    4: "very_unhealthy",
}


@dataclass(frozen=True, kw_only=True)
class CowaySensorEntityDescription(SensorEntityDescription):
    """Describe a Coway sensor entity."""

    value_fn: Callable[[CowayPurifier], int | str | None]


# --- Standard descriptions (used for most models) ---

PM2_5_DESCRIPTION = CowaySensorEntityDescription(
    key="pm2_5",
    translation_key="pm2_5",
    native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    device_class=SensorDeviceClass.PM25,
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda p: p.particulate_matter_2_5,
)

PM10_DESCRIPTION = CowaySensorEntityDescription(
    key="pm10",
    translation_key="pm10",
    native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    device_class=SensorDeviceClass.PM10,
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda p: p.particulate_matter_10,
)

PRE_FILTER_DESCRIPTION = CowaySensorEntityDescription(
    key="pre_filter",
    translation_key="pre_filter",
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda p: p.pre_filter_pct,
)

MAX2_FILTER_DESCRIPTION = CowaySensorEntityDescription(
    key="max2_filter",
    translation_key="max2_filter",
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda p: p.max2_pct,
)

LUX_DESCRIPTION = CowaySensorEntityDescription(
    key="lux",
    translation_key="lux",
    native_unit_of_measurement=LIGHT_LUX,
    device_class=SensorDeviceClass.ILLUMINANCE,
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda p: p.lux_sensor,
)

# --- AP-1512HHS UK/EU alternates ---

CHARCOAL_FILTER_DESCRIPTION = CowaySensorEntityDescription(
    key="pre_filter",
    translation_key="charcoal_filter",
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda p: p.odor_filter_pct,
)

HEPA_FILTER_DESCRIPTION = CowaySensorEntityDescription(
    key="max2_filter",
    translation_key="hepa_filter",
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda p: p.max2_pct,
)

# --- 250S lux (inverted sensor) ---

LUX_INVERTED_DESCRIPTION = CowaySensorEntityDescription(
    key="lux",
    translation_key="lux",
    native_unit_of_measurement=LIGHT_LUX,
    device_class=SensorDeviceClass.ILLUMINANCE,
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda p: (
        max(1022 - p.lux_sensor, 0) if p.lux_sensor is not None else None
    ),
)

# --- Descriptions common to all models ---

COMMON_DESCRIPTIONS: tuple[CowaySensorEntityDescription, ...] = (
    CowaySensorEntityDescription(
        key="co2",
        translation_key="co2",
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda p: p.carbon_dioxide,
    ),
    CowaySensorEntityDescription(
        key="voc",
        translation_key="voc",
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda p: p.volatile_organic_compounds,
    ),
    CowaySensorEntityDescription(
        key="aqi",
        translation_key="aqi",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda p: p.air_quality_index,
    ),
    CowaySensorEntityDescription(
        key="odor_filter",
        translation_key="odor_filter",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda p: p.odor_filter_pct,
    ),
    CowaySensorEntityDescription(
        key="timer_remaining",
        translation_key="timer_remaining",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda p: p.timer_remaining,
    ),
    CowaySensorEntityDescription(
        key="indoor_aq",
        translation_key="indoor_aq",
        device_class=SensorDeviceClass.ENUM,
        options=["good", "moderate", "unhealthy", "very_unhealthy"],
        value_fn=lambda p: AQ_GRADE_MAP.get(p.aq_grade),
    ),
)


def _get_sensor_descriptions(
    purifier: CowayPurifier,
) -> list[CowaySensorEntityDescription]:
    """Build model-specific sensor descriptions for a purifier."""
    model = purifier.device_attr.model
    code = purifier.device_attr.code
    product_name = purifier.device_attr.product_name
    is_uk_eu_ap = code in AP_1512HHS_UK_EU_CODES

    descriptions: list[CowaySensorEntityDescription] = []

    # PM2.5 — exclude for generic AIRMEGA models (no dedicated PM2.5 sensor)
    if product_name != "AIRMEGA":
        descriptions.append(PM2_5_DESCRIPTION)

    descriptions.append(PM10_DESCRIPTION)

    # Pre-filter / Charcoal filter
    descriptions.append(
        CHARCOAL_FILTER_DESCRIPTION if is_uk_eu_ap else PRE_FILTER_DESCRIPTION
    )

    # MAX2 / HEPA filter
    descriptions.append(
        HEPA_FILTER_DESCRIPTION if is_uk_eu_ap else MAX2_FILTER_DESCRIPTION
    )

    # Lux — 250S has an inverted sensor
    if model == MODEL_250S:
        descriptions.append(LUX_INVERTED_DESCRIPTION)
    else:
        descriptions.append(LUX_DESCRIPTION)

    descriptions.extend(COMMON_DESCRIPTIONS)
    return descriptions


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CowayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Coway sensor entities."""
    coordinator = entry.runtime_data
    entities: list[CowaySensor] = []
    valid_unique_ids: set[str] = set()
    current_device_ids = set(coordinator.data.purifiers)
    for device_id, purifier in coordinator.data.purifiers.items():
        for description in _get_sensor_descriptions(purifier):
            unique_id = f"{device_id}_{description.key}"
            if description.value_fn(purifier) is None:
                continue
            valid_unique_ids.add(unique_id)
            entities.append(CowaySensor(coordinator, device_id, description))

    # Remove stale sensor entities for the *current* devices that are no longer
    # provided by the cloud. We deliberately leave entities belonging to devices
    # that are missing from this update untouched, in case the device is just
    # temporarily unreachable.
    ent_reg = er.async_get(hass)
    for ent_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if ent_entry.domain != "sensor":
            continue
        if ent_entry.unique_id in valid_unique_ids:
            continue
        if not any(
            ent_entry.unique_id.startswith(f"{device_id}_")
            for device_id in current_device_ids
        ):
            continue
        ent_reg.async_remove(ent_entry.entity_id)

    async_add_entities(entities)


class CowaySensor(CowayEntity, SensorEntity):
    """Representation of a Coway sensor."""

    entity_description: CowaySensorEntityDescription

    def __init__(
        self,
        coordinator: CowayDataUpdateCoordinator,
        device_id: str,
        description: CowaySensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"

    @property
    def native_value(self) -> int | str | None:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.purifier)
