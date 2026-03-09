"""Tests for export formats and security."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import tempfile
import numpy as np
import pytest
from PIL import Image
from core.exporters import (
    sanitize_filename, make_output_path,
    export_txt, export_html, export_svg, export_png,
)


def _make_chars(rows=5, cols=10):
    return [["#"] * cols for _ in range(rows)]


def _make_colors(rows=5, cols=10):
    return np.full((rows, cols, 3), 200, dtype=np.uint8)


class TestSanitizeFilename:
    def test_strips_extension(self):
        assert sanitize_filename("photo.jpg") == "photo"

    def test_replaces_special_chars(self):
        assert sanitize_filename("my photo (1).jpg") == "my_photo_1"

    def test_collapses_underscores(self):
        assert sanitize_filename("a___b.txt") == "a_b"

    def test_empty_returns_output(self):
        assert sanitize_filename("...") == "output"


class TestMakeOutputPath:
    def test_custom_filename(self):
        path = make_output_path("input", "png", filename="custom.png")
        assert os.path.basename(path) == "custom.png"
        assert os.path.join("ascii", "custom.png") in path

    def test_custom_filename_adds_extension(self):
        path = make_output_path("input", "png", filename="custom")
        assert os.path.basename(path) == "custom.png"

    def test_auto_includes_timestamp(self):
        path = make_output_path("photo.jpg", "png")
        assert "photo_ascii_" in path
        assert path.endswith(".png")
        assert "ascii" in path

    def test_path_traversal_blocked(self):
        path = make_output_path("input", "txt", filename="../../etc/evil")
        assert ".." not in path
        assert os.path.basename(path) == "evil.txt"

    def test_absolute_path_stripped(self):
        path = make_output_path("input", "txt", filename="/tmp/secret.txt")
        assert os.path.basename(path) == "secret.txt"


class TestExportTxt:
    def test_creates_file(self):
        chars = _make_chars(3, 5)
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                path = export_txt(chars, "test")
                assert os.path.exists(path)
                content = open(path).read()
                assert content.count("\n") == 2  # 3 rows, 2 newlines
                assert "#####" in content
            finally:
                os.chdir(old_cwd)


class TestExportHtml:
    def test_creates_file(self):
        chars = _make_chars()
        colors = _make_colors()
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                path = export_html(chars, colors, "test")
                assert os.path.exists(path)
                content = open(path).read()
                assert "<!DOCTYPE html>" in content
                assert "rgb(" in content
            finally:
                os.chdir(old_cwd)

    def test_transparent_background(self):
        chars = _make_chars()
        colors = _make_colors()
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                path = export_html(chars, colors, "test", background="transparent")
                content = open(path).read()
                assert "background: transparent" in content
            finally:
                os.chdir(old_cwd)


class TestExportSvg:
    def test_creates_file(self):
        chars = _make_chars()
        colors = _make_colors()
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                path = export_svg(chars, colors, "test")
                assert os.path.exists(path)
                content = open(path).read()
                assert "<svg" in content
            finally:
                os.chdir(old_cwd)

    def test_transparent_no_rect(self):
        chars = _make_chars()
        colors = _make_colors()
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                path = export_svg(chars, colors, "test", background="transparent")
                content = open(path).read()
                assert "<rect" not in content
            finally:
                os.chdir(old_cwd)


class TestExportPng:
    def test_creates_file(self):
        chars = _make_chars()
        colors = _make_colors()
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                path = export_png(chars, colors, "test")
                assert os.path.exists(path)
                img = Image.open(path)
                assert img.mode == "RGB"
            finally:
                os.chdir(old_cwd)

    def test_transparent_produces_rgba(self):
        chars = _make_chars()
        colors = _make_colors()
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                path = export_png(chars, colors, "test", background="transparent")
                img = Image.open(path)
                assert img.mode == "RGBA"
                # Corner should be transparent
                assert img.getpixel((0, 0))[3] == 0
            finally:
                os.chdir(old_cwd)
