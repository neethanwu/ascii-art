"""Tests for dithering algorithms."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import numpy as np
import pytest
from core.dither import floyd_steinberg, bayer, atkinson, apply_dither


def _make_gradient(rows=20, cols=40):
    return np.linspace(0, 255, rows * cols).reshape(rows, cols).astype(np.float64)


class TestFloydSteinberg:
    def test_output_shape(self):
        img = _make_gradient()
        result = floyd_steinberg(img, levels=10)
        assert result.shape == img.shape

    def test_output_range(self):
        img = _make_gradient()
        result = floyd_steinberg(img, levels=10)
        assert result.min() >= 0
        assert result.max() <= 255

    def test_quantizes_to_levels(self):
        img = _make_gradient()
        result = floyd_steinberg(img, levels=4)
        unique = np.unique(result)
        assert len(unique) <= 4


class TestBayer:
    def test_output_shape(self):
        img = _make_gradient()
        result = bayer(img, levels=10)
        assert result.shape == img.shape

    def test_output_range(self):
        img = _make_gradient()
        result = bayer(img, levels=10)
        assert result.min() >= 0
        assert result.max() <= 255


class TestAtkinson:
    def test_output_shape(self):
        img = _make_gradient()
        result = atkinson(img, levels=10)
        assert result.shape == img.shape

    def test_output_range(self):
        img = _make_gradient()
        result = atkinson(img, levels=10)
        assert result.min() >= 0
        assert result.max() <= 255


class TestApplyDither:
    def test_none_returns_copy(self):
        img = _make_gradient()
        result = apply_dither(img, "none", levels=10)
        np.testing.assert_array_equal(result, img)

    def test_floyd_steinberg_dispatch(self):
        img = _make_gradient()
        result = apply_dither(img, "floyd-steinberg", levels=10)
        assert result.shape == img.shape

    def test_bayer_dispatch(self):
        img = _make_gradient()
        result = apply_dither(img, "bayer", levels=10)
        assert result.shape == img.shape

    def test_atkinson_dispatch(self):
        img = _make_gradient()
        result = apply_dither(img, "atkinson", levels=10)
        assert result.shape == img.shape

    def test_strength_parameter(self):
        img = _make_gradient()
        weak = apply_dither(img, "floyd-steinberg", levels=10, strength=0.1)
        strong = apply_dither(img, "floyd-steinberg", levels=10, strength=1.0)
        # Weaker dithering should produce results closer to original
        diff_weak = np.abs(weak - img).mean()
        diff_strong = np.abs(strong - img).mean()
        assert diff_weak <= diff_strong
