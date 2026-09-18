"""Switch entities for VCX-Knob."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import Command, DOMAIN
from .coordinator import VCXKnobCoordinator


@dataclass(frozen=True)
class VCXKnobSwitchDescription:
    key: str
    icon: str
    command: str | None = None
    state_key: str | None = None
    entity_category: EntityCategory | str | None = None


SWITCH_DESCRIPTIONS = (
    VCXKnobSwitchDescription("radar", "mdi:radar", state_key="radar_enabled", entity_category=EntityCategory.CONFIG),
    VCXKnobSwitchDescription("voice", "mdi:microphone", Command.YUYIN, "voice_enabled", EntityCategory.CONFIG),
    VCXKnobSwitchDescription("sensor", "mdi:sensor", state_key="sensors_enabled", entity_category=EntityCategory.CONFIG),
    VCXKnobSwitchDescription("auto_mode", "mdi:autorenew", Command.ZIDONG, "auto_enabled", EntityCategory.CONFIG),
    VCXKnobSwitchDescription("night_light", "mdi:lightbulb-night", Command.GUANGDENG, "lights_enabled", EntityCategory.CONFIG),
    VCXKnobSwitchDescription("foot_sensor", "mdi:eye", state_key="foot_sensor_enabled", entity_category=EntityCategory.CONFIG),
    VCXKnobSwitchDescription("sterilization", "mdi:spray-bottle", state_key="sterilization_enabled", entity_category=EntityCategory.CONFIG),
)


class VCXKnobSwitch(SwitchEntity):
    def __init__(self, coordinator: VCXKnobCoordinator, description: VCXKnobSwitchDescription) -> None:
        self._coordinator = coordinator
        self._description = description
        self._attr_has_entity_name = True
        self._attr_translation_key = description.key
        self._attr_icon = description.icon
        self._attr_entity_category = description.entity_category
        self._attr_unique_id = f"{coordinator.device_address}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.device_address)},
            "name": coordinator.device_name,
            "manufacturer": "VCX",
            "model": "VCX-Knob Smart Toilet",
        }
        self._attr_should_poll = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self._coordinator.async_add_listener(self._handle_coordinator_update))

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        return self._coordinator.client.is_connected

    @property
    def is_on(self) -> bool | None:
        data = self._coordinator.data
        if data is None or self._description.state_key is None:
            return None
        return bool(data.get(self._description.state_key, False))

    async def async_turn_on(self, **kwargs) -> None:
        if self._description.command:
            await self._coordinator.async_send_command(self._description.command, 1, 0, 0)

    async def async_turn_off(self, **kwargs) -> None:
        if self._description.command:
            await self._coordinator.async_send_command(self._description.command, 0, 0, 0)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: VCXKnobCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(VCXKnobSwitch(coordinator, item) for item in SWITCH_DESCRIPTIONS)
