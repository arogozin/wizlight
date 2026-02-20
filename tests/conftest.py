"""Shared test fixtures for wizlight tests."""

from __future__ import annotations

from typing import Any

import pytest


class FakeBulb:
    """Simulates a WiZ bulb's UDP responses.

    Use this fixture to test wizlight without real network access.
    """

    def __init__(
        self,
        mac: str = "a8bb50aabbcc",
        module_name: str = "ESP01_SHRGB3_01ABI",
        fw_version: str = "1.30.0",
        state: bool = True,
        brightness: int = 128,
        scene_id: int = 0,
        color_temp: int | None = 4000,
        rgb: tuple[int, int, int] | None = None,
    ) -> None:
        self.mac = mac
        self.module_name = module_name
        self.fw_version = fw_version
        self._state = state
        self._brightness = brightness
        self._scene_id = scene_id
        self._color_temp = color_temp
        self._rgb = rgb

    def handle(self, message: dict[str, Any]) -> dict[str, Any]:
        """Handle an incoming message and return a response."""
        method = message.get("method", "")

        if method == "getPilot":
            return self._get_pilot_response()
        elif method == "setPilot":
            return self._set_pilot_response(message.get("params", {}))
        elif method == "getSystemConfig":
            return self._get_system_config_response()
        elif method == "registration":
            return {"method": "registration", "env": "pro", "result": {"success": True}}
        elif method == "getPower":
            return {"method": "getPower", "env": "pro", "result": {"w": 8.5}}
        else:
            return {"method": method, "env": "pro", "result": {"success": True}}

    def _get_pilot_response(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "mac": self.mac,
            "rssi": -60,
            "src": "",
            "state": self._state,
            "sceneId": self._scene_id,
            "dimming": self._brightness,
        }
        if self._color_temp and self._scene_id == 0:
            result["temp"] = self._color_temp
        if self._rgb and self._scene_id == 0:
            result["r"] = self._rgb[0]
            result["g"] = self._rgb[1]
            result["b"] = self._rgb[2]
        return {"method": "getPilot", "env": "pro", "result": result}

    def _set_pilot_response(self, params: dict[str, Any]) -> dict[str, Any]:
        if "state" in params:
            self._state = params["state"]
        if "dimming" in params:
            self._brightness = params["dimming"]
        if "sceneId" in params:
            self._scene_id = params["sceneId"]
        if "temp" in params:
            self._color_temp = params["temp"]
            self._rgb = None
            self._scene_id = 0
        if "r" in params:
            self._rgb = (params["r"], params["g"], params["b"])
            self._color_temp = None
            self._scene_id = 0
        return {"method": "setPilot", "env": "pro", "result": {"success": True}}

    def _get_system_config_response(self) -> dict[str, Any]:
        return {
            "method": "getSystemConfig",
            "env": "pro",
            "result": {
                "mac": self.mac,
                "homeId": 12345,
                "roomId": 1,
                "moduleName": self.module_name,
                "fwVersion": self.fw_version,
                "groupId": 0,
                "typeId": 0,
                "whiteRange": {"min": 2200, "max": 6500},
            },
        }


class MockUDPClient:
    """Mock UDPClient that routes to a FakeBulb."""

    def __init__(self, fake_bulb: FakeBulb) -> None:
        self._fake_bulb = fake_bulb
        self.sent_messages: list[dict[str, Any]] = []

    async def send(
        self, ip: str, message: dict[str, Any], timeout: float = 11.0
    ) -> dict[str, Any]:
        self.sent_messages.append(message)
        return self._fake_bulb.handle(message)

    async def send_no_reply(self, ip: str, message: dict[str, Any]) -> None:
        self.sent_messages.append(message)

    async def close(self) -> None:
        pass


@pytest.fixture
def fake_bulb() -> FakeBulb:
    """Create a fake WiZ bulb with default settings."""
    return FakeBulb()


@pytest.fixture
def mock_client(fake_bulb: FakeBulb) -> MockUDPClient:
    """Create a mock UDP client connected to the fake bulb."""
    return MockUDPClient(fake_bulb)
