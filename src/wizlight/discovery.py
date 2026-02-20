"""WiZ device discovery via UDP broadcast and mDNS.

Discovers WiZ devices on the local network using two methods:
1. UDP broadcast: Sends a registration query to 255.255.255.255:38899
2. mDNS/Zeroconf: Looks for _wiz._udp.local. services (requires zeroconf extra)
"""

from __future__ import annotations

import asyncio
import logging

from wizlight.models import DiscoveredBulb
from wizlight.protocol import WIZ_PORT, BroadcastProtocol

_LOGGER = logging.getLogger(__name__)

# Registration message used for discovery — fake credentials, register=false
_DISCOVERY_MESSAGE = (
    b'{"method":"registration","params":{"phoneIp":"1.2.3.4",'
    b'"register":false,"phoneMac":"aaaaaaaaaaaa"}}'
)


async def find_wizlights(
    timeout: int = 5,
    address: str = "255.255.255.255",
) -> list[DiscoveredBulb]:
    """Discover WiZ devices via UDP broadcast.

    Sends a registration query to the broadcast address and collects responses.
    Each responding device is returned as a DiscoveredBulb.

    Args:
        timeout: How long to listen for responses (seconds).
        address: Broadcast address to query. Default: 255.255.255.255.

    Returns:
        List of DiscoveredBulb with IP and MAC addresses.
    """
    loop = asyncio.get_running_loop()

    transport, protocol = await loop.create_datagram_endpoint(
        BroadcastProtocol,
        local_addr=("0.0.0.0", 0),
        allow_broadcast=True,
    )

    try:
        # Send discovery broadcast every second
        for _ in range(timeout):
            transport.sendto(_DISCOVERY_MESSAGE, (address, WIZ_PORT))
            await asyncio.sleep(1)

        # Deduplicate by MAC address
        seen: dict[str, DiscoveredBulb] = {}
        for response, addr in protocol.responses:  # type: ignore[attr-defined]
            result = response.get("result", {})
            mac = result.get("mac", "")
            if mac and mac not in seen:
                seen[mac] = DiscoveredBulb(
                    ip_address=addr[0],
                    mac_address=mac,
                )

        return list(seen.values())
    finally:
        transport.close()


async def discover_mdns(timeout: int = 5) -> list[DiscoveredBulb]:
    """Discover WiZ devices via mDNS/Zeroconf.

    Requires the 'zeroconf' extra to be installed.

    Args:
        timeout: How long to listen for services (seconds).

    Returns:
        List of DiscoveredBulb with IP and MAC addresses.
    """
    try:
        from zeroconf import ServiceBrowser, Zeroconf
        from zeroconf.asyncio import AsyncZeroconf
    except ImportError:
        _LOGGER.warning(
            "mDNS discovery requires the 'zeroconf' extra. "
            "Install with: pip install wizlight[zeroconf]"
        )
        return []

    bulbs: dict[str, DiscoveredBulb] = {}

    class WizListener:
        def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            info = zc.get_service_info(type_, name)
            if info and info.addresses:
                import socket

                ip = socket.inet_ntoa(info.addresses[0])
                mac = info.properties.get(b"mac", b"").decode("utf-8", errors="replace")
                if mac:
                    bulbs[mac] = DiscoveredBulb(ip_address=ip, mac_address=mac)

        def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            pass

        def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            pass

    azc = AsyncZeroconf()
    listener = WizListener()
    browser = ServiceBrowser(azc.zeroconf, "_wiz._udp.local.", listener)

    try:
        await asyncio.sleep(timeout)
    finally:
        browser.cancel()
        await azc.async_close()

    return list(bulbs.values())


async def discover(
    timeout: int = 5,
    methods: list[str] | None = None,
    address: str = "255.255.255.255",
) -> list[DiscoveredBulb]:
    """Discover WiZ devices using all available methods.

    Combines UDP broadcast and mDNS discovery, deduplicating by MAC address.

    Args:
        timeout: How long to listen per method (seconds).
        methods: Discovery methods to use. Default: ["broadcast", "mdns"].
        address: Broadcast address for UDP discovery.

    Returns:
        Deduplicated list of DiscoveredBulb.
    """
    if methods is None:
        methods = ["broadcast", "mdns"]

    tasks = []
    if "broadcast" in methods:
        tasks.append(find_wizlights(timeout=timeout, address=address))
    if "mdns" in methods:
        tasks.append(discover_mdns(timeout=timeout))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    seen: dict[str, DiscoveredBulb] = {}
    for result in results:
        if isinstance(result, list):
            for bulb in result:
                if bulb.mac_address not in seen:
                    seen[bulb.mac_address] = bulb
        elif isinstance(result, Exception):
            _LOGGER.debug("Discovery method failed: %s", result)

    return list(seen.values())
