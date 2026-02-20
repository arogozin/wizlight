"""Color space conversions for WiZ RGBCW devices.

WiZ bulbs use a 5-channel color model: Red, Green, Blue, Cold White, Warm White.
This module converts between standard color spaces (RGB, HS, CT) and the RGBCW
representation used by the hardware.

The conversion uses a trapezoid mapping to handle the gamut constraints of
mixed RGB + white LED systems.
"""

from __future__ import annotations

import colorsys
import math


def rgb_to_rgbcw(
    r: int, g: int, b: int, brightness: int = 255
) -> tuple[int, int, int, int, int]:
    """Convert RGB to RGBCW (Red, Green, Blue, Cold White, Warm White).

    Args:
        r, g, b: RGB values (0-255)
        brightness: Target brightness (0-255)

    Returns:
        Tuple of (r, g, b, cold_white, warm_white), each 0-255.
    """
    if r == 0 and g == 0 and b == 0:
        return (0, 0, 0, 0, 0)

    # Calculate the white component
    w_min = min(r, g, b)

    # Remove white component from RGB
    r_out = r - w_min
    g_out = g - w_min
    b_out = b - w_min

    # Split white into warm and cold (50/50 for pure white)
    warm_white = w_min
    cold_white = w_min

    # Scale to brightness
    max_val = max(r_out, g_out, b_out, warm_white, cold_white, 1)
    scale = brightness / max_val

    return (
        min(255, int(r_out * scale)),
        min(255, int(g_out * scale)),
        min(255, int(b_out * scale)),
        min(255, int(cold_white * scale)),
        min(255, int(warm_white * scale)),
    )


def rgbcw_to_rgb(
    r: int, g: int, b: int, cold_white: int, warm_white: int
) -> tuple[int, int, int]:
    """Convert RGBCW to RGB.

    Args:
        r, g, b: RGB channels (0-255)
        cold_white, warm_white: White channels (0-255)

    Returns:
        Tuple of (r, g, b), each 0-255.
    """
    white = (cold_white + warm_white) // 2
    return (
        min(255, r + white),
        min(255, g + white),
        min(255, b + white),
    )


def hs_to_rgbcw(
    hue: float, saturation: float, brightness: int = 255
) -> tuple[int, int, int, int, int]:
    """Convert Hue/Saturation to RGBCW.

    Args:
        hue: Hue angle (0-360)
        saturation: Saturation percentage (0-100)
        brightness: Target brightness (0-255)

    Returns:
        Tuple of (r, g, b, cold_white, warm_white), each 0-255.
    """
    # Normalize inputs
    h = (hue % 360) / 360.0
    s = max(0.0, min(100.0, saturation)) / 100.0

    # Convert HS to RGB
    r_f, g_f, b_f = colorsys.hsv_to_rgb(h, s, 1.0)
    r = int(r_f * 255)
    g = int(g_f * 255)
    b = int(b_f * 255)

    return rgb_to_rgbcw(r, g, b, brightness)


def rgbcw_to_hs(
    r: int, g: int, b: int, cold_white: int, warm_white: int
) -> tuple[float, float]:
    """Convert RGBCW to Hue/Saturation.

    Args:
        r, g, b: RGB channels (0-255)
        cold_white, warm_white: White channels (0-255)

    Returns:
        Tuple of (hue 0-360, saturation 0-100).
    """
    # Add white back to RGB
    rgb = rgbcw_to_rgb(r, g, b, cold_white, warm_white)
    r_f = rgb[0] / 255.0
    g_f = rgb[1] / 255.0
    b_f = rgb[2] / 255.0

    h, s, _ = colorsys.rgb_to_hsv(r_f, g_f, b_f)
    return (round(h * 360, 2), round(s * 100, 2))


def kelvin_to_mired(kelvin: int) -> int:
    """Convert color temperature from Kelvin to Mired (micro reciprocal degrees)."""
    if kelvin <= 0:
        return 0
    return round(1_000_000 / kelvin)


def mired_to_kelvin(mired: int) -> int:
    """Convert color temperature from Mired to Kelvin."""
    if mired <= 0:
        return 0
    return round(1_000_000 / mired)


def kelvin_to_percent(kelvin: int, min_k: int = 2200, max_k: int = 6500) -> int:
    """Convert Kelvin to a percentage within a range.

    Args:
        kelvin: Color temperature in Kelvin
        min_k: Minimum Kelvin (warm end)
        max_k: Maximum Kelvin (cool end)

    Returns:
        Percentage (0-100) where 0 = warmest, 100 = coolest.
    """
    if max_k <= min_k:
        return 0
    clamped = max(min_k, min(max_k, kelvin))
    return round((clamped - min_k) / (max_k - min_k) * 100)


def percent_to_kelvin(percent: int, min_k: int = 2200, max_k: int = 6500) -> int:
    """Convert a percentage to Kelvin within a range."""
    clamped = max(0, min(100, percent))
    return round(min_k + (max_k - min_k) * clamped / 100)


def xy_to_rgb(x: float, y: float, brightness: int = 255) -> tuple[int, int, int]:
    """Convert CIE xy chromaticity coordinates to RGB.

    Uses the Wide RGB D65 conversion matrix.
    """
    if y == 0:
        return (0, 0, 0)

    z = 1.0 - x - y
    Y = brightness / 255.0  # noqa: N806
    X = (Y / y) * x  # noqa: N806
    Z = (Y / y) * z  # noqa: N806

    # Wide RGB D65 conversion
    r = X * 1.656492 - Y * 0.354851 - Z * 0.255038
    g = -X * 0.707196 + Y * 1.655397 + Z * 0.036152
    b = X * 0.051713 - Y * 0.121364 + Z * 1.011530

    # Apply gamma correction
    def gamma(v: float) -> float:
        if v <= 0.0031308:
            return 12.92 * v
        return (1.0 + 0.055) * math.pow(v, 1.0 / 2.4) - 0.055

    r = gamma(max(0, r))
    g = gamma(max(0, g))
    b = gamma(max(0, b))

    # Scale to 0-255
    max_val = max(r, g, b, 1e-10)
    return (
        min(255, int(r / max_val * 255)),
        min(255, int(g / max_val * 255)),
        min(255, int(b / max_val * 255)),
    )


# Short-form aliases
hs2rgbcw = hs_to_rgbcw
rgb2rgbcw = rgb_to_rgbcw
rgbcw2hs = rgbcw_to_hs
