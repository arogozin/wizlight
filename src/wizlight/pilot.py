"""PilotBuilder and PilotParser for WiZ device commands and state.

PilotBuilder constructs the 'params' dict for setPilot commands.
PilotParser extracts state from getPilot / syncPilot responses.
"""

from __future__ import annotations

from typing import Any

from wizlight.effects import SCENES, get_id_from_scene_name
from wizlight.exceptions import WizLightInvalidParameter


class PilotBuilder:
    """Build a setPilot command payload.

    Validates parameters and produces a dict suitable for the 'params' field
    of a setPilot JSON message.

    Usage:
        # Set to warm white at 50% brightness
        pilot = PilotBuilder(colortemp=3000, brightness=128)

        # Set to Fireplace effect at full brightness
        pilot = PilotBuilder(scene="Fireplace", brightness=255)

        # Set to specific RGB color
        pilot = PilotBuilder(r=255, g=0, b=128, brightness=200)

        # Turn off
        pilot = PilotBuilder(state=False)
    """

    def __init__(
        self,
        *,
        state: bool = True,
        brightness: int | None = None,
        r: int | None = None,
        g: int | None = None,
        b: int | None = None,
        rgbw: tuple[int, ...] | None = None,
        rgbww: tuple[int, ...] | None = None,
        colortemp: int | None = None,
        scene: int | str | None = None,
        speed: int | None = None,
        ratio: int | None = None,
        warm_white: int | None = None,
        cold_white: int | None = None,
    ) -> None:
        self._params: dict[str, Any] = {"state": state}

        if not state:
            return  # No other params needed for turn-off

        # Scene (by name or ID)
        if scene is not None:
            scene_id = self._resolve_scene(scene)
            self._params["sceneId"] = scene_id
        # RGBWW color (5 channels)
        elif rgbww is not None:
            self._set_rgbww(rgbww)
        # RGBW color (4 channels)
        elif rgbw is not None:
            self._set_rgbw(rgbw)
        elif r is not None or g is not None or b is not None:
            self._params["r"] = self._clamp(r or 0, 0, 255, "r")
            self._params["g"] = self._clamp(g or 0, 0, 255, "g")
            self._params["b"] = self._clamp(b or 0, 0, 255, "b")
            if warm_white is not None:
                self._params["w"] = self._clamp(warm_white, 0, 255, "warm_white")
            if cold_white is not None:
                self._params["c"] = self._clamp(cold_white, 0, 255, "cold_white")
        # Color temperature
        elif colortemp is not None:
            self._params["temp"] = self._clamp(colortemp, 1000, 10000, "colortemp")

        # Brightness (applies to any mode)
        if brightness is not None:
            self._params["dimming"] = self._clamp(brightness, 10, 255, "brightness")

        # Effect speed
        if speed is not None:
            self._params["speed"] = self._clamp(speed, 1, 200, "speed")

        # Dual-head ratio
        if ratio is not None:
            self._params["ratio"] = self._clamp(ratio, 0, 100, "ratio")

    def _resolve_scene(self, scene: int | str) -> int:
        """Resolve a scene name or ID to an integer ID."""
        if isinstance(scene, int):
            if scene not in SCENES:
                raise WizLightInvalidParameter(
                    f"Unknown scene ID {scene}. Valid IDs: {sorted(SCENES.keys())}"
                )
            return scene

        scene_id = get_id_from_scene_name(scene)
        if scene_id is None:
            raise WizLightInvalidParameter(
                f"Unknown scene name '{scene}'. Valid names: {sorted(SCENES.values())}"
            )
        return scene_id

    def _set_rgbw(self, rgbw: tuple[int, ...]) -> None:
        """Set RGBW from a 4-tuple (r, g, b, warm_white)."""
        if len(rgbw) < 3:
            raise WizLightInvalidParameter("rgbw must have at least 3 values (r, g, b)")

        self._params["r"] = self._clamp(rgbw[0], 0, 255, "r")
        self._params["g"] = self._clamp(rgbw[1], 0, 255, "g")
        self._params["b"] = self._clamp(rgbw[2], 0, 255, "b")
        if len(rgbw) > 3:
            self._params["w"] = self._clamp(rgbw[3], 0, 255, "warm_white")

    def _set_rgbww(self, rgbww: tuple[int, ...]) -> None:
        """Set RGBWW from a 5-tuple (r, g, b, warm_white, cold_white)."""
        if len(rgbww) < 3:
            raise WizLightInvalidParameter("rgbww must have at least 3 values (r, g, b)")

        self._params["r"] = self._clamp(rgbww[0], 0, 255, "r")
        self._params["g"] = self._clamp(rgbww[1], 0, 255, "g")
        self._params["b"] = self._clamp(rgbww[2], 0, 255, "b")
        if len(rgbww) > 3:
            self._params["w"] = self._clamp(rgbww[3], 0, 255, "warm_white")
        if len(rgbww) > 4:
            self._params["c"] = self._clamp(rgbww[4], 0, 255, "cold_white")

    @staticmethod
    def _clamp(value: int, min_val: int, max_val: int, name: str) -> int:
        """Clamp a value to a range, raising on invalid type."""
        if not isinstance(value, int):
            raise WizLightInvalidParameter(f"{name} must be an integer, got {type(value)}")
        return max(min_val, min(max_val, value))

    def to_dict(self) -> dict[str, Any]:
        """Return the params dict for a setPilot command."""
        return dict(self._params)

    @property
    def pilot_params(self) -> dict[str, Any]:
        """Alias for to_dict()."""
        return self.to_dict()


class PilotParser:
    """Parse state from a getPilot or syncPilot response.

    Extracts device state from the 'result' or 'params' dict of a WiZ response.

    Usage:
        parser = PilotParser(response_dict)
        brightness = parser.get_brightness()
        is_on = parser.get_power()
    """

    def __init__(self, result: dict[str, Any]) -> None:
        self._result = result

    def get_state(self) -> bool:
        """Get the on/off state."""
        return bool(self._result.get("state", False))

    def get_power(self) -> float | None:
        """Get power consumption in watts. Returns None if not available."""
        power = self._result.get("pc") or self._result.get("w")
        if power is not None:
            return float(power)
        return None

    def get_brightness(self) -> int | None:
        """Get brightness (0-255). Returns None if not available."""
        dimming = self._result.get("dimming")
        if dimming is not None:
            return int(dimming)
        return None

    def get_colortemp(self) -> int | None:
        """Get color temperature in Kelvin. Returns None if not in CT mode."""
        temp = self._result.get("temp")
        if temp is not None:
            return int(temp)
        return None

    def get_rgb(self) -> tuple[int, int, int] | None:
        """Get RGB color. Returns None if not in color mode."""
        r = self._result.get("r")
        g = self._result.get("g")
        b = self._result.get("b")
        if r is not None and g is not None and b is not None:
            return (int(r), int(g), int(b))
        return None

    def get_rgbww(self) -> tuple[int, int, int, int, int] | None:
        """Get RGBWW color (r, g, b, warm_white, cold_white).

        Returns None if not in color mode.
        """
        r = self._result.get("r")
        g = self._result.get("g")
        b = self._result.get("b")
        if r is None or g is None or b is None:
            return None

        w = self._result.get("w", 0)
        c = self._result.get("c", 0)
        return (int(r), int(g), int(b), int(w), int(c))

    def get_scene_id(self) -> int | None:
        """Get the active scene ID. Returns None if no scene is active."""
        scene_id = self._result.get("sceneId")
        if scene_id is not None and int(scene_id) != 0:
            return int(scene_id)
        return None

    def get_scene_name(self) -> str | None:
        """Get the active scene name. Returns None if no scene is active."""
        scene_id = self.get_scene_id()
        if scene_id is not None:
            return SCENES.get(scene_id)
        return None

    def get_source(self) -> str | None:
        """Get the data source identifier."""
        return self._result.get("src")

    def get_speed(self) -> int | None:
        """Get the effect speed. Returns None if not applicable."""
        speed = self._result.get("speed")
        if speed is not None:
            return int(speed)
        return None

    def get_ratio(self) -> int | None:
        """Get the dual-head ratio. Returns None if not applicable."""
        ratio = self._result.get("ratio")
        if ratio is not None:
            return int(ratio)
        return None

    def get_mac(self) -> str | None:
        """Get the device MAC address from the response."""
        return self._result.get("mac")

    def get_rssi(self) -> int | None:
        """Get the WiFi signal strength (RSSI)."""
        rssi = self._result.get("rssi")
        if rssi is not None:
            return int(rssi)
        return None

    def get_scene(self) -> str | None:
        """Get the active scene name. Alias for get_scene_name()."""
        return self.get_scene_name()

    def get_rgbw(self) -> tuple[int, int, int, int] | None:
        """Get RGBW color (r, g, b, warm_white).

        Returns None if not in color mode.
        """
        r = self._result.get("r")
        g = self._result.get("g")
        b = self._result.get("b")
        if r is None or g is None or b is None:
            return None

        w = self._result.get("w", 0)
        return (int(r), int(g), int(b), int(w))

    # --- Fan state methods ---

    def get_fan_state(self) -> int:
        """Get the fan on/off state (0=off, >0=on)."""
        return int(self._result.get("fanState", 0))

    def get_fan_speed(self) -> int:
        """Get the fan speed (1-6 typically)."""
        return int(self._result.get("fanSpeed", 0))

    def get_fan_mode(self) -> int:
        """Get the fan mode (1=normal, 2=breeze)."""
        return int(self._result.get("fanMode", 1))

    def get_fan_reverse(self) -> int:
        """Get the fan reverse state (0=forward, 1=reverse)."""
        return int(self._result.get("fanRevrs", 0))

    @property
    def pilotResult(self) -> dict[str, Any]:  # noqa: N802
        """Raw result dict."""
        return dict(self._result)
