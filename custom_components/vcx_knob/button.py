"""Button entities for VCX-Knob."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import Command, DOMAIN
from .coordinator import VCXKnobCoordinator


@dataclass(frozen=True)
class VCXKnobButtonDescription:
    key: str
    icon: str
    command: str
    data_byte: int = 0
    entity_category: EntityCategory | str | None = None


BUTTON_DESCRIPTIONS = (
    VCXKnobButtonDescription("big_flush", "mdi:toilet", Command.DACHONG),
    VCXKnobButtonDescription("small_flush", "mdi:toilet", Command.XIAOCHONG),
    VCXKnobButtonDescription("feminine_wash", "mdi:human-female", Command.FUXI),
    VCXKnobButtonDescription("rear_wash", "mdi:human-male", Command.TUNXI),
    VCXKnobButtonDescription("massage", "mdi:vibrate", Command.ANMO),
    VCXKnobButtonDescription("bubble", "mdi:buffer", Command.PAOMO),
    VCXKnobButtonDescription("stop", "mdi:stop", Command.STOP),
    VCXKnobButtonDescription("dry", "mdi:tumble-dryer", Command.HONGGAN),
    VCXKnobButtonDescription("open_lid", "mdi:arrow-up-bold-box", Command.FANGAI),
    VCXKnobButtonDescription("open_seat", "mdi:chair-rolling", Command.FANQUAN),
    VCXKnobButtonDescription("close", "mdi:arrow-down-bold-box", Command.JIENENG),
    VCXKnobButtonDescription("runbi", "mdi:water-pump", Command.RUNBI),
    VCXKnobButtonDescription("self_clean", "mdi:sparkles", Command.ZIJIE),
    VCXKnobButtonDescription(
        "factory_reset", "mdi:restore-alert", Command.HUIFUCHUCHANG,
        entity_category=EntityCategory.CONFIG,
    ),
)


class VCXKnobButton(ButtonEntity):
    """A one-shot toilet action."""

    def __init__(self, coordinator: VCXKnobCoordinator, description: VCXKnobButtonDescription) -> None:
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
        if description.key == "factory_reset":
            # Destructive action: user must explicitly enable it in the entity registry.
            self._attr_entity_registry_enabled_default = False

    @property
    def available(self) -> bool:
        return self._coordinator.client.is_connected

    async def async_press(self, **kwargs) -> None:
        await self._coordinator.async_send_command(
            self._description.command,
            self._description.data_byte,
            0,
            0,
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VCXKnobCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(VCXKnobButton(coordinator, item) for item in BUTTON_DESCRIPTIONS)
