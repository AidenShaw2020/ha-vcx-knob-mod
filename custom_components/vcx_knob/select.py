"""Select entities for VCX-Knob."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SELECTS
from .coordinator import VCXKnobCoordinator

_LOGGER = logging.getLogger(__name__)


class VCXKnobSelect(SelectEntity):
    def __init__(self, coordinator: VCXKnobCoordinator, description) -> None:
        self._coordinator = coordinator
        self._description = description
        self._attr_has_entity_name = True
        self._attr_translation_key = description.key
        self._attr_icon = description.icon
        self._attr_unique_id = f"{coordinator.device_address}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.device_address)},
            "name": coordinator.device_name,
            "manufacturer": "VCX",
            "model": "VCX-Knob Smart Toilet",
        }
        self._attr_should_poll = False
        self._attr_options = description.options
        self._attr_current_option = None
        self._attr_entity_category = description.entity_category

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self._coordinator.async_add_listener(self._handle_coordinator_update))
        self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self._coordinator.data
        if data is not None and self._description.state_key:
            state_code = data.get(self._description.state_key)
            if state_code is not None:
                self._attr_current_option = self._code_to_option(state_code)
        self.async_write_ha_state()

    def _code_to_option(self, code: int) -> str | None:
        if self._description.key in ("water_temperature", "seat_temperature"):
            return {0: "off", 1: "34", 2: "37", 3: "40"}.get(code)
        if self._description.key == "wind_temperature":
            return {0: "off", 1: "40", 2: "45", 3: "50"}.get(code)
        if self._description.key == "radar_sensitivity":
            return {1: "low", 2: "medium", 3: "high"}.get(code)
        return {0: "off", 1: "low", 2: "medium", 3: "high"}.get(code)

    @property
    def available(self) -> bool:
        return self._coordinator.client.is_connected

    async def async_select_option(self, option: str) -> None:
        data_byte = self._description.options_map.get(option)
        if data_byte is None:
            _LOGGER.error("Invalid option for %s: %s", self._description.key, option)
            return
        await self._coordinator.async_send_command(self._description.command, data_byte, 0, 0)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: VCXKnobCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(VCXKnobSelect(coordinator, item) for item in SELECTS)
