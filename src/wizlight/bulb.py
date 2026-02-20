"""Main WiZ device control interface.

The `wizlight` class is the primary interface for controlling a single WiZ device.
One instance represents one physical device at a known IP address.

Usage:
    from wizlight import wizlight, PilotBuilder

    bulb = wizlight("192.168.1.100")
    await bulb.updateState()
    print(bulb.state.get_brightness())

    await bulb.turn_on(PilotBuilder(scene="Fireplace", brightness=200))
    await bulb.turn_off()
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from wizlight.effects import get_scenes_for_bulb_type
from wizlight.models import BulbType, DiscoveredBulb, FirmwareInfo
from wizlight.pilot import PilotBuilder, PilotParser
from wizlight.protocol import WIZ_PORT, UDPClient

_LOGGER = logging.getLogger(__name__)

# Constant for PIR (motion sensor) source identification in state responses.
PIR_SOURCE = "pir"

# Keep-alive interval for push registration (seconds)
_PUSH_KEEP_ALIVE = 20


class wizlight:  # noqa: N801 — lowercase class name is intentional
    """Control interface for a single WiZ device.

    Args:
        ip: The device's IP address on the local network.
        port: UDP port (default 38899).
        client: Optional shared UDPClient instance. If None, one is created.
    """

    def __init__(
        self,
        ip: str,
        port: int = WIZ_PORT,
        client: UDPClient | None = None,
    ) -> None:
        self.ip = ip
        self.port = port
        self._client = client or UDPClient(port=port)
        self._owns_client = client is None
        self._state: PilotParser | None = None
        self._bulbtype: BulbType | None = None
        self._mac: str | None = None
        self._system_config: dict[str, Any] | None = None
        self._push_callback: Callable[[PilotParser], None] | None = None
        self._push_task: asyncio.Task[None] | None = None
        self._discovery_callback: Callable[[DiscoveredBulb], None] | None = None
        self._supported_scenes: list[str] | None = None
        self.power_monitoring: bool | None = None

    # --- State ---

    @property
    def state(self) -> PilotParser | None:
        """The most recently fetched device state, or None if never fetched."""
        return self._state

    @property
    def status(self) -> bool:
        """Whether the device is currently on."""
        if self._state is None:
            return False
        return self._state.get_state()

    @property
    def bulbtype(self) -> BulbType | None:
        """The detected device type, or None if never queried."""
        return self._bulbtype

    @property
    def mac(self) -> str | None:
        """The device's MAC address, or None if never queried."""
        return self._mac

    @property
    def diagnostics(self) -> dict[str, Any]:
        """Diagnostic information for this device."""
        diag: dict[str, Any] = {
            "ip": self.ip,
            "mac": self._mac,
            "power_monitoring": self.power_monitoring,
        }
        if self._bulbtype:
            diag["bulb_type"] = self._bulbtype.bulb_type.value
            diag["module_name"] = self._bulbtype.name
            diag["fw_version"] = self._bulbtype.fw_version
        if self._system_config:
            diag["system_config"] = self._system_config
        if self._state:
            diag["state"] = self._state.pilotResult
        return diag

    async def updateState(self) -> PilotParser:  # noqa: N802
        """Fetch and return the current device state."""
        response = await self._send({"method": "getPilot", "params": {}})
        result = response.get("result", response.get("params", {}))
        self._state = PilotParser(result)

        # Cache MAC if present
        mac = result.get("mac")
        if mac:
            self._mac = mac

        return self._state

    async def get_bulbtype(self) -> BulbType:
        """Query and cache the device type."""
        config = await self.get_system_config()
        module_name = config.get("moduleName", "")
        white_range = config.get("whiteRange")

        self._bulbtype = BulbType.from_module_name(module_name, white_range)
        self._bulbtype.fw_version = config.get("fwVersion", "")

        # Detect white channels from module name
        name_upper = module_name.upper()
        if "RGBWW" in name_upper:
            self._bulbtype.white_channels = 2
        elif "RGBW" in name_upper:
            self._bulbtype.white_channels = 1

        # Cache MAC
        mac = config.get("mac")
        if mac:
            self._mac = mac

        return self._bulbtype

    async def getMac(self) -> str:  # noqa: N802
        """Get the device's MAC address."""
        if self._mac:
            return self._mac

        config = await self.get_system_config()
        self._mac = config.get("mac", "")
        return self._mac

    async def getSupportedScenes(self) -> list[str]:  # noqa: N802
        """Get the list of scene names supported by this device.

        Returns:
            List of scene name strings.
        """
        if self._supported_scenes is not None:
            return self._supported_scenes

        if self._bulbtype is None:
            await self.get_bulbtype()

        assert self._bulbtype is not None
        scenes_dict = get_scenes_for_bulb_type(self._bulbtype.bulb_type.value)
        self._supported_scenes = sorted(scenes_dict.values())
        return self._supported_scenes

    # --- Control ---

    async def turn_on(self, pilot: PilotBuilder | None = None) -> None:
        """Turn on the device with optional parameters."""
        if pilot is None:
            pilot = PilotBuilder(state=True)

        params = pilot.to_dict()
        await self._send({"method": "setPilot", "params": params})

    async def turn_off(self) -> None:
        """Turn off the device."""
        await self._send({"method": "setPilot", "params": {"state": False}})

    async def set_speed(self, speed: int) -> None:
        """Set the effect speed (1-200)."""
        await self._send({"method": "setPilot", "params": {"speed": speed}})

    async def set_ratio(self, ratio: int) -> None:
        """Set the dual-head ratio (0-100)."""
        await self._send({"method": "setPilot", "params": {"ratio": ratio}})

    # --- Fan control ---

    async def fan_turn_on(
        self, mode: int | None = None, speed: int | None = None
    ) -> None:
        """Turn on the fan."""
        params: dict[str, Any] = {"fanState": 1}
        if mode is not None:
            params["fanMode"] = mode
        if speed is not None:
            params["fanSpeed"] = speed
        await self._send({"method": "setPilot", "params": params})

    async def fan_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        await self._send({"method": "setPilot", "params": {"fanState": 0}})

    async def fan_set_state(
        self,
        mode: int | None = None,
        speed: int | None = None,
        reverse: int | None = None,
    ) -> None:
        """Set fan state parameters."""
        params: dict[str, Any] = {}
        if mode is not None:
            params["fanMode"] = mode
        if speed is not None:
            params["fanSpeed"] = speed
        if reverse is not None:
            params["fanRevrs"] = reverse
        if params:
            await self._send({"method": "setPilot", "params": params})

    # --- System configuration ---

    async def get_system_config(self) -> dict[str, Any]:
        """Get the device system configuration."""
        response = await self._send({"method": "getSystemConfig", "params": {}})
        self._system_config = response.get("result", {})
        return self._system_config

    async def set_system_config(self, **kwargs: Any) -> None:
        """Modify the device system configuration."""
        await self._send({"method": "setSystemConfig", "params": kwargs})

    async def get_user_config(self) -> dict[str, Any]:
        """Get the device user configuration."""
        response = await self._send({"method": "getUserConfig", "params": {}})
        return response.get("result", {})

    async def set_user_config(self, **kwargs: Any) -> None:
        """Modify the device user configuration."""
        await self._send({"method": "setUserConfig", "params": kwargs})

    # --- Firmware ---

    async def get_firmware_info(self) -> FirmwareInfo:
        """Get firmware information."""
        config = await self.get_system_config()
        return FirmwareInfo(
            version=config.get("fwVersion", ""),
            module_name=config.get("moduleName", ""),
            home_id=config.get("homeId"),
            room_id=config.get("roomId"),
        )

    async def reboot(self) -> None:
        """Reboot the device."""
        await self._send({"method": "reboot", "params": {}})

    # --- Power monitoring ---

    async def get_power(self) -> float | None:
        """Get power consumption in watts (if supported).

        Returns:
            Power in watts, or None if not supported.
        """
        try:
            response = await self._send({"method": "getPower", "params": {}})
            result = response.get("result", {})
            watts = result.get("w")
            if watts is not None:
                self.power_monitoring = True
                return float(watts)
            self.power_monitoring = False
            return None
        except Exception:
            self.power_monitoring = False
            return None

    # --- Schedules ---

    async def get_schedules(self) -> list[dict[str, Any]]:
        """Get device schedules."""
        response = await self._send({"method": "getSchdPset", "params": {}})
        return response.get("result", {}).get("schdPsetList", [])

    async def set_schedule(self, schedule: dict[str, Any]) -> None:
        """Set a device schedule."""
        await self._send({"method": "setSchdPset", "params": schedule})

    async def delete_schedule(self, index: int) -> None:
        """Delete a schedule by index."""
        params = {"schdPsetList": [{"i": index, "en": 0}]}
        await self._send({"method": "setSchdPset", "params": params})

    # --- Room/group management ---

    async def get_room_id(self) -> int | None:
        """Get the WiZ room ID this device belongs to."""
        config = await self.get_system_config()
        return config.get("roomId")

    async def set_room_id(self, room_id: int) -> None:
        """Assign this device to a WiZ room."""
        await self.set_system_config(roomId=room_id)

    async def get_home_id(self) -> int | None:
        """Get the WiZ home ID this device belongs to."""
        config = await self.get_system_config()
        return config.get("homeId")

    # --- Push registration ---

    async def start_push(self, callback: Callable[[PilotParser], None]) -> None:
        """Start receiving push state updates from this device.

        Registers with the device for syncPilot messages and starts a
        background keep-alive task. The callback is invoked whenever the
        device reports a state change.

        Args:
            callback: Function called with PilotParser on each state update.
        """
        from wizlight.push import PushManager

        self._push_callback = callback
        manager = PushManager.get()

        if not manager.is_running:
            await manager.start()

        # Subscribe to updates for our MAC
        mac = await self.getMac()
        manager.subscribe(mac, self._on_push_update)

        # Register with the device and start keep-alive
        await self._register_push()
        self._push_task = asyncio.create_task(self._push_keep_alive())

    def _on_push_update(self, state: PilotParser) -> None:
        """Handle a push state update."""
        self._state = state
        if self._push_callback:
            self._push_callback(state)

    async def _register_push(self) -> None:
        """Register for push updates from the device."""

        local_ip = self._get_local_ip()
        try:
            await self.register_for_push(local_ip)
        except Exception:
            _LOGGER.debug("Failed to register for push with %s", self.ip)

    async def _push_keep_alive(self) -> None:
        """Periodically re-register for push updates."""
        try:
            while True:
                await asyncio.sleep(_PUSH_KEEP_ALIVE)
                try:
                    await self._register_push()
                except Exception:
                    _LOGGER.debug("Push keep-alive failed for %s", self.ip)
        except asyncio.CancelledError:
            pass

    def _get_local_ip(self) -> str:
        """Get the local IP address for push registration."""
        import socket

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect((self.ip, self.port))
            local_ip = sock.getsockname()[0]
            sock.close()
            return local_ip
        except Exception:
            return "0.0.0.0"

    def set_discovery_callback(
        self, callback: Callable[[DiscoveredBulb], None]
    ) -> None:
        """Set a callback for device discovery via push firstBeat."""
        self._discovery_callback = callback

    async def register_for_push(
        self,
        listener_ip: str,
        listener_mac: str = "aaaaaaaaaaaa",
    ) -> None:
        """Register to receive push state updates from this device."""
        await self._send({
            "method": "registration",
            "id": 105,
            "params": {
                "phoneIp": listener_ip,
                "phoneMac": listener_mac,
                "register": True,
            },
        })

    async def unregister_push(
        self,
        listener_ip: str,
        listener_mac: str = "aaaaaaaaaaaa",
    ) -> None:
        """Unregister from push state updates."""
        await self._send({
            "method": "registration",
            "id": 105,
            "params": {
                "phoneIp": listener_ip,
                "phoneMac": listener_mac,
                "register": False,
            },
        })

    # --- Raw protocol access ---

    async def send_raw(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send an arbitrary protocol message."""
        return await self._send({"method": method, "params": params or {}})

    # --- Internal ---

    async def _send(self, message: dict[str, Any]) -> dict[str, Any]:
        """Send a message to this device and return the response."""
        return await self._client.send(self.ip, message)

    async def close(self) -> None:
        """Close the UDP client and stop push updates."""
        import contextlib

        if self._push_task and not self._push_task.done():
            self._push_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._push_task
        if self._owns_client:
            await self._client.close()

    async def async_close(self) -> None:
        """Close the connection. Alias for close()."""
        await self.close()

    async def __aenter__(self) -> wizlight:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
