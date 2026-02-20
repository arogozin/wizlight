"""Async UDP transport layer for WiZ device communication.

This module provides the low-level UDP communication primitives. All WiZ devices
communicate via JSON messages over UDP on port 38899. This module handles:
- Async send/receive with timeouts
- Retry with progressive backoff
- Connection pooling per target IP
- JSON serialization/deserialization
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from wizlight.exceptions import (
    WizLightCommandError,
    WizLightConnectionError,
    WizLightTimeOutError,
)

_LOGGER = logging.getLogger(__name__)

WIZ_PORT = 38899
PUSH_PORT = 38900

# Progressive backoff delays (seconds) between retries
_RETRY_DELAYS = [0, 0.5, 1.5, 3.0, 6.0]
_TOTAL_TIMEOUT = 11.0


class WizProtocol(asyncio.DatagramProtocol):
    """Async UDP datagram protocol for WiZ device communication.

    Handles a single request-response cycle. A new protocol instance is created
    for each outbound message, or reused via the UDPClient transport pool.
    """

    def __init__(self) -> None:
        self.transport: asyncio.DatagramTransport | None = None
        self._response_future: asyncio.Future[dict[str, Any]] | None = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore[assignment]

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            message = json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            _LOGGER.debug("Malformed response from %s: %s", addr, exc)
            return

        if self._response_future and not self._response_future.done():
            self._response_future.set_result(message)

    def error_received(self, exc: Exception) -> None:
        _LOGGER.debug("Protocol error: %s", exc)
        if self._response_future and not self._response_future.done():
            self._response_future.set_exception(
                WizLightConnectionError(f"UDP error: {exc}")
            )

    def connection_lost(self, exc: Exception | None) -> None:
        if exc and self._response_future and not self._response_future.done():
            self._response_future.set_exception(
                WizLightConnectionError(f"Connection lost: {exc}")
            )


class UDPClient:
    """High-level async UDP client for WiZ devices.

    Handles message serialization, retries with backoff, and transport management.

    Usage:
        client = UDPClient()
        response = await client.send("192.168.1.100", {"method": "getPilot"})
        await client.close()
    """

    def __init__(
        self,
        port: int = WIZ_PORT,
        retry_delays: list[float] | None = None,
    ) -> None:
        self._port = port
        self._retry_delays = retry_delays or list(_RETRY_DELAYS)
        self._transport: asyncio.DatagramTransport | None = None
        self._protocol: WizProtocol | None = None

    async def _ensure_transport(self) -> tuple[asyncio.DatagramTransport, WizProtocol]:
        """Create or reuse the UDP transport."""
        if self._transport is not None and not self._transport.is_closing():
            assert self._protocol is not None
            return self._transport, self._protocol

        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            WizProtocol,
            local_addr=("0.0.0.0", 0),
        )
        self._transport = transport  # type: ignore[assignment]
        self._protocol = protocol  # type: ignore[assignment]
        return self._transport, self._protocol  # type: ignore[return-value]

    async def send(
        self,
        ip: str,
        message: dict[str, Any],
        timeout: float = _TOTAL_TIMEOUT,
    ) -> dict[str, Any]:
        """Send a message and await the response.

        Args:
            ip: Target device IP address.
            message: The command dict (will be JSON-encoded).
            timeout: Maximum total time to wait across all retries.

        Returns:
            The parsed response dict.

        Raises:
            WizLightTimeOutError: If no response after all retries.
            WizLightConnectionError: If the UDP transport fails.
            WizLightCommandError: If the device returns an error response.
        """
        data = json.dumps(message).encode("utf-8")
        last_exc: Exception | None = None

        for delay in self._retry_delays:
            if delay > 0:
                await asyncio.sleep(delay)

            try:
                response = await self._send_once(ip, data, timeout=min(timeout, 3.0))
            except (TimeoutError, WizLightConnectionError) as exc:
                last_exc = exc
                _LOGGER.debug("Retry after %s: %s", type(exc).__name__, exc)
                continue

            # Check for error in response
            if "error" in response:
                raise WizLightCommandError(
                    f"Device {ip} error: {response['error']}"
                )

            return response

        raise WizLightTimeOutError(
            f"No response from {ip}:{self._port} after {len(self._retry_delays)} attempts"
        ) from last_exc

    async def _send_once(
        self, ip: str, data: bytes, timeout: float = 3.0
    ) -> dict[str, Any]:
        """Send a single UDP message and await the response."""
        transport, protocol = await self._ensure_transport()

        loop = asyncio.get_running_loop()
        protocol._response_future = loop.create_future()

        try:
            transport.sendto(data, (ip, self._port))
            return await asyncio.wait_for(protocol._response_future, timeout=timeout)
        except TimeoutError as exc:
            raise TimeoutError(f"No response from {ip}") from exc

    async def send_no_reply(self, ip: str, message: dict[str, Any]) -> None:
        """Send a message without waiting for a response (fire-and-forget)."""
        transport, _ = await self._ensure_transport()
        data = json.dumps(message).encode("utf-8")
        transport.sendto(data, (ip, self._port))

    async def close(self) -> None:
        """Close the UDP transport."""
        if self._transport and not self._transport.is_closing():
            self._transport.close()
        self._transport = None
        self._protocol = None


class BroadcastProtocol(asyncio.DatagramProtocol):
    """UDP protocol for broadcast-based device discovery.

    Collects responses from WiZ devices on the local network when a broadcast
    registration message is sent.
    """

    def __init__(self) -> None:
        self.transport: asyncio.DatagramTransport | None = None
        self.responses: list[tuple[dict[str, Any], tuple[str, int]]] = []

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore[assignment]

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            message = json.loads(data.decode("utf-8"))
            self.responses.append((message, addr))
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    def error_received(self, exc: Exception) -> None:
        _LOGGER.debug("Broadcast protocol error: %s", exc)

    def connection_lost(self, exc: Exception | None) -> None:
        pass
