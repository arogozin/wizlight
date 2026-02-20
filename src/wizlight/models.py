"""Data models for WiZ devices.

Defines the core data structures used throughout the library:
- BulbClass: device category enum
- Features: capability flags per device
- KelvinRange: color temperature limits
- BulbType: complete device type descriptor
- DiscoveredBulb: network discovery result
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field  # noqa: F401
from enum import Enum


class BulbClass(Enum):
    """WiZ device classification."""

    RGB = "RGB"  # Full color + white
    TW = "TW"  # Tunable white (warm ↔ cool)
    DW = "DW"  # Dimmable white (single channel)
    SOCKET = "SOCKET"  # Smart plug (on/off only)
    FANDIM = "FANDIM"  # Fan with dimmable light


@dataclass
class Features:
    """Capability flags for a WiZ device."""

    color: bool = False
    brightness: bool = True
    color_temp: bool = False
    effect: bool = False
    dual_head: bool = False
    fan: bool = False
    fan_reverse: bool = False
    fan_breeze_mode: bool = False

    # Aliases
    @property
    def colorTemp(self) -> bool:  # noqa: N802
        return self.color_temp

    @property
    def color_tmp(self) -> bool:
        """Alias used by HA core integration."""
        return self.color_temp


@dataclass
class KelvinRange:
    """Color temperature range for a device."""

    min: int = 2200
    max: int = 6500


@dataclass
class BulbType:
    """Complete device type descriptor.

    Combines the device's classification, capabilities, and hardware specifics.
    Built from device module name via `from_module_name()` or populated directly.
    """

    bulb_type: BulbClass = BulbClass.RGB
    name: str = ""
    features: Features = field(default_factory=Features)
    kelvin_range: KelvinRange | None = None
    fw_version: str = ""
    white_channels: int = 1
    white_to_color_ratio: int = 20
    fan_speed_range: int | None = None

    @classmethod
    def from_module_name(cls, module_name: str, white_range: dict | None = None) -> BulbType:
        """Detect bulb type from its module name string.

        WiZ devices report module names like 'ESP01_SHRGB3_01ABI' which encode
        the hardware capabilities. This method parses the name to determine
        the device class and features.
        """
        from wizlight.devices import detect_bulb_type

        return detect_bulb_type(module_name, white_range)

    # Alias
    @classmethod
    def from_data(cls, module_name: str, white_range: dict | None = None) -> BulbType:
        return cls.from_module_name(module_name, white_range)


@dataclass
class DiscoveredBulb:
    """A WiZ device found via network discovery."""

    ip_address: str
    mac_address: str


@dataclass
class FirmwareInfo:
    """Firmware information for a WiZ device."""

    version: str
    module_name: str
    home_id: int | None = None
    room_id: int | None = None


@dataclass
class Schedule:
    """A WiZ device schedule entry."""

    days: list[int]  # 0=Mon .. 6=Sun
    hour: int
    minute: int
    scene_id: int | None = None
    dimming: int | None = None
    color_temp: int | None = None
    enabled: bool = True
