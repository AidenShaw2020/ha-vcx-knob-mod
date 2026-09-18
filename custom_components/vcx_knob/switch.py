"""Switch platform kept for upgrade compatibility.

DM Toilet Control 1.0.6 exposes the corresponding functions as one-shot
commands and does not read switch state back from the toilet. They are therefore
represented as buttons in button.py instead of speculative switches.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VCXKnobCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VCXKnobCoordinator = hass.data[DOMAIN][entry.entry_id]
    registry = er.async_get(hass)
    for retired_key in (
        "radar",
        "voice",
        "sensor",
        "auto_mode",
        "night_light",
        "foot_sensor",
        "sterilization",
    ):
        entity_id = registry.async_get_entity_id(
            "switch", DOMAIN, f"{coordinator.device_address}_{retired_key}"
        )
        if entity_id is not None:
            registry.async_remove(entity_id)

    async_add_entities([])