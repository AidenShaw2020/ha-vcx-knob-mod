"""Administrator-only Bluetooth helper services for VCX-Knob."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.service import async_register_admin_service

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_PAIR_BLUETOOTH_DEVICE = "pair_bluetooth_device"
SERVICE_SCAN_BLUETOOTH = "scan_bluetooth_device"
SERVICE_GET_DEVICE_INFO = "get_bluetooth_device_info"

_MAC = vol.Match(r"^(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
_TIMEOUT = vol.All(vol.Coerce(int), vol.Range(min=5, max=60))

SERVICE_SCHEMA_PAIR = vol.Schema({
    vol.Required("device_address"): _MAC,
    vol.Optional("timeout", default=15): _TIMEOUT,
})
SERVICE_SCHEMA_SCAN = vol.Schema({
    vol.Optional("timeout", default=10): _TIMEOUT,
    vol.Optional("device_filter", default="VCX"): vol.All(str, vol.Length(min=1, max=64)),
})
SERVICE_SCHEMA_INFO = vol.Schema({vol.Required("device_address"): _MAC})


async def _run_bluetoothctl(*args: str, timeout: int = 15) -> str:
    """Run bluetoothctl without invoking a shell."""
    process = await asyncio.create_subprocess_exec(
        "bluetoothctl",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()
        raise
    return stdout.decode(errors="replace") + stderr.decode(errors="replace")


async def _pair_service_handler(hass: HomeAssistant, call: ServiceCall) -> None:
    """Pair and trust a Bluetooth device. Registration enforces admin access."""
    address = call.data["device_address"]
    timeout = call.data["timeout"]
    _LOGGER.info("Pairing Bluetooth device %s", address)

    try:
        result = await _run_bluetoothctl("pair", address, timeout=timeout)
    except asyncio.TimeoutError:
        _LOGGER.error("Bluetooth pairing timed out for %s", address)
        return
    except FileNotFoundError:
        _LOGGER.error("bluetoothctl is not available on this Home Assistant host")
        return

    if "Pairing successful" in result or "Already paired" in result:
        try:
            await _run_bluetoothctl("trust", address, timeout=10)
        except (asyncio.TimeoutError, FileNotFoundError) as err:
            _LOGGER.warning("Device %s paired, but trust operation failed: %s", address, err)
        return

    _LOGGER.warning("Bluetooth pairing failed for %s: %s", address, result.strip())


async def _scan_service_handler(hass: HomeAssistant, call: ServiceCall) -> None:
    """Scan for matching connectable BLE devices. Registration enforces admin access."""
    from homeassistant.components.bluetooth import (
        BluetoothCallbackMatcher,
        BluetoothScanningMode,
        BluetoothServiceInfo,
        async_register_callback,
    )

    timeout = call.data["timeout"]
    device_filter = call.data["device_filter"]
    discovered: dict[str, str] = {}

    def _callback(service_info: BluetoothServiceInfo, _change: Any) -> None:
        if service_info.name and device_filter.casefold() in service_info.name.casefold():
            discovered[service_info.address] = service_info.name

    remove_callback = async_register_callback(
        hass,
        _callback,
        BluetoothCallbackMatcher(connectable=True),
        BluetoothScanningMode.ACTIVE,
    )
    try:
        await asyncio.sleep(timeout)
    finally:
        remove_callback()

    _LOGGER.info("Bluetooth scan found %d matching device(s): %s", len(discovered), discovered)


async def _info_service_handler(hass: HomeAssistant, call: ServiceCall) -> None:
    """Log pairing/trust/connection state. Registration enforces admin access."""
    address = call.data["device_address"]
    try:
        result = await _run_bluetoothctl("info", address, timeout=10)
    except (asyncio.TimeoutError, FileNotFoundError) as err:
        _LOGGER.error("Unable to query Bluetooth device %s: %s", address, err)
        return

    paired = "Paired: yes" in result
    trusted = "Trusted: yes" in result
    connected = "Connected: yes" in result
    _LOGGER.info(
        "Bluetooth device %s - paired=%s trusted=%s connected=%s",
        address,
        paired,
        trusted,
        connected,
    )


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register security-sensitive helper services as administrator-only."""
    if hass.services.has_service(DOMAIN, SERVICE_PAIR_BLUETOOTH_DEVICE):
        return

    async def _pair(call: ServiceCall) -> None:
        await _pair_service_handler(hass, call)

    async def _scan(call: ServiceCall) -> None:
        await _scan_service_handler(hass, call)

    async def _info(call: ServiceCall) -> None:
        await _info_service_handler(hass, call)

    async_register_admin_service(
        hass, DOMAIN, SERVICE_PAIR_BLUETOOTH_DEVICE, _pair, schema=SERVICE_SCHEMA_PAIR
    )
    async_register_admin_service(
        hass, DOMAIN, SERVICE_SCAN_BLUETOOTH, _scan, schema=SERVICE_SCHEMA_SCAN
    )
    async_register_admin_service(
        hass, DOMAIN, SERVICE_GET_DEVICE_INFO, _info, schema=SERVICE_SCHEMA_INFO
    )
