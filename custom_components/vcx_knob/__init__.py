"""VCX-Knob Smart Toilet integration (hardened fork)."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_NAME, Platform
from homeassistant.core import HomeAssistant

from .bluetooth_pairing import async_setup_services
from .const import CONF_DEVICE_ADDRESS, CONF_DEVICE_NAME, DOMAIN
from .coordinator import VCXKnobBLEClient, VCXKnobCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: Final = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.SELECT,
    Platform.BINARY_SENSOR,
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up integration-level services once during Home Assistant startup."""
    hass.data.setdefault(DOMAIN, {})
    await async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured VCX-Knob device."""
    device_address = entry.data.get(CONF_DEVICE_ADDRESS) or entry.data.get(CONF_ADDRESS)
    device_name = entry.data.get(CONF_DEVICE_NAME) or entry.data.get(CONF_NAME, "VCX-Knob")

    if not device_address:
        _LOGGER.error("Configuration entry does not contain a Bluetooth device address")
        return False

    coordinator: VCXKnobCoordinator | None = None

    def _notification_callback(data: bytes) -> None:
        """Forward one complete FFA2 packet to the coordinator."""
        if coordinator is not None:
            coordinator.handle_status_packet(data)
    client = VCXKnobBLEClient(
        hass=hass,
        address=device_address,
        name=device_name,
        notification_callback=_notification_callback,
    )
    coordinator = VCXKnobCoordinator(
        hass=hass,
        config_entry=entry,
        client=client,
        poll_interval=30,
    )

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Populate initial device state before entities are forwarded.
    await coordinator.async_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    _LOGGER.info("VCX-Knob integration set up for %s", device_name)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a configured VCX-Knob device."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: VCXKnobCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_disconnect()
    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry after its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Keep compatibility with upstream v1 config entries."""
    _LOGGER.debug("Migrating config entry from version %s.%s", entry.version, entry.minor_version)
    return True
