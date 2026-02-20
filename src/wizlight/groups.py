"""WiZ native room and group management.

WiZ devices can be assigned to rooms and homes. Devices in the same room can be
controlled as a group via the WiZ cloud or by sending commands to each device.
This module provides helpers for reading and writing room/home assignments.

Protocol methods: getSystemConfig (roomId, homeId), setSystemConfig
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RoomAssignment:
    """A device's room and home assignment."""

    home_id: int | None = None
    room_id: int | None = None
    group_id: int | None = None

    @classmethod
    def from_system_config(cls, config: dict[str, Any]) -> RoomAssignment:
        """Extract room assignment from a getSystemConfig response."""
        return cls(
            home_id=config.get("homeId"),
            room_id=config.get("roomId"),
            group_id=config.get("groupId"),
        )


def build_room_params(
    home_id: int | None = None,
    room_id: int | None = None,
    group_id: int | None = None,
) -> dict[str, Any]:
    """Build setSystemConfig params for room assignment."""
    params: dict[str, Any] = {}
    if home_id is not None:
        params["homeId"] = home_id
    if room_id is not None:
        params["roomId"] = room_id
    if group_id is not None:
        params["groupId"] = group_id
    return params
