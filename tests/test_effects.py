"""Tests for the effects/scenes registry."""

from wizlight.effects import (
    SCENES,
    SCENES_DW,
    SCENES_TW,
    get_id_from_scene_name,
    get_scene_name,
    get_scenes_for_bulb_type,
)


def test_all_36_scenes_plus_rhythm():
    """All 36 standard scenes + Rhythm should be registered."""
    assert len(SCENES) == 37
    assert 1000 in SCENES  # Rhythm


def test_club_is_present():
    """Club (ID 26) must be in the scene list."""
    assert 26 in SCENES
    assert SCENES[26] == "Club"


def test_snowy_sky_is_present():
    """Snowy sky (ID 36) must also be present."""
    assert 36 in SCENES
    assert SCENES[36] == "Snowy sky"


def test_get_id_from_scene_name():
    assert get_id_from_scene_name("Club") == 26
    assert get_id_from_scene_name("club") == 26
    assert get_id_from_scene_name("CLUB") == 26
    assert get_id_from_scene_name("Spring") == 20
    assert get_id_from_scene_name("Fireplace") == 5
    assert get_id_from_scene_name("Rhythm") == 1000
    assert get_id_from_scene_name("nonexistent") is None


def test_get_scene_name():
    assert get_scene_name(26) == "Club"
    assert get_scene_name(5) == "Fireplace"
    assert get_scene_name(1000) == "Rhythm"
    assert get_scene_name(9999) is None


def test_scenes_for_rgb():
    scenes = get_scenes_for_bulb_type("RGB")
    assert 26 in scenes  # Club
    assert 36 in scenes  # Snowy sky
    assert 1000 in scenes  # Rhythm
    assert len(scenes) == 37


def test_scenes_for_tw():
    scenes = get_scenes_for_bulb_type("TW")
    assert len(scenes) == len(SCENES_TW)
    # TW shouldn't have Club
    assert 26 not in scenes


def test_scenes_for_dw():
    scenes = get_scenes_for_bulb_type("DW")
    assert len(scenes) == len(SCENES_DW)


def test_scenes_for_socket():
    scenes = get_scenes_for_bulb_type("SOCKET")
    assert len(scenes) == 0


def test_scenes_for_fandim_same_as_rgb():
    scenes = get_scenes_for_bulb_type("FANDIM")
    assert len(scenes) == 37
