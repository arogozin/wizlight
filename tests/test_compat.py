"""Tests for API import paths.

Verifies that all public symbols are accessible from their expected modules.
"""


def test_main_imports():
    """Verify the main module exports the public API."""
    from wizlight import PilotBuilder, PilotParser, wizlight
    assert wizlight is not None
    assert PilotBuilder is not None
    assert PilotParser is not None


def test_bulb_imports():
    """Verify wizlight.bulb exports."""
    from wizlight.bulb import PIR_SOURCE
    assert PIR_SOURCE == "pir"


def test_bulblibrary_imports():
    """Verify wizlight.bulblibrary exports."""
    from wizlight.bulblibrary import BulbClass, BulbType, Features
    assert BulbType is not None
    assert BulbClass is not None
    assert Features is not None


def test_discovery_imports():
    """Verify wizlight.discovery exports."""
    from wizlight.discovery import DiscoveredBulb, find_wizlights
    assert find_wizlights is not None
    assert DiscoveredBulb is not None


def test_exceptions_imports():
    """Verify wizlight.exceptions exports."""
    from wizlight.exceptions import (
        WizLightConnectionError,
        WizLightNotKnownBulb,
        WizLightTimeOutError,
    )
    assert WizLightConnectionError is not None
    assert WizLightTimeOutError is not None
    assert WizLightNotKnownBulb is not None


def test_scenes_imports():
    """Verify wizlight.scenes exports."""
    from wizlight.scenes import get_id_from_scene_name
    assert get_id_from_scene_name("Club") == 26


def test_rgbcw_imports():
    """Verify wizlight.rgbcw exports."""
    from wizlight.rgbcw import hs2rgbcw, rgb2rgbcw
    assert hs2rgbcw is not None
    assert rgb2rgbcw is not None


def test_get_id_from_main_module():
    """Verify get_id_from_scene_name is accessible from main module."""
    from wizlight import get_id_from_scene_name
    assert get_id_from_scene_name("Club") == 26


def test_discovered_bulb_asdict():
    """Verify DiscoveredBulb supports dataclasses.asdict()."""
    from dataclasses import asdict

    from wizlight.discovery import DiscoveredBulb

    bulb = DiscoveredBulb(ip_address="192.168.1.1", mac_address="aabbcc")
    d = asdict(bulb)
    assert d["ip_address"] == "192.168.1.1"
    assert d["mac_address"] == "aabbcc"
