"""WiZ native schedule management.

WiZ devices support on-device schedules that persist even when the network is down.
Schedules are stored on the device and triggered by the bulb's internal clock.
This module provides helpers for reading and writing schedules.

Protocol methods: getSchdPset, setSchdPset, syncSchdPset
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ScheduleEntry:
    """A single schedule entry on a WiZ device.

    Attributes:
        index: Schedule slot index (0-based).
        enabled: Whether this schedule is active.
        days: Bitmask of active days (bit 0 = Monday, bit 6 = Sunday).
            E.g., 0b1111111 = every day, 0b0100000 = Saturday only.
        hour: Hour (0-23).
        minute: Minute (0-59).
        scene_id: Scene to activate (None = use other params).
        dimming: Brightness (10-100).
        color_temp: Color temperature in Kelvin (None = use scene).
    """

    index: int = 0
    enabled: bool = True
    days: int = 0b1111111  # Every day
    hour: int = 0
    minute: int = 0
    scene_id: int | None = None
    dimming: int | None = None
    color_temp: int | None = None

    @property
    def day_list(self) -> list[str]:
        """Human-readable list of active days."""
        names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return [names[i] for i in range(7) if self.days & (1 << i)]

    def to_protocol_dict(self) -> dict[str, Any]:
        """Convert to the dict format expected by the WiZ protocol."""
        entry: dict[str, Any] = {
            "i": self.index,
            "en": 1 if self.enabled else 0,
            "d": self.days,
            "h": self.hour,
            "m": self.minute,
        }
        if self.scene_id is not None:
            entry["sceneId"] = self.scene_id
        if self.dimming is not None:
            entry["dimming"] = self.dimming
        if self.color_temp is not None:
            entry["temp"] = self.color_temp
        return entry

    @classmethod
    def from_protocol_dict(cls, data: dict[str, Any]) -> ScheduleEntry:
        """Create from a dict received from the WiZ protocol."""
        return cls(
            index=data.get("i", 0),
            enabled=bool(data.get("en", 1)),
            days=data.get("d", 0b1111111),
            hour=data.get("h", 0),
            minute=data.get("m", 0),
            scene_id=data.get("sceneId"),
            dimming=data.get("dimming"),
            color_temp=data.get("temp"),
        )


def parse_schedule_response(result: dict[str, Any]) -> list[ScheduleEntry]:
    """Parse a getSchdPset response into ScheduleEntry objects."""
    entries = result.get("schdPsetList", [])
    return [ScheduleEntry.from_protocol_dict(e) for e in entries]


def build_schedule_params(schedules: list[ScheduleEntry]) -> dict[str, Any]:
    """Build setSchdPset params from ScheduleEntry objects."""
    return {"schdPsetList": [s.to_protocol_dict() for s in schedules]}
