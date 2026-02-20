"""WiZ device database and type detection.

Maps known module names to device capabilities. WiZ bulbs report module names
like 'ESP01_SHRGB3_01ABI' which encode hardware type. This module parses those
names to determine device class, features, and color temperature ranges.
"""

from __future__ import annotations

from wizlight.models import BulbClass, BulbType, Features, KelvinRange

# Known module name patterns and their configurations.
# Keys are substrings matched against the module name.
# Order matters — first match wins.
_MODULE_PATTERNS: list[tuple[str, BulbClass, Features, KelvinRange | None]] = [
    # Fan devices
    (
        "FANDIM",
        BulbClass.FANDIM,
        Features(
            color=False,
            brightness=True,
            color_temp=False,
            effect=True,
            fan=True,
            fan_reverse=True,
            fan_breeze_mode=True,
        ),
        None,
    ),
    # Socket / smart plug
    (
        "SOCKET",
        BulbClass.SOCKET,
        Features(
            color=False,
            brightness=False,
            color_temp=False,
            effect=False,
        ),
        None,
    ),
    # RGB + warm white + cold white (full spectrum)
    (
        "RGBWW",
        BulbClass.RGB,
        Features(color=True, brightness=True, color_temp=True, effect=True),
        KelvinRange(2200, 6500),
    ),
    # RGB + cold white
    (
        "RGBW",
        BulbClass.RGB,
        Features(color=True, brightness=True, color_temp=True, effect=True),
        KelvinRange(2200, 6500),
    ),
    # RGB only (no white channels)
    (
        "RGB",
        BulbClass.RGB,
        Features(color=True, brightness=True, color_temp=False, effect=True),
        None,
    ),
    # Tunable white (warm ↔ cool)
    (
        "TW",
        BulbClass.TW,
        Features(color=False, brightness=True, color_temp=True, effect=True),
        KelvinRange(2700, 6500),
    ),
    # Dimmable white
    (
        "DW",
        BulbClass.DW,
        Features(color=False, brightness=True, color_temp=False, effect=True),
        None,
    ),
    # Single head tunable white
    (
        "SHTW",
        BulbClass.TW,
        Features(color=False, brightness=True, color_temp=True, effect=True),
        KelvinRange(2700, 6500),
    ),
    # Dual head tunable white
    (
        "DHTW",
        BulbClass.TW,
        Features(color=False, brightness=True, color_temp=True, effect=True),
        KelvinRange(2700, 6500),
    ),
    # Single head RGB
    (
        "SHRGB",
        BulbClass.RGB,
        Features(color=True, brightness=True, color_temp=True, effect=True),
        KelvinRange(2200, 6500),
    ),
    # Dual head RGB
    (
        "DHRGB",
        BulbClass.RGB,
        Features(color=True, brightness=True, color_temp=True, effect=True),
        KelvinRange(2200, 6500),
    ),
]

# Specific known module names with exact kelvin ranges
_KNOWN_MODULES: dict[str, tuple[BulbClass, KelvinRange | None]] = {
    "ESP01_SHRGB1C_31": (BulbClass.RGB, KelvinRange(2200, 6500)),
    "ESP01_SHRGB3_01ABI": (BulbClass.RGB, KelvinRange(2200, 6500)),
    "ESP01_SHDW1_31": (BulbClass.DW, None),
    "ESP01_SHTW1C_31": (BulbClass.TW, KelvinRange(2700, 6500)),
    "ESP03_SHRGB1C_01": (BulbClass.RGB, KelvinRange(2200, 6500)),
    "ESP03_SHRGB1W_01ABI": (BulbClass.RGB, KelvinRange(2200, 6500)),
    "ESP03_SHRGBP_31ABI": (BulbClass.RGB, KelvinRange(2200, 6500)),
    "ESP06_SHDW1_01": (BulbClass.DW, None),
    "ESP06_SHDW9_01": (BulbClass.DW, None),
    "ESP06_SHTW1_01": (BulbClass.TW, KelvinRange(2700, 6500)),
    "ESP06_SHTW9_01": (BulbClass.TW, KelvinRange(2700, 6500)),
    "ESP14_SHRGB1C_01ABI": (BulbClass.RGB, KelvinRange(2200, 6500)),
    "ESP15_SHRGB1C_01ABI": (BulbClass.RGB, KelvinRange(2200, 6500)),
    "ESP17_SHRGB9W_01ABI": (BulbClass.RGB, KelvinRange(2200, 6500)),
    "ESP20_SHRGB9W_01ABI": (BulbClass.RGB, KelvinRange(2200, 6500)),
    "ESP21_SHTW9_01": (BulbClass.TW, KelvinRange(2700, 6500)),
    "ESP56_SHTW11_01": (BulbClass.TW, KelvinRange(2700, 6500)),
}


def detect_bulb_type(module_name: str, white_range: dict | None = None) -> BulbType:
    """Detect bulb capabilities from its module name.

    Args:
        module_name: The module name reported by the device (e.g. 'ESP01_SHRGB3_01ABI')
        white_range: Optional dict with 'whiteRange' containing min/max kelvin.

    Returns:
        BulbType with detected capabilities.
    """
    name_upper = module_name.upper()

    # Try exact match first
    if module_name in _KNOWN_MODULES:
        bulb_class, kelvin = _KNOWN_MODULES[module_name]
        # Override kelvin range from device if provided
        if white_range and "min" in white_range and "max" in white_range:
            kelvin = KelvinRange(white_range["min"], white_range["max"])
        features = _features_for_class(bulb_class)
        return BulbType(
            bulb_type=bulb_class,
            name=module_name,
            features=features,
            kelvin_range=kelvin,
        )

    # Try pattern matching
    for pattern, bulb_class, features, kelvin in _MODULE_PATTERNS:
        if pattern in name_upper:
            # Override kelvin range from device if provided
            if white_range and "min" in white_range and "max" in white_range:
                kelvin = KelvinRange(white_range["min"], white_range["max"])
            return BulbType(
                bulb_type=bulb_class,
                name=module_name,
                features=Features(
                    color=features.color,
                    brightness=features.brightness,
                    color_temp=features.color_temp,
                    effect=features.effect,
                    fan=features.fan,
                    fan_reverse=features.fan_reverse,
                    fan_breeze_mode=features.fan_breeze_mode,
                ),
                kelvin_range=kelvin,
            )

    # Unknown module — default to RGB with full features
    return BulbType(
        bulb_type=BulbClass.RGB,
        name=module_name,
        features=Features(color=True, brightness=True, color_temp=True, effect=True),
        kelvin_range=KelvinRange(2200, 6500),
    )


def _features_for_class(bulb_class: BulbClass) -> Features:
    """Get default features for a bulb class."""
    match bulb_class:
        case BulbClass.RGB:
            return Features(color=True, brightness=True, color_temp=True, effect=True)
        case BulbClass.TW:
            return Features(color=False, brightness=True, color_temp=True, effect=True)
        case BulbClass.DW:
            return Features(color=False, brightness=True, color_temp=False, effect=True)
        case BulbClass.SOCKET:
            return Features(color=False, brightness=False, color_temp=False, effect=False)
        case BulbClass.FANDIM:
            return Features(
                color=False,
                brightness=True,
                color_temp=False,
                effect=True,
                fan=True,
                fan_reverse=True,
                fan_breeze_mode=True,
            )
