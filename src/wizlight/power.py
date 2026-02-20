"""WiZ device power monitoring.

Some WiZ devices (particularly smart plugs) support power consumption reporting
via the getPower protocol method. This module provides typed models for the data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PowerData:
    """Power consumption data from a WiZ device."""

    watts: float = 0.0
    total_kwh: float = 0.0

    @classmethod
    def from_response(cls, result: dict[str, Any]) -> PowerData:
        """Parse a getPower response."""
        return cls(
            watts=float(result.get("w", 0)),
            total_kwh=float(result.get("kwh", 0)),
        )
