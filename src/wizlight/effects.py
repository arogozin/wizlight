"""Complete WiZ effect/scene registry.

Every WiZ scene is identified by an integer ID. The bulb firmware uses these IDs
in setPilot/getPilot commands. This module maps all known scene IDs to their
human-readable names and provides lookup helpers.
"""

from __future__ import annotations

from enum import Enum

# Complete scene mapping — all 36 standard scenes + Rhythm
SCENES: dict[int, str] = {
    1: "Ocean",
    2: "Romance",
    3: "Sunset",
    4: "Party",
    5: "Fireplace",
    6: "Cozy",
    7: "Forest",
    8: "Pastel colors",
    9: "Wake-up",
    10: "Bedtime",
    11: "Warm white",
    12: "Daylight",
    13: "Cool white",
    14: "Night light",
    15: "Focus",
    16: "Relax",
    17: "True colors",
    18: "TV time",
    19: "Plantgrowth",
    20: "Spring",
    21: "Summer",
    22: "Fall",
    23: "Deep dive",
    24: "Jungle",
    25: "Mojito",
    26: "Club",
    27: "Christmas",
    28: "Halloween",
    29: "Candlelight",
    30: "Golden white",
    31: "Pulse",
    32: "Steampunk",
    33: "Diwali",
    34: "White",
    35: "Alarm",
    36: "Snowy sky",
    1000: "Rhythm",
}

# Reverse lookup: lowercase name → ID
_NAME_TO_ID: dict[str, int] = {name.lower(): id_ for id_, name in SCENES.items()}


class SceneClass(Enum):
    """Categories of scenes by type."""

    DYNAMIC = "dynamic"  # Animated color effects
    STATIC_WHITE = "static_white"  # Fixed white temperature
    MUSIC = "music"  # Music-reactive


# Scene classification
SCENE_CLASSES: dict[int, SceneClass] = {
    1: SceneClass.DYNAMIC,
    2: SceneClass.DYNAMIC,
    3: SceneClass.DYNAMIC,
    4: SceneClass.DYNAMIC,
    5: SceneClass.DYNAMIC,
    6: SceneClass.DYNAMIC,
    7: SceneClass.DYNAMIC,
    8: SceneClass.DYNAMIC,
    9: SceneClass.DYNAMIC,
    10: SceneClass.DYNAMIC,
    11: SceneClass.STATIC_WHITE,
    12: SceneClass.STATIC_WHITE,
    13: SceneClass.STATIC_WHITE,
    14: SceneClass.STATIC_WHITE,
    15: SceneClass.DYNAMIC,
    16: SceneClass.DYNAMIC,
    17: SceneClass.DYNAMIC,
    18: SceneClass.DYNAMIC,
    19: SceneClass.DYNAMIC,
    20: SceneClass.DYNAMIC,
    21: SceneClass.DYNAMIC,
    22: SceneClass.DYNAMIC,
    23: SceneClass.DYNAMIC,
    24: SceneClass.DYNAMIC,
    25: SceneClass.DYNAMIC,
    26: SceneClass.DYNAMIC,
    27: SceneClass.DYNAMIC,
    28: SceneClass.DYNAMIC,
    29: SceneClass.DYNAMIC,
    30: SceneClass.STATIC_WHITE,
    31: SceneClass.DYNAMIC,
    32: SceneClass.DYNAMIC,
    33: SceneClass.DYNAMIC,
    34: SceneClass.STATIC_WHITE,
    35: SceneClass.DYNAMIC,
    36: SceneClass.DYNAMIC,
    1000: SceneClass.MUSIC,
}

# Scenes available per bulb class (by ID)
# RGB bulbs support all scenes
SCENES_RGB: list[int] = list(range(1, 37)) + [1000]

# Tunable white bulbs only support white-temperature and some dynamic scenes
SCENES_TW: list[int] = [6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 30, 34, 35, 1000]

# Dimmable white bulbs support a minimal set
SCENES_DW: list[int] = [9, 10, 13, 14, 29, 30, 31, 32]


def get_id_from_scene_name(name: str) -> int | None:
    """Get scene ID from its name (case-insensitive).

    Returns None if the scene name is not recognized.
    """
    return _NAME_TO_ID.get(name.lower())


def get_scene_name(scene_id: int) -> str | None:
    """Get scene name from its ID.

    Returns None if the scene ID is not recognized.
    """
    return SCENES.get(scene_id)


def get_scenes_for_bulb_type(bulb_class: str) -> dict[int, str]:
    """Get available scenes for a given bulb class.

    Args:
        bulb_class: One of "RGB", "TW", "DW", "SOCKET", "FANDIM"

    Returns:
        Dict mapping scene ID → name for available scenes.
    """
    match bulb_class.upper():
        case "RGB" | "FANDIM":
            ids = SCENES_RGB
        case "TW":
            ids = SCENES_TW
        case "DW":
            ids = SCENES_DW
        case "SOCKET":
            return {}
        case _:
            ids = SCENES_RGB  # Default to full list
    return {id_: SCENES[id_] for id_ in ids if id_ in SCENES}
