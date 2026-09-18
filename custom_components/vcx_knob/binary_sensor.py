"""Binary sensor entities for VCX-Knob."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VCXKnobCoordinator


BINARY_SENSORS = (
    BinarySensorEntityDescription(
        key="connection",
        translation_key="connection",
        device_class="connectivity",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


class VCXKnobBinarySensor(BinarySensorEntity):
    def __init__(
        self,
        coordinator: VCXKnobCoordinator,
        description: BinarySensorEntityDescription,
    ) -> None:
        self._coordinator = coordinator
        self.entity_description = description
        self._attr_has_entity_name = True
        self._attr_unique_id = (
            f"{coordinator.device_address}_{description.key}"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.device_address)},
            "name": coordinator.device_name,
            "manufacturer": "VCX",
            "model": "VCX-Knob Smart Toilet",
        }
        self._attr_should_poll = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            self._coordinator.async_add_listener(
                self._handle_coordinator_update
            )
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        data = self._coordinator.data or {}
        return bool(data.get("connected", False))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VCXKnobCoordinator = hass.data[DOMAIN][entry.entry_id]
    registry = er.async_get(hass)
    paired_entity_id = registry.async_get_entity_id(
        "binary_sensor", DOMAIN, f"{coordinator.device_address}_paired"
    )
    if paired_entity_id is not None:
        registry.async_remove(paired_entity_id)

    async_add_entities(
        VCXKnobBinarySensor(coordinator, item)
        for item in BINARY_SENSORS
    )