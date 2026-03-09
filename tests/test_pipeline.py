"""Tests for image processing pipeline."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import tempfile
import numpy as np
import pytest
from PIL import Image
from core.pipeline import load_image, process_image, crop_to_ratio


def _create_test_image(width=200, height=150, color=(128, 64, 32)):
    """Create a simple test image."""
    img = Image.new("RGB", (width, height), color)
    return img


def _save_temp_image(img, suffix=".png"):
    """Save image to a temp file and return path."""
    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    img.save(f.name)
    f.close()
    return f.name


class TestLoadImage:
    def test_loads_png(self):
        img = _create_test_image()
        path = _save_temp_image(img)
        try:
            result = load_image(path)
            assert result.size == (200, 150)
            assert result.mode == "RGB"
        finally:
            os.unlink(path)

    def test_loads_jpeg(self):
        img = _create_test_image()
        path = _save_temp_image(img, suffix=".jpg")
        try:
            result = load_image(path)
            assert result.mode == "RGB"
        finally:
            os.unlink(path)

    def test_converts_rgba_to_rgb(self):
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        path = _save_temp_image(img)
        try:
            result = load_image(path)
            assert result.mode == "RGB"
        finally:
            os.unlink(path)

    def test_invalid_path_raises(self):
        with pytest.raises(Exception):
            load_image("/nonexistent/path.png")


class TestProcessImage:
    def test_output_structure(self):
        img = _create_test_image()
        grid = process_image(img, cols=40)
        assert hasattr(grid, "brightness")
        assert hasattr(grid, "colors")
        assert grid.brightness.shape[1] == 40
        assert grid.colors.shape[1] == 40
        assert grid.colors.shape[2] == 3

    def test_different_column_widths(self):
        img = _create_test_image()
        for cols in [20, 40, 80, 120]:
            grid = process_image(img, cols=cols)
            assert grid.brightness.shape[1] == cols

    def test_invert_flips_brightness(self):
        img = _create_test_image(color=(0, 0, 0))  # Black image
        normal = process_image(img, cols=10)
        inverted = process_image(img, cols=10, invert=True)
        assert inverted.brightness.mean() > normal.brightness.mean()


class TestCropToRatio:
    def test_original_no_change(self):
        img = _create_test_image(200, 150)
        result = crop_to_ratio(img, "original")
        assert result.size == (200, 150)

    def test_square_crop(self):
        img = _create_test_image(200, 150)
        result = crop_to_ratio(img, "1:1")
        w, h = result.size
        assert abs(w - h) <= 1

    def test_widescreen_crop(self):
        img = _create_test_image(200, 200)
        result = crop_to_ratio(img, "16:9")
        w, h = result.size
        ratio = w / h
        assert abs(ratio - 16 / 9) < 0.1
