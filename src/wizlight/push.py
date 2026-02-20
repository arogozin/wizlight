"""Push update manager for real-time WiZ device state changes.

WiZ devices can be registered to push state updates (syncPilot messages) whenever
their state changes (e.g., turned on/off via the WiZ app or physical switch).
This module manages the subscription lifecycle and dispatches updates to callbacks.

The PushManager listens on UDP port 38900. Devices send syncPilot messages there
after being registered via the 'registration' protocol method.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

from wizlight.pilot import PilotParser
from wizlight.protocol import PUSH_PORT

_LOGGER = logging.getLogger(__name__)

# Keep-alive interval — must re-register within this window or the device
# stops sending push updates. WiZ devices expect registration every ~20s.
KEEP_ALIVE_INTERVAL = 20


class PushManager:
    """Manages push subscriptions for multiple WiZ devices.

    Singleton pattern — use PushManager.get() to get the shared instance.
    Listens on UDP port 38900 for incoming syncPilot and firstBeat messages,
    dispatches them to registered callbacks keyed by MAC address.

    Usage:
        manager = PushManager.get()
        await manager.start()

        # Subscribe to updates from a specific device
        unsubscribe = manager.subscribe("aabbccddeeff", my_callback)

        # Later...
        unsubscribe()
        await manager.stop()
    """

    _instance: PushManager | None = None

    @classmethod
    def get(cls) -> PushManager:
        """Get or create the singleton PushManager instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self._transport: asyncio.DatagramTransport | None = None
        self._protocol: _PushProtocol | None = None
        self._subscribers: dict[str, list[Callable[[PilotParser], None]]] = {}
        self._discovery_callbacks: list[Callable[[str, str], None]] = []
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    async def start(self) -> None:
        """Start listening for push updates on port 38900."""
        if self._running:
            return

        loop = asyncio.get_running_loop()
        self._protocol = _PushProtocol(self._on_message)
        transport, _ = await loop.create_datagram_endpoint(
            lambda: self._protocol,
            local_addr=("0.0.0.0", PUSH_PORT),
        )
        self._transport = transport  # type: ignore[assignment]
        self._running = True
        _LOGGER.debug("PushManager listening on port %d", PUSH_PORT)

    async def stop(self) -> None:
        """Stop listening for push updates."""
        if self._transport:
            self._transport.close()
        self._transport = None
        self._protocol = None
        self._running = False
        _LOGGER.debug("PushManager stopped")

    def subscribe(
        self, mac: str, callback: Callable[[PilotParser], None]
    ) -> Callable[[], None]:
        """Subscribe to state updates for a device.

        Args:
            mac: Device MAC address (lowercase, no separators).
            callback: Function called with PilotParser on each state update.

        Returns:
            An unsubscribe function. Call it to remove this subscription.
        """
        mac_lower = mac.lower().replace(":", "").replace("-", "")
        if mac_lower not in self._subscribers:
            self._subscribers[mac_lower] = []
        self._subscribers[mac_lower].append(callback)

        def unsubscribe() -> None:
            import contextlib

            if mac_lower in self._subscribers:
                with contextlib.suppress(ValueError):
                    self._subscribers[mac_lower].remove(callback)
                if not self._subscribers[mac_lower]:
                    del self._subscribers[mac_lower]

        return unsubscribe

    def on_discovery(self, callback: Callable[[str, str], None]) -> Callable[[], None]:
        """Register a callback for device discovery via firstBeat.

        Args:
            callback: Function called with (ip, mac) when a new device is discovered.

        Returns:
            An unsubscribe function.
        """
        self._discovery_callbacks.append(callback)

        def unsubscribe() -> None:
            import contextlib

            with contextlib.suppress(ValueError):
                self._discovery_callbacks.remove(callback)

        return unsubscribe

    def _on_message(self, data: dict[str, Any], addr: tuple[str, int]) -> None:
        """Handle an incoming push message."""
        method = data.get("method", "")

        if method == "syncPilot":
            self._handle_sync_pilot(data, addr)
        elif method == "firstBeat":
            self._handle_first_beat(data, addr)
        else:
            _LOGGER.debug("Unknown push method '%s' from %s", method, addr)

    def _handle_sync_pilot(self, data: dict[str, Any], addr: tuple[str, int]) -> None:
        """Handle a syncPilot state update."""
        params = data.get("params", {})
        mac = params.get("mac", "").lower()

        if not mac:
            _LOGGER.debug("syncPilot without MAC from %s", addr)
            return

        parser = PilotParser(params)
        callbacks = self._subscribers.get(mac, [])
        for callback in callbacks:
            try:
                callback(parser)
            except Exception:
                _LOGGER.exception("Error in push callback for %s", mac)

    def _handle_first_beat(self, data: dict[str, Any], addr: tuple[str, int]) -> None:
        """Handle a firstBeat discovery message."""
        params = data.get("params", {})
        mac = params.get("mac", "").lower()
        ip = addr[0]

        if mac:
            for callback in self._discovery_callbacks:
                try:
                    callback(ip, mac)
                except Exception:
                    _LOGGER.exception("Error in discovery callback")


class _PushProtocol(asyncio.DatagramProtocol):
    """Internal UDP protocol for receiving push messages."""

    def __init__(self, on_message: Callable[[dict[str, Any], tuple[str, int]], None]) -> None:
        self._on_message = on_message

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        pass

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            message = json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return

        self._on_message(message, addr)

    def error_received(self, exc: Exception) -> None:
        _LOGGER.debug("Push protocol error: %s", exc)
