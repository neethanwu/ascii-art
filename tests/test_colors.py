"""Tests for color mode implementations."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import numpy as np
import pytest
from core.colors import parse_hex_color, apply_color, NAMED_COLORS


class TestParseHexColor:
    def test_hex_with_hash(self):
        assert parse_hex_color("#ff6600") == (255, 102, 0)

    def test_hex_without_hash(self):
        assert parse_hex_color("ff6600") == (255, 102, 0)

    def test_named_color(self):
        assert parse_hex_color("coral") == (255, 127, 80)

    def test_named_color_with_hash(self):
        assert parse_hex_color("#coral") == (255, 127, 80)

    def test_named_color_case_insensitive(self):
        assert parse_hex_color("SkyBlue") == (135, 206, 235)

    def test_invalid_hex_raises(self):
        with pytest.raises(ValueError):
            parse_hex_color("xyz")

    def test_invalid_length_raises(self):
        with pytest.raises(ValueError):
            parse_hex_color("fff")

    def test_all_named_colors_resolve(self):
        for name, hex_val in NAMED_COLORS.items():
            r, g, b = parse_hex_color(name)
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255


class TestApplyColor:
    def _make_inputs(self, rows=5, cols=10):
        brightness = np.full((rows, cols), 200.0)
        colors = np.full((rows, cols, 3), 128, dtype=np.uint8)
        return brightness, colors

    def test_grayscale_dark(self):
        b, c = self._make_inputs()
        result = apply_color(b, c, mode="grayscale", background="dark")
        assert result.shape == (5, 10, 3)
        assert result[0, 0, 0] == 200  # Gray value matches brightness

    def test_grayscale_light(self):
        b, c = self._make_inputs()
        result = apply_color(b, c, mode="grayscale", background="light")
        assert result[0, 0, 0] == 55  # 255 - 200

    def test_full_color(self):
        b, c = self._make_inputs()
        result = apply_color(b, c, mode="full")
        np.testing.assert_array_equal(result, c)

    def test_matrix(self):
        b, c = self._make_inputs()
        result = apply_color(b, c, mode="matrix")
        assert result[0, 0, 0] == 0    # No red
        assert result[0, 0, 1] == 200  # Green = brightness
        assert result[0, 0, 2] == 0    # No blue

    def test_amber(self):
        b, c = self._make_inputs()
        result = apply_color(b, c, mode="amber")
        assert result[0, 0, 0] == 200        # Red = brightness
        assert result[0, 0, 1] == 120         # Green = brightness * 0.6
        assert result[0, 0, 2] == 0           # No blue

    def test_custom_color(self):
        b, c = self._make_inputs()
        result = apply_color(b, c, mode="custom", custom_color="#ff0000")
        assert result[0, 0, 0] > 0    # Has red
        assert result[0, 0, 1] == 0   # No green
        assert result[0, 0, 2] == 0   # No blue

    def test_output_dtype(self):
        b, c = self._make_inputs()
        result = apply_color(b, c, mode="grayscale")
        assert result.dtype == np.uint8
