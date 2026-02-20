"""Scene registry re-exports.

Convenience module that re-exports scene utilities from wizlight.effects.
"""

from wizlight.effects import (
    SCENES,
    SCENES_DW,
    SCENES_RGB,
    SCENES_TW,
    SceneClass,
    get_id_from_scene_name,
    get_scene_name,
    get_scenes_for_bulb_type,
)

__all__ = [
    "SCENES",
    "SCENES_DW",
    "SCENES_RGB",
    "SCENES_TW",
    "SceneClass",
    "get_id_from_scene_name",
    "get_scene_name",
    "get_scenes_for_bulb_type",
]
