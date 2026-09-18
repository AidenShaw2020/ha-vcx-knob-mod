"""VCX-Knob 设备的 BLE 协调器

此模块提供协调器，用于管理通过蓝牙低功耗与 VCX-Knob 智能马桶设备的通信。

协调器扩展了 DataUpdateCoordinator 以提供自动状态轮询和
Home Assistant 实体的状态管理。

该协调器的数据包含来自所有状态包的合并状态:
{
    "connected": bool,
    "paired": bool,
    "rssi": int | None,
    "device_address": str,
    # Type 01: 基础状态
    "flush_enabled": bool,
    "seat_enabled": bool,
    "bubble_enabled": bool,
    "air_enabled": bool,
    "radar_enabled": bool,
    "voice_enabled": bool,
    "sensors_enabled": bool,
    "lights_enabled": bool,
    # Type 02: 温度（根据参考实现更新）
    "water_level": int,
    "water_temp_value": int,
    "wind_level": int,
    "wind_temp_value": int,
    "seat_level": int,
    "seat_temp_value": int,
    "water_pressure": int,
    "ambient_light_brightness": int,
    # Type 03: 百分比
    "air_percentage": int,
    "water_percentage": int,
    "radar_level": int,
    "cover_close_time": int,
    # Type 04: 强度（根据参考实现更新）
    "cover_flip_intensity": int,
    "ring_flip_intensity": int,
    "cover_close_intensity": int,
    "ring_close_intensity": int,
    # Type 05: 冲水参数（根据参考实现更新）
    "bubble_level": int,
    "big_flush_down": int,
    "big_flush_water": int,
    "small_flush_up": int,
    "small_flush_water": int,
    "small_flush_down": int,
    # Type 06: 传感器（根据参考实现更新）
    "foot_sensor_enabled": int,
    "foot_sensor_distance": int,
    "sterilization_time": int,
}
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import timedelta
from typing import Final

import voluptuous as vol
from bleak import BleakClient, BleakError
from bleak.exc import BleakDBusError
from bleak_retry_connector import establish_connection
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BluetoothServiceInfo,
    async_get_scanner,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    BLE_NOTIFY_CHARACTERISTIC_UUID,
    BLE_SERVICE_UUID,
    BLE_WRITE_CHARACTERISTIC_UUID,
    BLE_DEVICE_NAME_FILTER,
    CONF_AUTO_CONNECT,
    CONF_DEVICE_ADDRESS,
    CONF_DEVICE_NAME,
    DEFAULT_AUTO_CONNECT,
    DEFAULT_CONNECTION_TIMEOUT,
    DEFAULT_SCAN_TIMEOUT,
    DEFAULT_STATUS_POLL_INTERVAL,
    DOMAIN,
)
from .protocol import build_command, decode_status_packet, parse_status_packet

_LOGGER = logging.getLogger(__name__)


# ============================================================================
# 常量
# ============================================================================

# 重试配置
CONNECT_RETRY_COUNT: Final = 3
CONNECT_RETRY_DELAY: Final = 5  # 秒
DISCONNECT_COOLDOWN: Final = 10  # 秒

# 状态轮询
MIN_POLL_INTERVAL: Final = 10  # 秒
MAX_POLL_INTERVAL: Final = 300  # 秒

# 连接超时
CONNECTION_TIMEOUT: Final = DEFAULT_CONNECTION_TIMEOUT


# ============================================================================
# 异常
# ============================================================================

class VCXKnobConnectionError(Exception):
    """当设备连接失败时抛出"""

    def __init__(self, message: str, retryable: bool = True) -> None:
        """初始化异常

        Args:
            message: 错误消息
            retryable: 错误是否可重试
        """
        super().__init__(message)
        self.retryable = retryable


class VCXKnobNotFoundError(VCXKnobConnectionError):
    """扫描期间找不到设备时抛出"""

    def __init__(self, address: str) -> None:
        """初始化异常

        Args:
            address: 未找到的设备地址
        """
        super().__init__(f"设备 {address} 未找到", retryable=True)


# ============================================================================
# BLE 客户端管理器
# ============================================================================

class VCXKnobBLEClient:
    """Manage the VCX-Knob BLE connection through Home Assistant Bluetooth."""

    def __init__(
        self,
        hass: HomeAssistant,
        address: str,
        name: str,
        notification_callback: Callable[[bytes], None],
    ) -> None:
        """Initialize the BLE client."""
        self._hass = hass
        self._address = address
        self._name = name
        self._notification_callback = notification_callback
        self._client: BleakClient | None = None
        self._status_buffer: list[str] = []
        self._rx_buffer = bytearray()
        self._is_connected = False
        self._disconnect_time: float | None = None
        self._lock = asyncio.Lock()

    def _disconnected_callback(self, _client: BleakClient) -> None:
        """Handle a BLE disconnect."""
        _LOGGER.warning("Device %s disconnected", self._address)
        self._is_connected = False

    @property
    def address(self) -> str:
        """Return the BLE address."""
        return self._address

    @property
    def name(self) -> str:
        """Return the device name."""
        return self._name

    @property
    def is_connected(self) -> bool:
        """Return whether the BLE client is connected."""
        return (
            self._is_connected
            and self._client is not None
            and self._client.is_connected
        )

    @property
    def rssi(self) -> int | None:
        """Return the latest RSSI seen by Home Assistant."""
        try:
            service_info = bluetooth.async_last_service_info(
                self._hass,
                self._address,
                True,
            )
            return service_info.rssi if service_info else None
        except Exception:
            return None

    def _log_gatt_profile(self) -> None:
        """Log all discovered GATT services and characteristics."""
        if self._client is None:
            return

        services = self._client.services
        _LOGGER.warning(
            "GATT profile for %s (%s):",
            self._name,
            self._address,
        )
        for service in services.services.values():
            _LOGGER.warning(
                "GATT service uuid=%s handle=%s",
                service.uuid,
                service.handle,
            )
            for char in service.characteristics:
                _LOGGER.warning(
                    "  characteristic uuid=%s handle=%s properties=%s",
                    char.uuid,
                    char.handle,
                    ",".join(char.properties),
                )

    async def connect(self) -> None:
        """Connect using Home Assistant's BLE device and bleak-retry-connector."""
        async with self._lock:
            if self.is_connected:
                _LOGGER.debug("Already connected to %s", self._address)
                return

            if self._disconnect_time:
                cooldown_remaining = DISCONNECT_COOLDOWN - (
                    asyncio.get_event_loop().time() - self._disconnect_time
                )
                if cooldown_remaining > 0:
                    await asyncio.sleep(cooldown_remaining)

            ble_device = bluetooth.async_ble_device_from_address(
                self._hass,
                self._address,
                connectable=True,
            )
            if ble_device is None:
                raise VCXKnobNotFoundError(self._address)

            _LOGGER.info(
                "Connecting to %s (%s) through Home Assistant Bluetooth",
                self._name,
                self._address,
            )

            try:
                async with asyncio.timeout(CONNECTION_TIMEOUT):
                    self._client = await establish_connection(
                        BleakClient,
                        ble_device,
                        self._name or self._address,
                        disconnected_callback=self._disconnected_callback,
                    )

                services = self._client.services
                service = services.get_service(BLE_SERVICE_UUID)
                write_char = services.get_characteristic(
                    BLE_WRITE_CHARACTERISTIC_UUID
                )
                notify_char = services.get_characteristic(
                    BLE_NOTIFY_CHARACTERISTIC_UUID
                )

                if service is None or write_char is None or notify_char is None:
                    self._log_gatt_profile()
                    missing: list[str] = []
                    if service is None:
                        missing.append(f"service {BLE_SERVICE_UUID}")
                    if write_char is None:
                        missing.append(f"write characteristic {BLE_WRITE_CHARACTERISTIC_UUID}")
                    if notify_char is None:
                        missing.append(f"notify characteristic {BLE_NOTIFY_CHARACTERISTIC_UUID}")
                    try:
                        await self._client.disconnect()
                    finally:
                        self._client = None
                    raise VCXKnobConnectionError(
                        "Expected VCX-Knob GATT profile is missing: "
                        + ", ".join(missing),
                        retryable=False,
                    )

                _LOGGER.info(
                    "VCX-Knob GATT profile verified: service=%s write=%s notify=%s",
                    service.uuid,
                    write_char.uuid,
                    notify_char.uuid,
                )
                _LOGGER.debug(
                    "Write properties=%s; notify properties=%s",
                    write_char.properties,
                    notify_char.properties,
                )

                await self._client.start_notify(
                    notify_char,
                    self._notification_handler,
                )

                self._is_connected = True
                self._disconnect_time = None
                self._status_buffer.clear()
                self._rx_buffer.clear()
                _LOGGER.info("Connected to %s (%s)", self._name, self._address)

            except asyncio.TimeoutError as err:
                raise VCXKnobConnectionError(
                    f"Connection to {self._address} timed out",
                    retryable=True,
                ) from err
            except BleakDBusError as err:
                raise VCXKnobConnectionError(
                    f"DBus error while connecting to {self._address}: {err}",
                    retryable=True,
                ) from err
            except VCXKnobConnectionError:
                raise
            except BleakError as err:
                raise VCXKnobConnectionError(
                    f"Unable to connect to {self._address}: {err}",
                    retryable=True,
                ) from err

    async def disconnect(self) -> None:
        """Disconnect from the BLE device."""
        async with self._lock:
            client = self._client
            if client is None:
                self._is_connected = False
                return

            try:
                if client.is_connected:
                    try:
                        notify_char = client.services.get_characteristic(
                            BLE_NOTIFY_CHARACTERISTIC_UUID
                        )
                        if notify_char is not None:
                            await client.stop_notify(notify_char)
                    except Exception:
                        pass
                    await client.disconnect()
            except Exception as err:
                _LOGGER.warning("Error while disconnecting: %s", err)
            finally:
                self._client = None
                self._is_connected = False
                self._disconnect_time = asyncio.get_event_loop().time()

    async def send_command(
        self,
        cmd: str,
        d1: int = 0,
        d2: int = 0,
        d3: int = 0,
    ) -> None:
        """Send one VCX-Knob command."""
        if not self.is_connected or self._client is None:
            raise VCXKnobConnectionError(
                "Not connected to device",
                retryable=True,
            )

        command = build_command(cmd, d1, d2, d3)
        _LOGGER.debug("Sending command: %s", command.hex().upper())

        try:
            write_char = self._client.services.get_characteristic(
                BLE_WRITE_CHARACTERISTIC_UUID
            )
            if write_char is None:
                self._log_gatt_profile()
                raise VCXKnobConnectionError(
                    f"Write characteristic {BLE_WRITE_CHARACTERISTIC_UUID} not found",
                    retryable=False,
                )

            properties = set(write_char.properties)
            if "write" in properties:
                use_response = True
                write_mode = "write-with-response"
            elif "write-without-response" in properties:
                use_response = False
                write_mode = "write-without-response"
            else:
                self._log_gatt_profile()
                raise VCXKnobConnectionError(
                    "Write characteristic supports neither 'write' nor "
                    "'write-without-response'",
                    retryable=False,
                )

            _LOGGER.debug(
                "Using %s for %s; properties=%s",
                write_mode,
                BLE_WRITE_CHARACTERISTIC_UUID,
                sorted(properties),
            )

            async with asyncio.timeout(10):
                await self._client.write_gatt_char(
                    write_char,
                    command,
                    response=use_response,
                )
        except asyncio.TimeoutError as err:
            raise VCXKnobConnectionError(
                "Command send timed out",
                retryable=True,
            ) from err
        except VCXKnobConnectionError:
            raise
        except BleakError as err:
            raise VCXKnobConnectionError(
                f"Command send failed: {err}",
                retryable=True,
            ) from err

    def _notification_handler(self, _sender: object, data: bytearray) -> None:
        """Reassemble fragmented BLE notifications into 8-byte status packets."""
        raw = bytes(data)
        _LOGGER.debug(
            "BLE notification (%d bytes): %s",
            len(raw),
            raw.hex().upper(),
        )

        self._rx_buffer.extend(raw)

        # Status packets begin with AA 08 88 and are exactly 8 bytes long.
        # Keep incomplete tails for the next BLE notification instead of dropping them.
        header = b"\xAA\x08\x88"
        while True:
            start = self._rx_buffer.find(header)
            if start < 0:
                # Preserve up to two trailing bytes in case they are the beginning
                # of the next AA 08 88 header.
                if len(self._rx_buffer) > 2:
                    del self._rx_buffer[:-2]
                break

            if start > 0:
                _LOGGER.debug(
                    "Discarding %d byte(s) before status packet header",
                    start,
                )
                del self._rx_buffer[:start]

            if len(self._rx_buffer) < 8:
                break

            packet = bytes(self._rx_buffer[:8])
            del self._rx_buffer[:8]
            packet_hex = packet.hex().upper()
            self._status_buffer.append(packet_hex)
            _LOGGER.debug("Reassembled status packet: %s", packet_hex)

            # Deliver only complete protocol packets to the coordinator.
            try:
                self._notification_callback(packet)
            except Exception:
                _LOGGER.exception("Status notification callback failed")

        if len(self._status_buffer) > 100:
            self._status_buffer = self._status_buffer[-100:]
    def get_status_buffer(self) -> list[str]:
        """Return complete status packets received so far."""
        return self._status_buffer.copy()

    def clear_status_buffer(self) -> None:
        """Clear parsed and partial status buffers before a new query."""
        self._status_buffer.clear()
        self._rx_buffer.clear()

# ============================================================================
# 数据更新协调器
# ============================================================================

class VCXKnobCoordinator(DataUpdateCoordinator[dict]):
    """用于管理 VCX-Knob 设备状态和更新的协调器

    此协调器:
    - 管理 BLE 连接
    - 定期轮询状态更新
    - 向实体提供当前状态
    - 处理断开后的重连
    - 执行来自实体的命令
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: VCXKnobBLEClient,
        poll_interval: int = DEFAULT_STATUS_POLL_INTERVAL,
    ) -> None:
        """初始化协调器

        Args:
            hass: Home Assistant 实例
            config_entry: 此集成的配置条目
            client: BLE 客户端实例
            poll_interval: 状态轮询间隔（秒）
        """
        self._config_entry = config_entry
        self._client = client
        self._poll_interval = max(MIN_POLL_INTERVAL, min(MAX_POLL_INTERVAL, poll_interval))

        self._device_state: dict[str, bool | int | str | None] = {
            "connected": False,
            "paired": False,
            "rssi": None,
            "device_address": self.device_address,  # 添加设备地址到状态
        }

        # 监听 Home Assistant 关闭事件
        config_entry.async_on_unload(
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self._async_shutdown)
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self._poll_interval),
        )


        # 检查配对状态
        hass.async_create_task(self._async_check_paired_status())

    @property
    def client(self) -> VCXKnobBLEClient:
        """获取 BLE 客户端"""
        return self._client

    @property
    def device_address(self) -> str:
        """获取设备地址"""
        return self._config_entry.data[CONF_DEVICE_ADDRESS]

    @property
    def device_name(self) -> str:
        """获取设备名称"""
        return self._config_entry.data.get(CONF_DEVICE_NAME, "VCX-Knob")

    @property
    def auto_connect(self) -> bool:
        """获取是否自动连接配置"""
        return self._config_entry.data.get(CONF_AUTO_CONNECT, DEFAULT_AUTO_CONNECT)

    async def _async_check_paired_status(self) -> None:
        """检查蓝牙设备配对状态"""
        try:
            process = await asyncio.create_subprocess_exec(
                "bluetoothctl",
                "info",
                self.device_address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
            result = stdout.decode() + stderr.decode()

            # 解析配对状态
            paired = "Paired: yes" in result
            self._device_state["paired"] = paired
            _LOGGER.debug("设备 %s 配对状态: %s", self.device_address, paired)

        except asyncio.TimeoutError:
            _LOGGER.warning("检查配对状态超时: %s", self.device_address)
            self._device_state["paired"] = False
        except FileNotFoundError:
            # 蓝牙命令不可用（可能不在 Linux 上）
            _LOGGER.debug("bluetoothctl 不可用，无法检查配对状态")
            self._device_state["paired"] = True  # 假设已配对
        except Exception as err:
            _LOGGER.warning("检查配对状态时出错: %s", err)
            self._device_state["paired"] = False

    async def _async_update_data(self) -> dict:
        """Maintain BLE connection and diagnostic state.

        VCX-Knob status is handled asynchronously from FFA2 notifications.
        The periodic coordinator refresh only maintains connectivity and RSSI;
        it deliberately sends no device command.
        """
        if not self.auto_connect:
            self._device_state["connected"] = False
            return self._device_state.copy()

        try:
            if not self._client.is_connected:
                _LOGGER.info("设备已断开，尝试重新连接...")
                await self._client.connect()

            self._device_state["rssi"] = self._client.rssi
            self._device_state["connected"] = True
            return self._device_state.copy()

        except VCXKnobConnectionError as err:
            self._device_state["connected"] = False
            if err.retryable:
                _LOGGER.warning("连接错误（将重试）: %s", err)
                return self._device_state.copy()
            raise UpdateFailed(f"不可重试的连接错误: {err}") from err

        except Exception as err:
            self._device_state["connected"] = False
            raise UpdateFailed(f"更新失败: {err}") from err

    @callback
    def handle_status_packet(self, data: bytes) -> None:
        """Decode one complete FFA2 status packet and notify HA entities."""
        try:
            packet = parse_status_packet(data)
            if packet is None:
                return

            decoded = decode_status_packet(packet)
            if decoded is None:
                return

            self._device_state.update(decoded)
            self._device_state["connected"] = self._client.is_connected
            self._device_state["rssi"] = self._client.rssi

            _LOGGER.debug(
                "Applied push status packet type=%s decoded=%s",
                packet.get("type"),
                decoded,
            )
            self.async_set_updated_data(self._device_state.copy())

        except Exception:
            _LOGGER.exception("Failed to process VCX-Knob status notification")
    async def async_send_command(
        self,
        cmd: str,
        d1: int = 0,
        d2: int = 0,
        d3: int = 0,
    ) -> None:
        """向设备发送命令

        这是实体发送命令的便捷方法

        Args:
            cmd: 命令码
            d1: 第一个数据字节
            d2: 第二个数据字节
            d3: 第三个数据字节

        Raises:
            VCXKnobConnectionError: 如果命令发送失败
        """
        await self._client.send_command(cmd, d1, d2, d3)

    async def async_disconnect(self) -> None:
        """从设备断开连接"""
        await self._client.disconnect()
        self._device_state["connected"] = False

    @callback
    def _async_shutdown(self, event: Event) -> None:
        """处理 Home Assistant 关闭

        Args:
            event: 关闭事件
        """
        _LOGGER.info("正在关闭 %s 的协调器", self.device_address)
        self.hass.async_create_task(self.async_disconnect())


# ============================================================================
# 工具函数
# ============================================================================

async def async_get_ble_device(
    hass: HomeAssistant,
    address: str,
) -> BluetoothServiceInfo | None:
    """通过地址获取 BLE 设备

    Args:
        hass: Home Assistant 实例
        address: BLE 设备地址

    Returns:
        如果找到返回 BluetoothServiceInfo，否则返回 None
    """
    return bluetooth.async_last_service_info(hass, address, connectable=True)


async def async_scan_for_device(
    hass: HomeAssistant,
    name_filter: str = BLE_DEVICE_NAME_FILTER,
    timeout: int = DEFAULT_SCAN_TIMEOUT,
) -> BluetoothServiceInfo | None:
    """扫描 VCX-Knob 设备

    Args:
        hass: Home Assistant 实例
        name_filter: 设备名称过滤器
        timeout: 扫描超时（秒）

    Returns:
        如果找到返回 BluetoothServiceInfo，否则返回 None
    """
    _LOGGER.info("正在扫描 BLE 设备 '%s'（超时: %d秒）", name_filter, timeout)

    current_address = set()

    def _service_info_callback(
        service_info: BluetoothServiceInfo,
        _change: bluetooth.BluetoothChange,
    ) -> None:
        """BLE 扫描器回调"""
        if service_info.name and name_filter in service_info.name:
            _LOGGER.debug(
                "发现设备: %s (%s)",
                service_info.name,
                service_info.address,
            )
            current_address.add(service_info.address)

    # 注册回调
    remove_callback = bluetooth.async_register_callback(
        hass,
        _service_info_callback,
        bluetooth.BluetoothCallbackMatcher(connectable=True),
    )

    try:
        # 确保扫描器正在运行
        scanner = async_get_scanner(hass)

        # 等待设备发现
        await asyncio.sleep(timeout)

        # 获取第一个找到的设备信息
        for address in current_address:
            device_info = await async_get_ble_device(hass, address)
            if device_info:
                return device_info

        return None

    finally:
        remove_callback()
