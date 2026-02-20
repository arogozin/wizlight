"""Tests for data models."""

from dataclasses import asdict

from wizlight.models import (
    BulbClass,
    BulbType,
    DiscoveredBulb,
    Features,
    KelvinRange,
)


class TestFeatures:
    def test_defaults(self):
        f = Features()
        assert f.color is False
        assert f.brightness is True
        assert f.color_temp is False
        assert f.effect is False
        assert f.fan is False

    def test_compat_aliases(self):
        f = Features(color_temp=True)
        assert f.colorTemp is True
        assert f.color_tmp is True

    def test_dual_head(self):
        f = Features(dual_head=True)
        assert f.dual_head is True


class TestBulbType:
    def test_from_module_name_rgb(self):
        bt = BulbType.from_module_name("ESP01_SHRGB3_01ABI")
        assert bt.bulb_type == BulbClass.RGB
        assert bt.features.color is True
        assert bt.features.brightness is True

    def test_from_module_name_tw(self):
        bt = BulbType.from_module_name("ESP06_SHTW1_01")
        assert bt.bulb_type == BulbClass.TW
        assert bt.features.color is False
        assert bt.features.color_temp is True

    def test_from_module_name_socket(self):
        bt = BulbType.from_module_name("ESP_SOCKET_01")
        assert bt.bulb_type == BulbClass.SOCKET
        assert bt.features.brightness is False

    def test_from_data_alias(self):
        bt = BulbType.from_data("ESP01_SHRGB3_01ABI")
        assert bt.bulb_type == BulbClass.RGB

    def test_white_range_override(self):
        bt = BulbType.from_module_name("ESP01_SHRGB3_01ABI", {"min": 2700, "max": 5000})
        assert bt.kelvin_range is not None
        assert bt.kelvin_range.min == 2700
        assert bt.kelvin_range.max == 5000


class TestDiscoveredBulb:
    def test_asdict(self):
        bulb = DiscoveredBulb(ip_address="192.168.1.100", mac_address="aabbcc")
        d = asdict(bulb)
        assert d == {"ip_address": "192.168.1.100", "mac_address": "aabbcc"}


class TestKelvinRange:
    def test_defaults(self):
        kr = KelvinRange()
        assert kr.min == 2200
        assert kr.max == 6500
