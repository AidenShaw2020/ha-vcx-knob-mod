"""Optimistic ambient RGB light from DM Toilet Control 1.0.6."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .coordinator import VCXKnobCoordinator

EFFECT_TO_MODE = {
    "Static": 1,
    "Flash": 2,
    "Breathing": 3,
    "Flow": 4,
    "Rainbow Flow": 5,
    "Rainbow Gradient": 6,
    "Welcome": 7,
}


class VCXKnobAmbientLight(LightEntity, RestoreEntity):
    """Ambient RGB controller using the app's AA 08 03 frame."""

    _attr_has_entity_name = True
    _attr_translation_key = "ambient_light"
    _attr_icon = "mdi:led-strip-variant"
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = list(EFFECT_TO_MODE)
    _attr_assumed_state = True

    def __init__(self, coordinator: VCXKnobCoordinator) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.device_address}_ambient_light"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.device_address)},
            "name": coordinator.device_name,
            "manufacturer": "VCX",
            "model": "VCX-Knob Smart Toilet",
        }
        self._attr_should_poll = False
        self._attr_is_on = False
        self._attr_brightness = 56  # app default lightness is 22%
        self._attr_rgb_color = (255, 0, 0)
        self._attr_effect = "Static"

    @property
    def available(self) -> bool:
        return self._coordinator.client.is_connected

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is None:
            return

        self._attr_is_on = last_state.state == STATE_ON
        if (brightness := last_state.attributes.get(ATTR_BRIGHTNESS)) is not None:
            self._attr_brightness = int(brightness)
        if (rgb := last_state.attributes.get(ATTR_RGB_COLOR)) is not None:
            self._attr_rgb_color = tuple(int(value) for value in rgb)
        if (effect := last_state.attributes.get(ATTR_EFFECT)) in EFFECT_TO_MODE:
            self._attr_effect = effect

    def _scaled_rgb(self) -> tuple[int, int, int]:
        rgb = self._attr_rgb_color or (255, 0, 0)
        brightness = self._attr_brightness if self._attr_brightness is not None else 255
        return tuple(
            max(0, min(255, round(channel * brightness / 255)))
            for channel in rgb
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        if (rgb := kwargs.get(ATTR_RGB_COLOR)) is not None:
            self._attr_rgb_color = tuple(int(value) for value in rgb)
        if (brightness := kwargs.get(ATTR_BRIGHTNESS)) is not None:
            self._attr_brightness = max(1, min(255, int(brightness)))
        if (effect := kwargs.get(ATTR_EFFECT)) is not None:
            if effect not in EFFECT_TO_MODE:
                raise ValueError(f"Unsupported ambient effect: {effect}")
            self._attr_effect = effect

        mode = EFFECT_TO_MODE[self._attr_effect or "Static"]
        red, green, blue = self._scaled_rgb()
        await self._coordinator.async_send_ambient_light(
            mode | 0x80, red, green, blue
        )
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        red, green, blue = self._scaled_rgb()
        # DM Toilet Control adds bit 7 while manual light control is enabled.
        await self._coordinator.async_send_ambient_light(
            0x80, red, green, blue
        )
        self._attr_is_on = False
        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VCXKnobCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VCXKnobAmbientLight(coordinator)])