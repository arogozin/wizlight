"""Tests for PilotBuilder and PilotParser."""

import pytest

from wizlight.exceptions import WizLightInvalidParameter
from wizlight.pilot import PilotBuilder, PilotParser


class TestPilotBuilder:
    def test_basic_turn_on(self):
        pilot = PilotBuilder()
        params = pilot.to_dict()
        assert params["state"] is True

    def test_turn_off(self):
        pilot = PilotBuilder(state=False)
        params = pilot.to_dict()
        assert params["state"] is False
        assert "dimming" not in params

    def test_scene_by_name(self):
        pilot = PilotBuilder(scene="Club", brightness=200)
        params = pilot.to_dict()
        assert params["sceneId"] == 26
        assert params["dimming"] == 200

    def test_scene_by_id(self):
        pilot = PilotBuilder(scene=5)
        params = pilot.to_dict()
        assert params["sceneId"] == 5

    def test_invalid_scene_name(self):
        with pytest.raises(WizLightInvalidParameter):
            PilotBuilder(scene="NoSuchScene")

    def test_invalid_scene_id(self):
        with pytest.raises(WizLightInvalidParameter):
            PilotBuilder(scene=9999)

    def test_rgb(self):
        pilot = PilotBuilder(r=255, g=128, b=0, brightness=200)
        params = pilot.to_dict()
        assert params["r"] == 255
        assert params["g"] == 128
        assert params["b"] == 0
        assert params["dimming"] == 200

    def test_rgbw(self):
        pilot = PilotBuilder(rgbw=(100, 200, 50, 128))
        params = pilot.to_dict()
        assert params["r"] == 100
        assert params["g"] == 200
        assert params["b"] == 50
        assert params["w"] == 128

    def test_rgbww(self):
        pilot = PilotBuilder(rgbww=(100, 200, 50, 128, 64))
        params = pilot.to_dict()
        assert params["r"] == 100
        assert params["g"] == 200
        assert params["b"] == 50
        assert params["w"] == 128
        assert params["c"] == 64

    def test_colortemp(self):
        pilot = PilotBuilder(colortemp=3500, brightness=128)
        params = pilot.to_dict()
        assert params["temp"] == 3500
        assert params["dimming"] == 128

    def test_speed(self):
        pilot = PilotBuilder(scene="Party", speed=150)
        params = pilot.to_dict()
        assert params["speed"] == 150

    def test_brightness_clamp(self):
        pilot = PilotBuilder(brightness=5)  # Below min of 10
        params = pilot.to_dict()
        assert params["dimming"] == 10

    def test_pilot_params_alias(self):
        pilot = PilotBuilder(scene="Club")
        assert pilot.pilot_params == pilot.to_dict()


class TestPilotParser:
    def test_power_state(self):
        parser = PilotParser({"state": True})
        assert parser.get_state() is True

    def test_power_state_off(self):
        parser = PilotParser({"state": False})
        assert parser.get_state() is False

    def test_brightness(self):
        parser = PilotParser({"dimming": 128})
        assert parser.get_brightness() == 128

    def test_colortemp(self):
        parser = PilotParser({"temp": 4000})
        assert parser.get_colortemp() == 4000

    def test_rgb(self):
        parser = PilotParser({"r": 255, "g": 128, "b": 0})
        assert parser.get_rgb() == (255, 128, 0)

    def test_rgb_none_when_missing(self):
        parser = PilotParser({"r": 255})
        assert parser.get_rgb() is None

    def test_rgbw(self):
        parser = PilotParser({"r": 100, "g": 200, "b": 50, "w": 128})
        assert parser.get_rgbw() == (100, 200, 50, 128)

    def test_rgbww(self):
        parser = PilotParser({"r": 100, "g": 200, "b": 50, "w": 128, "c": 64})
        assert parser.get_rgbww() == (100, 200, 50, 128, 64)

    def test_scene_id(self):
        parser = PilotParser({"sceneId": 26})
        assert parser.get_scene_id() == 26

    def test_scene_name(self):
        parser = PilotParser({"sceneId": 26})
        assert parser.get_scene_name() == "Club"
        assert parser.get_scene() == "Club"  # alias

    def test_scene_id_zero_returns_none(self):
        parser = PilotParser({"sceneId": 0})
        assert parser.get_scene_id() is None

    def test_source(self):
        parser = PilotParser({"src": "pir"})
        assert parser.get_source() == "pir"

    def test_rssi(self):
        parser = PilotParser({"rssi": -60})
        assert parser.get_rssi() == -60

    def test_speed(self):
        parser = PilotParser({"speed": 100})
        assert parser.get_speed() == 100

    def test_power_watts(self):
        parser = PilotParser({"w": 8.5})
        assert parser.get_power() == 8.5

    def test_power_watts_none(self):
        parser = PilotParser({})
        assert parser.get_power() is None

    def test_fan_state(self):
        parser = PilotParser({"fanState": 1, "fanSpeed": 3, "fanMode": 2, "fanRevrs": 0})
        assert parser.get_fan_state() == 1
        assert parser.get_fan_speed() == 3
        assert parser.get_fan_mode() == 2
        assert parser.get_fan_reverse() == 0

    def test_pilot_result_dict(self):
        data = {"state": True, "dimming": 100}
        parser = PilotParser(data)
        assert parser.pilotResult == data
