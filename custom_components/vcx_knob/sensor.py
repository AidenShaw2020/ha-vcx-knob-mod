"""Sensor entities for VCX-Knob."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VCXKnobCoordinator


SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(key="device_address", translation_key="device_address", entity_category=EntityCategory.DIAGNOSTIC, icon="mdi:bluetooth"),
    SensorEntityDescription(key="rssi", translation_key="rssi", native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT, device_class="signal_strength", state_class="measurement", entity_category=EntityCategory.DIAGNOSTIC),
    SensorEntityDescription(key="air_percentage", translation_key="air_percentage", native_unit_of_measurement=PERCENTAGE, state_class="measurement", icon="mdi:air-filter"),
    SensorEntityDescription(key="water_percentage", translation_key="water_percentage", native_unit_of_measurement=PERCENTAGE, state_class="measurement", icon="mdi:water-percent"),
    SensorEntityDescription(key="radar_level", translation_key="radar_level", state_class="measurement", icon="mdi:radar", entity_category=EntityCategory.DIAGNOSTIC),
    SensorEntityDescription(key="cover_close_time", translation_key="cover_close_time", native_unit_of_measurement=UnitOfTime.SECONDS, state_class="measurement", icon="mdi:clock-outline"),
    SensorEntityDescription(key="cover_flip_intensity", translation_key="cover_flip_intensity", state_class="measurement", icon="mdi:arrow-up-down"),
    SensorEntityDescription(key="ring_flip_intensity", translation_key="ring_flip_intensity", state_class="measurement", icon="mdi:arrow-up-down"),
    SensorEntityDescription(key="cover_close_intensity", translation_key="cover_close_intensity", state_class="measurement", icon="mdi:arrow-collapse"),
    SensorEntityDescription(key="ring_close_intensity", translation_key="ring_close_intensity", state_class="measurement", icon="mdi:arrow-collapse"),
    SensorEntityDescription(key="bubble_level", translation_key="bubble_level", state_class="measurement", icon="mdi:buffer"),
    SensorEntityDescription(key="big_flush_water", translation_key="big_flush_water", native_unit_of_measurement=UnitOfTime.SECONDS, state_class="measurement", icon="mdi:timer-outline", entity_category=EntityCategory.DIAGNOSTIC),
    SensorEntityDescription(key="small_flush_water", translation_key="small_flush_water", native_unit_of_measurement=UnitOfTime.SECONDS, state_class="measurement", icon="mdi:timer-outline", entity_category=EntityCategory.DIAGNOSTIC),
    SensorEntityDescription(key="small_flush_up", translation_key="small_flush_up", native_unit_of_measurement=UnitOfTime.SECONDS, state_class="measurement", icon="mdi:timer-outline", entity_category=EntityCategory.DIAGNOSTIC),
    SensorEntityDescription(key="foot_sensor_distance", translation_key="foot_sensor_distance", native_unit_of_measurement="cm", state_class="measurement", icon="mdi:ruler", entity_category=EntityCategory.DIAGNOSTIC),
    SensorEntityDescription(key="sterilization_time", translation_key="sterilization_time", native_unit_of_measurement=UnitOfTime.MINUTES, state_class="measurement", icon="mdi:clock-outline", entity_category=EntityCategory.DIAGNOSTIC),
    SensorEntityDescription(key="water_pressure", translation_key="water_pressure", state_class="measurement", icon="mdi:water-pump", entity_category=EntityCategory.DIAGNOSTIC),
    SensorEntityDescription(key="ambient_light_brightness", translation_key="ambient_light_brightness", native_unit_of_measurement=PERCENTAGE, state_class="measurement", icon="mdi:lightbulb"),
)


class VCXKnobSensor(SensorEntity):
    def __init__(self, coordinator: VCXKnobCoordinator, description: SensorEntityDescription) -> None:
        self._coordinator = coordinator
        self.entity_description = description
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.device_address}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.device_address)},
            "name": coordinator.device_name,
            "manufacturer": "VCX",
            "model": "VCX-Knob Smart Toilet",
        }
        self._attr_should_poll = False
        if description.key not in {"device_address", "rssi"}:
            self._attr_entity_registry_enabled_default = False
    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self._coordinator.async_add_listener(self._handle_coordinator_update))

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        if self.entity_description.key == "device_address":
            return True
        data = self._coordinator.data
        return bool(data and self._coordinator.last_update_success and data.get("connected", False))

    @property
    def native_value(self):
        data = self._coordinator.data
        if self.entity_description.key == "device_address":
            return self._coordinator.device_address
        return None if data is None else data.get(self.entity_description.key)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: VCXKnobCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(VCXKnobSensor(coordinator, item) for item in SENSORS)
