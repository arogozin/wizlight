"""Command-line interface for wizlight.

Provides commands for discovering and controlling WiZ devices from the terminal.

Usage:
    wizlight discover
    wizlight state 192.168.1.100
    wizlight on 192.168.1.100 --scene Fireplace --brightness 200
    wizlight off 192.168.1.100
    wizlight effects
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any


def main() -> None:
    """CLI entry point."""
    try:
        import click
    except ImportError:
        print("CLI requires 'click'. Install with: pip install wizlight[cli]")
        sys.exit(1)

    _build_cli(click)()


def _build_cli(click: Any) -> Any:
    """Build the Click CLI app."""

    @click.group()
    @click.version_option()
    def cli() -> None:
        """wizlight — Control WiZ smart lights from the command line."""

    @cli.command()
    @click.option("--timeout", default=5, help="Discovery timeout in seconds.")
    @click.option("--address", default="255.255.255.255", help="Broadcast address.")
    @click.option("--json-output", "as_json", is_flag=True, help="Output as JSON.")
    def discover(timeout: int, address: str, as_json: bool) -> None:
        """Discover WiZ devices on the local network."""
        from wizlight.discovery import find_wizlights

        bulbs = asyncio.run(find_wizlights(timeout=timeout, address=address))

        if as_json:
            from dataclasses import asdict

            print(json.dumps([asdict(b) for b in bulbs], indent=2))
        else:
            if not bulbs:
                print("No WiZ devices found.")
                return
            print(f"Found {len(bulbs)} device(s):\n")
            for b in bulbs:
                print(f"  {b.ip_address}  ({b.mac_address})")

    @cli.command()
    @click.argument("ip")
    @click.option("--json-output", "as_json", is_flag=True, help="Output as JSON.")
    def state(ip: str, as_json: bool) -> None:
        """Get the current state of a WiZ device."""
        from wizlight.bulb import wizlight as WizBulb

        async def _run() -> None:
            async with WizBulb(ip) as bulb:
                pilot = await bulb.updateState()
                bulbtype = await bulb.get_bulbtype()

                if as_json:
                    print(json.dumps({
                        "ip": ip,
                        "mac": bulb.mac,
                        "power": pilot.get_power(),
                        "brightness": pilot.get_brightness(),
                        "colortemp": pilot.get_colortemp(),
                        "rgb": pilot.get_rgb(),
                        "scene_id": pilot.get_scene_id(),
                        "scene_name": pilot.get_scene_name(),
                        "speed": pilot.get_speed(),
                        "rssi": pilot.get_rssi(),
                        "module": bulbtype.name,
                        "fw_version": bulbtype.fw_version,
                        "type": bulbtype.bulb_type.value,
                    }, indent=2))
                else:
                    on_off = "ON" if pilot.get_power() else "OFF"
                    print(f"  Device:     {ip} ({bulb.mac})")
                    print(f"  Module:     {bulbtype.name}")
                    print(f"  Firmware:   {bulbtype.fw_version}")
                    print(f"  Type:       {bulbtype.bulb_type.value}")
                    print(f"  Power:      {on_off}")
                    if pilot.get_brightness() is not None:
                        print(f"  Brightness: {pilot.get_brightness()}")
                    if pilot.get_colortemp() is not None:
                        print(f"  Color Temp: {pilot.get_colortemp()}K")
                    if pilot.get_rgb() is not None:
                        print(f"  RGB:        {pilot.get_rgb()}")
                    if pilot.get_scene_name() is not None:
                        print(f"  Scene:      {pilot.get_scene_name()} (ID {pilot.get_scene_id()})")
                    if pilot.get_rssi() is not None:
                        print(f"  RSSI:       {pilot.get_rssi()} dBm")

        asyncio.run(_run())

    @cli.command()
    @click.argument("ip")
    @click.option("--scene", help="Scene name or ID.")
    @click.option("--brightness", type=int, help="Brightness (10-255).")
    @click.option("--colortemp", type=int, help="Color temperature in Kelvin.")
    @click.option("--rgb", nargs=3, type=int, help="RGB color (3 values 0-255).")
    @click.option("--speed", type=int, help="Effect speed (1-200).")
    def on(
        ip: str,
        scene: str | None,
        brightness: int | None,
        colortemp: int | None,
        rgb: tuple[int, int, int] | None,
        speed: int | None,
    ) -> None:
        """Turn on a WiZ device with optional parameters."""
        from wizlight.bulb import wizlight as WizBulb
        from wizlight.pilot import PilotBuilder

        # Resolve scene by name or int
        scene_val: int | str | None = scene
        if scene is not None:
            try:
                scene_val = int(scene)
            except ValueError:
                scene_val = scene

        kwargs: dict[str, Any] = {}
        if scene_val is not None:
            kwargs["scene"] = scene_val
        if brightness is not None:
            kwargs["brightness"] = brightness
        if colortemp is not None:
            kwargs["colortemp"] = colortemp
        if rgb is not None:
            kwargs["r"] = rgb[0]
            kwargs["g"] = rgb[1]
            kwargs["b"] = rgb[2]
        if speed is not None:
            kwargs["speed"] = speed

        pilot = PilotBuilder(**kwargs)

        async def _run() -> None:
            async with WizBulb(ip) as bulb:
                await bulb.turn_on(pilot)
                print(f"Turned on {ip}")

        asyncio.run(_run())

    @cli.command()
    @click.argument("ip")
    def off(ip: str) -> None:
        """Turn off a WiZ device."""
        from wizlight.bulb import wizlight as WizBulb

        async def _run() -> None:
            async with WizBulb(ip) as bulb:
                await bulb.turn_off()
                print(f"Turned off {ip}")

        asyncio.run(_run())

    @cli.command()
    @click.option("--bulb-type", default="RGB", help="Bulb type (RGB, TW, DW).")
    def effects(bulb_type: str) -> None:
        """List available effects/scenes."""
        from wizlight.effects import get_scenes_for_bulb_type

        scenes = get_scenes_for_bulb_type(bulb_type)
        if not scenes:
            print(f"No effects available for bulb type '{bulb_type}'.")
            return

        print(f"Effects for {bulb_type} bulbs:\n")
        for id_, name in sorted(scenes.items()):
            print(f"  {id_:4d}  {name}")

    @cli.command()
    @click.argument("ip")
    def info(ip: str) -> None:
        """Get detailed device information."""
        from wizlight.bulb import wizlight as WizBulb

        async def _run() -> None:
            async with WizBulb(ip) as bulb:
                config = await bulb.get_system_config()
                print(json.dumps(config, indent=2))

        asyncio.run(_run())

    return cli


if __name__ == "__main__":
    main()
