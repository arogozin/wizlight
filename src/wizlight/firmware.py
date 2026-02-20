"""WiZ device firmware information and OTA helpers.

Protocol methods: getSystemConfig (fwVersion, moduleName), getDevInfo
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DeviceInfo:
    """Comprehensive device information from getSystemConfig and getDevInfo."""

    mac: str = ""
    module_name: str = ""
    fw_version: str = ""
    home_id: int | None = None
    room_id: int | None = None
    type_id: int | None = None
    ip: str = ""

    @classmethod
    def from_system_config(cls, config: dict[str, Any], ip: str = "") -> DeviceInfo:
        """Build from a getSystemConfig response."""
        return cls(
            mac=config.get("mac", ""),
            module_name=config.get("moduleName", ""),
            fw_version=config.get("fwVersion", ""),
            home_id=config.get("homeId"),
            room_id=config.get("roomId"),
            type_id=config.get("typeId"),
            ip=ip,
        )
