"""Optimistic select entities based on DM Toilet Control 1.0.6."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, SELECTS, SelectEntityDescription
from .coordinator import VCXKnobCoordinator

_LOGGER = logging.getLogger(__name__)


class VCXKnobSelect(SelectEntity, RestoreEntity):
    """A locally tracked setting.

    DM Toilet Control 1.0.6 does not read these values from the toilet. We mirror
    that behavior: state becomes known after a successful command, while an
    incoming FFA2 packet may override it on firmware variants that report state.
    """

    def __init__(
        self,
        coordinator: VCXKnobCoordinator,
        description: SelectEntityDescription,
    ) -> None:
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
        self._attr_assumed_state = True

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            self._coordinator.async_add_listener(self._handle_coordinator_update)
        )
        self._handle_coordinator_update()

        if self._attr_current_option is None:
            last_state = await self.async_get_last_state()
            if last_state is not None and last_state.state in self.options:
                self._attr_current_option = last_state.state
                if self._description.state_key:
                    code = self._description.options_map[last_state.state]
                    self._coordinator.restore_app_value(
                        self._description.state_key, code
                    )
                self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self._coordinator.data
        if data is not None and self._description.state_key:
            state_code = data.get(self._description.state_key)
            if state_code is not None:
                reverse_map = {
                    code: option
                    for option, code in self._description.options_map.items()
                }
                self._attr_current_option = reverse_map.get(int(state_code))
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        return self._coordinator.client.is_connected

    async def async_select_option(self, option: str) -> None:
        code = self._description.options_map.get(option)
        if code is None:
            _LOGGER.error(
                "Invalid option for %s: %s",
                self._description.key,
                option,
            )
            return

        if not self._description.state_key:
            raise ValueError(
                f"Select {self._description.key} has no state_key"
            )

        if self._description.payload_kind == "temperature":
            await self._coordinator.async_set_app_temperature(
                self._description.state_key,
                self._description.command,
                code,
            )
            return

        if self._description.payload_kind == "level":
            await self._coordinator.async_set_app_level(
                self._description.state_key,
                self._description.command,
                code,
            )
            return

        raise ValueError(
            f"Unknown payload kind {self._description.payload_kind!r}"
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VCXKnobCoordinator = hass.data[DOMAIN][entry.entry_id]
    registry = er.async_get(hass)
    for retired_key in (
        "water_level",
        "air_level",
        "light_brightness",
        "radar_sensitivity",
    ):
        entity_id = registry.async_get_entity_id(
            "select", DOMAIN, f"{coordinator.device_address}_{retired_key}"
        )
        if entity_id is not None:
            registry.async_remove(entity_id)

    async_add_entities(
        VCXKnobSelect(coordinator, item) for item in SELECTS
    )