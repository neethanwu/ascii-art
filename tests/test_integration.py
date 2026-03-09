"""Integration tests — end-to-end CLI runs."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import subprocess
import tempfile
import numpy as np
import pytest
from PIL import Image

PYTHON = os.path.join(
    os.path.dirname(__file__), "..", "scripts", ".venv", "bin", "python"
)
CONVERT = os.path.join(os.path.dirname(__file__), "..", "scripts", "convert.py")


def _run(args, cwd=None):
    """Run convert.py with given args, return (returncode, stdout, stderr)."""
    cmd = [PYTHON, CONVERT] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr


def _create_test_image(tmpdir):
    """Create a test image in tmpdir."""
    arr = np.zeros((100, 150, 3), dtype=np.uint8)
    for x in range(150):
        for y in range(100):
            arr[y, x] = [int(x / 150 * 255), int(y / 100 * 255), 128]
    path = os.path.join(tmpdir, "test.png")
    Image.fromarray(arr).save(path)
    return path


@pytest.fixture
def tmpdir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.mark.skipif(not os.path.exists(PYTHON), reason="venv not set up")
class TestTextConversion:
    def test_text_to_stdout(self, tmpdir):
        rc, stdout, stderr = _run(
            ["--input", "Hello", "--type", "text"], cwd=tmpdir
        )
        assert rc == 0
        assert len(stdout.strip()) > 0

    def test_text_with_font(self, tmpdir):
        rc, stdout, stderr = _run(
            ["--input", "Hi", "--type", "text", "--font", "doom"], cwd=tmpdir
        )
        assert rc == 0
        assert len(stdout.strip()) > 0

    def test_text_export_txt(self, tmpdir):
        rc, stdout, stderr = _run(
            ["--input", "Test", "--type", "text", "--export", "txt",
             "--filename", "out.txt"], cwd=tmpdir
        )
        assert rc == 0
        assert os.path.exists(os.path.join(tmpdir, "ascii", "out.txt"))


@pytest.mark.skipif(not os.path.exists(PYTHON), reason="venv not set up")
class TestImageConversion:
    def test_all_styles(self, tmpdir):
        img_path = _create_test_image(tmpdir)
        styles = ["classic", "braille", "block", "edge",
                   "dot-cross", "halftone", "retro-art", "terminal"]
        for style in styles:
            rc, stdout, stderr = _run(
                ["--input", img_path, "--style", style, "--cols", "40",
                 "--export", "txt", "--filename", f"{style}.txt"], cwd=tmpdir
            )
            assert rc == 0, f"Style {style} failed: {stderr}"
            assert os.path.exists(os.path.join(tmpdir, "ascii", f"{style}.txt"))

    def test_all_color_modes(self, tmpdir):
        img_path = _create_test_image(tmpdir)
        for color in ["grayscale", "full", "matrix", "amber"]:
            rc, stdout, stderr = _run(
                ["--input", img_path, "--color", color, "--cols", "40",
                 "--export", "txt", "--filename", f"{color}.txt"], cwd=tmpdir
            )
            assert rc == 0, f"Color {color} failed: {stderr}"

    def test_custom_named_color(self, tmpdir):
        img_path = _create_test_image(tmpdir)
        rc, stdout, stderr = _run(
            ["--input", img_path, "--color", "custom", "--custom-color", "coral",
             "--cols", "40", "--export", "png", "--filename", "coral.png"], cwd=tmpdir
        )
        assert rc == 0

    def test_transparent_png(self, tmpdir):
        img_path = _create_test_image(tmpdir)
        rc, stdout, stderr = _run(
            ["--input", img_path, "--cols", "40", "--background", "transparent",
             "--export", "png", "--filename", "trans.png"], cwd=tmpdir
        )
        assert rc == 0
        img = Image.open(os.path.join(tmpdir, "ascii", "trans.png"))
        assert img.mode == "RGBA"

    def test_transparent_html(self, tmpdir):
        img_path = _create_test_image(tmpdir)
        rc, stdout, stderr = _run(
            ["--input", img_path, "--cols", "40", "--background", "transparent",
             "--export", "html", "--filename", "trans.html"], cwd=tmpdir
        )
        assert rc == 0
        content = open(os.path.join(tmpdir, "ascii", "trans.html")).read()
        assert "background: transparent" in content

    def test_preset_respects_explicit_override(self, tmpdir):
        """Retro-art preset defaults to amber, but explicit grayscale should stick."""
        img_path = _create_test_image(tmpdir)
        rc, stdout, stderr = _run(
            ["--input", img_path, "--style", "retro-art", "--color", "grayscale",
             "--cols", "40", "--export", "png", "--filename", "override.png"], cwd=tmpdir
        )
        assert rc == 0

    def test_random_mode(self, tmpdir):
        img_path = _create_test_image(tmpdir)
        rc, stdout, stderr = _run(
            ["--input", img_path, "--random", "--cols", "40",
             "--export", "txt", "--filename", "random.txt"], cwd=tmpdir
        )
        assert rc == 0
        assert "Random mode:" in stderr

    def test_all_export_formats(self, tmpdir):
        img_path = _create_test_image(tmpdir)
        for fmt in ["txt", "html", "svg", "png"]:
            rc, stdout, stderr = _run(
                ["--input", img_path, "--cols", "40",
                 "--export", fmt, "--filename", f"out.{fmt}"], cwd=tmpdir
            )
            assert rc == 0, f"Export {fmt} failed: {stderr}"
            assert os.path.exists(os.path.join(tmpdir, "ascii", f"out.{fmt}"))

    def test_dithering(self, tmpdir):
        img_path = _create_test_image(tmpdir)
        for dither in ["floyd-steinberg", "bayer", "atkinson"]:
            rc, stdout, stderr = _run(
                ["--input", img_path, "--dither", dither, "--cols", "40",
                 "--export", "txt", "--filename", f"{dither}.txt"], cwd=tmpdir
            )
            assert rc == 0, f"Dither {dither} failed: {stderr}"

    def test_aspect_ratios(self, tmpdir):
        img_path = _create_test_image(tmpdir)
        for ratio in ["original", "16:9", "4:3", "1:1"]:
            rc, stdout, stderr = _run(
                ["--input", img_path, "--ratio", ratio, "--cols", "40",
                 "--export", "txt", "--filename", f"ratio_{ratio}.txt"], cwd=tmpdir
            )
            assert rc == 0, f"Ratio {ratio} failed: {stderr}"


@pytest.mark.skipif(not os.path.exists(PYTHON), reason="venv not set up")
class TestAutoDetect:
    def test_image_auto_detected(self, tmpdir):
        img_path = _create_test_image(tmpdir)
        rc, stdout, stderr = _run(
            ["--input", img_path, "--cols", "40",
             "--export", "txt", "--filename", "auto.txt"], cwd=tmpdir
        )
        assert rc == 0

    def test_text_auto_detected(self, tmpdir):
        rc, stdout, stderr = _run(
            ["--input", "Hello World"], cwd=tmpdir
        )
        assert rc == 0
        assert len(stdout.strip()) > 0
