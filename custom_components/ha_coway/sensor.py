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
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import CowayConfigEntry, CowayDataUpdateCoordinator
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


SENSOR_DESCRIPTIONS: tuple[CowaySensorEntityDescription, ...] = (
    CowaySensorEntityDescription(
        key="pm2_5",
        translation_key="pm2_5",
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        device_class=SensorDeviceClass.PM25,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda p: p.particulate_matter_2_5,
    ),
    CowaySensorEntityDescription(
        key="pm10",
        translation_key="pm10",
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        device_class=SensorDeviceClass.PM10,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda p: p.particulate_matter_10,
    ),
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
        key="pre_filter",
        translation_key="pre_filter",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda p: p.pre_filter_pct,
    ),
    CowaySensorEntityDescription(
        key="max2_filter",
        translation_key="max2_filter",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda p: p.max2_pct,
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
        key="lux",
        translation_key="lux",
        native_unit_of_measurement=LIGHT_LUX,
        device_class=SensorDeviceClass.ILLUMINANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda p: p.lux_sensor,
    ),
    CowaySensorEntityDescription(
        key="indoor_aq",
        translation_key="indoor_aq",
        device_class=SensorDeviceClass.ENUM,
        options=["good", "moderate", "unhealthy", "very_unhealthy"],
        value_fn=lambda p: AQ_GRADE_MAP.get(p.aq_grade),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CowayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Coway sensor entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        CowaySensor(coordinator, device_id, description)
        for device_id in coordinator.data.purifiers
        for description in SENSOR_DESCRIPTIONS
    )


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
