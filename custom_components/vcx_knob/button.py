"""Button entities for app-verified VCX-Knob commands."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import Command, DOMAIN
from .coordinator import VCXKnobCoordinator


@dataclass(frozen=True)
class VCXKnobButtonDescription:
    key: str
    icon: str
    command: str


BUTTON_DESCRIPTIONS = (
    VCXKnobButtonDescription("power", "mdi:power", Command.POWER),
    VCXKnobButtonDescription("light", "mdi:lightbulb", Command.LIGHT),
    VCXKnobButtonDescription("eco", "mdi:leaf", Command.ECO),
    VCXKnobButtonDescription("bubble", "mdi:buffer", Command.FOAM),
    VCXKnobButtonDescription("feminine_wash", "mdi:human-female", Command.FEMININE_WASH),
    VCXKnobButtonDescription("rear_wash", "mdi:human-male", Command.REAR_WASH),
    VCXKnobButtonDescription("child_wash", "mdi:human-child", Command.CHILD_WASH),
    VCXKnobButtonDescription("dry", "mdi:tumble-dryer", Command.DRY),
    VCXKnobButtonDescription("big_flush", "mdi:toilet", Command.FLUSH),
    VCXKnobButtonDescription("massage", "mdi:vibrate", Command.MASSAGE),
    VCXKnobButtonDescription("open_lid", "mdi:arrow-up-bold-box", Command.LID_TOGGLE),
    VCXKnobButtonDescription("open_seat", "mdi:chair-rolling", Command.SEAT_TOGGLE),
    VCXKnobButtonDescription("auto_mode", "mdi:autorenew", Command.AUTO),
    VCXKnobButtonDescription("self_clean", "mdi:sparkles", Command.SELF_CLEAN),
    VCXKnobButtonDescription("stop", "mdi:stop", Command.STOP),
)


class VCXKnobButton(ButtonEntity):
    """A one-shot command exposed by DM Toilet Control."""

    def __init__(
        self,
        coordinator: VCXKnobCoordinator,
        description: VCXKnobButtonDescription,
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

    @property
    def available(self) -> bool:
        return self._coordinator.client.is_connected

    async def async_press(self, **kwargs) -> None:
        await self._coordinator.async_send_app_action(self._description.command)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VCXKnobCoordinator = hass.data[DOMAIN][entry.entry_id]
    registry = er.async_get(hass)
    for retired_key in ("small_flush", "close", "runbi", "factory_reset"):
        entity_id = registry.async_get_entity_id(
            "button", DOMAIN, f"{coordinator.device_address}_{retired_key}"
        )
        if entity_id is not None:
            registry.async_remove(entity_id)

    async_add_entities(
        VCXKnobButton(coordinator, item) for item in BUTTON_DESCRIPTIONS
    )