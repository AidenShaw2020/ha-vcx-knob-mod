"""Constants for the VCX-Knob integration.

The command map in this file is intentionally limited to commands verified in
DM Toilet Control 1.0.6. Unsupported upstream guesses are not exposed as
entities.
"""

from dataclasses import dataclass, field
from enum import StrEnum

from homeassistant.helpers.entity import EntityCategory

DOMAIN = "vcx_knob"
MANUFACTURER = "VCX"
MODEL = "Knob Smart Toilet"

DEFAULT_SCAN_TIMEOUT = 10
DEFAULT_CONNECTION_TIMEOUT = 30
DEFAULT_STATUS_POLL_INTERVAL = 30
DEFAULT_AUTO_CONNECT = True

BLE_SERVICE_UUID = "0000FFA0-0000-1000-8000-00805F9B34FB"
BLE_WRITE_CHARACTERISTIC_UUID = "0000FFA1-0000-1000-8000-00805F9B34FB"
BLE_NOTIFY_CHARACTERISTIC_UUID = "0000FFA2-0000-1000-8000-00805F9B34FB"
BLE_DEVICE_NAME_FILTER = "VCX-Knob"

PROTOCOL_HEADER = 0xAA
PROTOCOL_LENGTH = 0x08
PROTOCOL_CMD_TYPE = 0x02
PROTOCOL_AMBIENT_TYPE = 0x03
PROTOCOL_STATUS_TYPE = 0x88


class Command(StrEnum):
    """Commands verified in DM Toilet Control 1.0.6."""

    FEMININE_WASH = "01"
    REAR_WASH = "02"
    CHILD_WASH = "03"
    DRY = "04"
    LID_TOGGLE = "05"
    SEAT_TOGGLE = "06"
    FLUSH = "07"
    AUTO = "08"
    STOP = "09"
    POWER = "0E"
    LIGHT = "0F"
    WATER_TEMPERATURE = "10"
    SELF_CLEAN = "11"
    FOAM = "12"
    ECO = "13"
    MASSAGE = "14"
    WIND_TEMPERATURE = "20"
    WATER_PRESSURE = "21"
    NOZZLE_POSITION = "22"
    SEAT_TEMPERATURE = "30"


class StatusPacketType(StrEnum):
    """Best-effort FFA2 packet types from the independent reverse engineering."""

    TYPE_01 = "01"
    TYPE_02 = "02"
    TYPE_03 = "03"
    TYPE_04 = "04"
    TYPE_05 = "05"
    TYPE_06 = "06"


WATER_SEAT_TEMPERATURE_MAP = {
    0: "off",
    1: 34,
    2: 37,
    3: 40,
}

WIND_TEMPERATURE_MAP = {
    0: "off",
    1: 45,
    2: 50,
    3: 55,
}

# DM Toilet Control starts each process with these local values. The app does
# not read them from the toilet before sending commands.
APP_DEFAULT_WATER_TEMP_CODE = 1
APP_DEFAULT_WIND_TEMP_CODE = 0
APP_DEFAULT_SEAT_TEMP_CODE = 0
APP_DEFAULT_WATER_PRESSURE_LEVEL = 0
APP_DEFAULT_NOZZLE_POSITION_LEVEL = 0

APP_TEMPERATURE_STATE_KEYS = frozenset(
    {
        "water_temp_code",
        "wind_temp_code",
        "seat_temp_code",
    }
)
APP_LEVEL_STATE_KEYS = frozenset(
    {
        "water_pressure_level",
        "nozzle_position_level",
    }
)


@dataclass(frozen=True)
class EntityDescription:
    key: str
    name: str
    entity_category: EntityCategory | str | None = None
    translation_key: str | None = None
    device_class: str | None = None
    unit: str | None = None
    state_class: str | None = None

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("key must not be empty")
        if not self.name:
            raise ValueError("name must not be empty")


@dataclass(frozen=True)
class SwitchEntityDescription(EntityDescription):
    command: str | None = None
    data_byte: str = "00"


@dataclass(frozen=True)
class SensorEntityDescription(EntityDescription):
    icon: str | None = None


@dataclass(frozen=True)
class ButtonEntityDescription(EntityDescription):
    command: str = field(default="")
    data_byte: str = "00"


@dataclass(frozen=True)
class SelectEntityDescription(EntityDescription):
    command: str = field(default="")
    options: list[str] = field(default_factory=list)
    options_map: dict[str, int] = field(default_factory=dict)
    state_key: str | None = None
    payload_kind: str = "temperature"
    icon: str | None = None


SELECTS = [
    SelectEntityDescription(
        key="water_temperature",
        name="Water temperature",
        icon="mdi:water-thermometer",
        command=Command.WATER_TEMPERATURE,
        options=["off", "34", "37", "40"],
        options_map={"off": 0, "34": 1, "37": 2, "40": 3},
        state_key="water_temp_code",
        payload_kind="temperature",
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(
        key="seat_temperature",
        name="Seat temperature",
        icon="mdi:seat",
        command=Command.SEAT_TEMPERATURE,
        options=["off", "34", "37", "40"],
        options_map={"off": 0, "34": 1, "37": 2, "40": 3},
        state_key="seat_temp_code",
        payload_kind="temperature",
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(
        key="wind_temperature",
        name="Dryer temperature",
        icon="mdi:air-conditioner",
        command=Command.WIND_TEMPERATURE,
        options=["off", "45", "50", "55"],
        options_map={"off": 0, "45": 1, "50": 2, "55": 3},
        state_key="wind_temp_code",
        payload_kind="temperature",
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(
        key="water_pressure_level",
        name="Water pressure",
        icon="mdi:water-pump",
        command=Command.WATER_PRESSURE,
        options=["0", "1", "2", "3"],
        options_map={"0": 0, "1": 1, "2": 2, "3": 3},
        state_key="water_pressure_level",
        payload_kind="level",
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(
        key="nozzle_position",
        name="Nozzle position",
        icon="mdi:ray-start-arrow",
        command=Command.NOZZLE_POSITION,
        options=["0", "1", "2", "3"],
        options_map={"0": 0, "1": 1, "2": 2, "3": 3},
        state_key="nozzle_position_level",
        payload_kind="level",
        entity_category=EntityCategory.CONFIG,
    ),
]

CONF_DEVICE_ADDRESS = "device_address"
CONF_DEVICE_NAME = "device_name"
CONF_AUTO_CONNECT = "auto_connect"

SERVICE_SEND_COMMAND = "send_command"

ATTR_LAST_UPDATE = "last_update"
ATTR_COMMAND_SENT = "command_sent"
ATTR_PACKET_RECEIVED = "packet_received"