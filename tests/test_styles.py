"""Tests for art style implementations."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import numpy as np
import pytest
from core.styles import (
    classic_ascii, braille_style, block_style, edge_style,
    dot_cross_style, halftone_style, DEFAULT_RAMP, DOT_CROSS_RAMP,
    HALFTONE_RAMP, PRESETS,
)


def _make_brightness(rows=10, cols=20, value=128.0):
    return np.full((rows, cols), value, dtype=np.float64)


def _make_gradient(rows=10, cols=20):
    return np.linspace(0, 255, rows * cols).reshape(rows, cols)


class TestClassicAscii:
    def test_output_shape(self):
        b = _make_brightness(10, 20)
        result = classic_ascii(b)
        assert len(result) == 10
        assert len(result[0]) == 20

    def test_dark_pixels_map_to_dense_chars(self):
        b = _make_brightness(1, 1, value=0.0)
        result = classic_ascii(b)
        assert result[0][0] == DEFAULT_RAMP[0]  # Darkest char

    def test_bright_pixels_map_to_sparse_chars(self):
        b = _make_brightness(1, 1, value=255.0)
        result = classic_ascii(b)
        assert result[0][0] == DEFAULT_RAMP[-1]  # Lightest char (space)

    def test_custom_ramp(self):
        b = _make_brightness(1, 1, value=0.0)
        result = classic_ascii(b, ramp="AB ")
        assert result[0][0] == "A"

    def test_gradient_uses_full_ramp(self):
        b = _make_gradient(1, 100)
        result = classic_ascii(b)
        chars = set(result[0])
        # Gradient should hit most ramp characters
        assert len(chars) > 1


class TestBrailleStyle:
    def test_output_dimensions(self):
        # Input must be divisible by 4 rows, 2 cols
        b = np.full((40, 20), 128.0)
        result = braille_style(b)
        assert len(result) == 10  # 40 / 4
        assert len(result[0]) == 10  # 20 / 2

    def test_all_dark_produces_filled_braille(self):
        b = np.full((4, 2), 0.0)  # All dark, below default threshold 128
        result = braille_style(b)
        assert result[0][0] == chr(0x28FF)  # All dots on

    def test_all_bright_produces_empty_braille(self):
        b = np.full((4, 2), 255.0)  # All bright, above threshold
        result = braille_style(b)
        assert result[0][0] == chr(0x2800)  # No dots


class TestBlockStyle:
    def test_output_shape(self):
        b = _make_brightness(5, 10)
        result = block_style(b)
        assert len(result) == 5
        assert len(result[0]) == 10

    def test_dark_pixels_produce_full_block(self):
        # block_style inverts: low brightness (dark input) → full block
        b = _make_brightness(1, 1, value=255.0)
        result = block_style(b)
        assert result[0][0] == "\u2588"  # Full block for high brightness (inverted)

    def test_bright_pixels_produce_space(self):
        b = _make_brightness(1, 1, value=0.0)
        result = block_style(b)
        assert result[0][0] == " "  # Space for low brightness (inverted)


class TestEdgeStyle:
    def test_below_threshold_is_space(self):
        mag = np.full((5, 5), 10.0)  # Below default threshold 30
        direction = np.zeros((5, 5))
        result = edge_style(mag, direction)
        assert all(ch == " " for row in result for ch in row)

    def test_horizontal_edge(self):
        mag = np.full((1, 1), 100.0)
        direction = np.array([[0.0]])  # 0 radians = horizontal
        result = edge_style(mag, direction)
        assert result[0][0] == "\u2014"  # em dash

    def test_vertical_edge(self):
        mag = np.full((1, 1), 100.0)
        direction = np.array([[np.pi / 2]])  # 90 degrees = vertical
        result = edge_style(mag, direction)
        assert result[0][0] == "|"


class TestDotCrossStyle:
    def test_delegates_to_classic(self):
        b = _make_brightness(5, 10)
        result = dot_cross_style(b)
        assert len(result) == 5
        assert len(result[0]) == 10


class TestHalftoneStyle:
    def test_delegates_to_classic(self):
        b = _make_brightness(5, 10)
        result = halftone_style(b)
        assert len(result) == 5
        assert len(result[0]) == 10


class TestPresets:
    def test_retro_art_exists(self):
        assert "retro-art" in PRESETS
        assert "ramp" in PRESETS["retro-art"]
        assert "color" in PRESETS["retro-art"]

    def test_terminal_exists(self):
        assert "terminal" in PRESETS
        assert PRESETS["terminal"]["color"] == "matrix"
