"""Tests for color space conversions."""

from wizlight.color import (
    hs2rgbcw,
    hs_to_rgbcw,
    kelvin_to_mired,
    kelvin_to_percent,
    mired_to_kelvin,
    percent_to_kelvin,
    rgb2rgbcw,
    rgb_to_rgbcw,
    rgbcw2hs,
    rgbcw_to_hs,
    rgbcw_to_rgb,
)


class TestRGBtoRGBCW:
    def test_pure_red(self):
        r, g, b, cw, ww = rgb_to_rgbcw(255, 0, 0)
        assert r > 0
        assert g == 0
        assert b == 0

    def test_black(self):
        assert rgb_to_rgbcw(0, 0, 0) == (0, 0, 0, 0, 0)

    def test_white(self):
        r, g, b, cw, ww = rgb_to_rgbcw(255, 255, 255)
        # White should produce mostly white channels
        assert cw > 0 or ww > 0


class TestRGBCWtoRGB:
    def test_pure_color(self):
        rgb = rgbcw_to_rgb(255, 0, 0, 0, 0)
        assert rgb == (255, 0, 0)

    def test_with_white(self):
        rgb = rgbcw_to_rgb(0, 0, 0, 128, 128)
        assert rgb[0] == rgb[1] == rgb[2] == 128


class TestHStoRGBCW:
    def test_red(self):
        result = hs_to_rgbcw(0, 100)
        assert result[0] > 0  # Red channel

    def test_alias(self):
        assert hs2rgbcw(0, 100) == hs_to_rgbcw(0, 100)

    def test_rgb_alias(self):
        assert rgb2rgbcw(255, 0, 0) == rgb_to_rgbcw(255, 0, 0)

    def test_hs_alias(self):
        assert rgbcw2hs(255, 0, 0, 0, 0) == rgbcw_to_hs(255, 0, 0, 0, 0)


class TestKelvinMired:
    def test_kelvin_to_mired(self):
        assert kelvin_to_mired(4000) == 250
        assert kelvin_to_mired(6500) == 154

    def test_mired_to_kelvin(self):
        assert mired_to_kelvin(250) == 4000
        assert mired_to_kelvin(154) == 6494  # Rounding

    def test_zero_handling(self):
        assert kelvin_to_mired(0) == 0
        assert mired_to_kelvin(0) == 0


class TestKelvinPercent:
    def test_min_is_zero(self):
        assert kelvin_to_percent(2200, 2200, 6500) == 0

    def test_max_is_100(self):
        assert kelvin_to_percent(6500, 2200, 6500) == 100

    def test_mid_is_50(self):
        mid = (2200 + 6500) // 2
        pct = kelvin_to_percent(mid, 2200, 6500)
        assert 45 <= pct <= 55  # Approximate due to rounding

    def test_percent_to_kelvin_roundtrip(self):
        assert percent_to_kelvin(0, 2200, 6500) == 2200
        assert percent_to_kelvin(100, 2200, 6500) == 6500
