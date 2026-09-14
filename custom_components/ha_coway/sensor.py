"""Sensor platform for the Coway integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

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
    EntityCategory,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pycoway import CowayPurifier

from .const import DOMAIN
from .coordinator import CowayConfigEntry, CowayDataUpdateCoordinator
from .devices import AP_1512HHS_UK_EU_CODES, FAMILY_250S, detect_family
from .entity import (
    CowayEntity,
    async_remove_stale_entities,
    async_track_new_purifiers,
)

PARALLEL_UPDATES = 0  # Read-only platform; data arrives via the coordinator

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
    entity_category=EntityCategory.DIAGNOSTIC,
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda p: p.pre_filter_pct,
)

MAX2_FILTER_DESCRIPTION = CowaySensorEntityDescription(
    key="max2_filter",
    translation_key="max2_filter",
    native_unit_of_measurement=PERCENTAGE,
    entity_category=EntityCategory.DIAGNOSTIC,
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
    entity_category=EntityCategory.DIAGNOSTIC,
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda p: p.odor_filter_pct,
)

HEPA_FILTER_DESCRIPTION = CowaySensorEntityDescription(
    key="max2_filter",
    translation_key="hepa_filter",
    native_unit_of_measurement=PERCENTAGE,
    entity_category=EntityCategory.DIAGNOSTIC,
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
    # Coway reports VOC as a unitless level index (``VOCs_IDX``), not a
    # concentration, so no VOC device class: those require µg/m³ or ppb.
    CowaySensorEntityDescription(
        key="voc",
        translation_key="voc",
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
        entity_category=EntityCategory.DIAGNOSTIC,
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
        value_fn=lambda p: (
            AQ_GRADE_MAP.get(p.aq_grade) if p.aq_grade is not None else None
        ),
    ),
)


def _get_sensor_descriptions(
    purifier: CowayPurifier,
) -> list[CowaySensorEntityDescription]:
    """Build model-specific sensor descriptions for a purifier."""
    family = detect_family(purifier.device_attr)
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
    if family == FAMILY_250S:
        descriptions.append(LUX_INVERTED_DESCRIPTION)
    else:
        descriptions.append(LUX_DESCRIPTION)

    descriptions.extend(COMMON_DESCRIPTIONS)
    return descriptions


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CowayConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Coway sensor entities."""
    coordinator = entry.runtime_data
    ent_reg = er.async_get(hass)

    @callback
    def _async_add_purifiers(device_ids: list[str]) -> None:
        entities: list[CowaySensor] = []
        for device_id in device_ids:
            purifier = coordinator.data.purifiers[device_id]
            for description in _get_sensor_descriptions(purifier):
                unique_id = f"{device_id}_{description.key}"
                # A None value normally means the model lacks this sensor, but
                # it can also be a transient gap (device off or unreachable).
                # Keep entities that already exist in the registry so history
                # and customizations survive a badly-timed reload.
                if description.value_fn(
                    purifier
                ) is None and not ent_reg.async_get_entity_id(
                    "sensor", DOMAIN, unique_id
                ):
                    continue
                entities.append(CowaySensor(coordinator, device_id, description))
        async_add_entities(entities)

    async_remove_stale_entities(
        hass,
        entry,
        "sensor",
        {
            f"{device_id}_{description.key}"
            for device_id, purifier in coordinator.data.purifiers.items()
            for description in _get_sensor_descriptions(purifier)
        },
    )
    async_track_new_purifiers(entry, _async_add_purifiers)


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
