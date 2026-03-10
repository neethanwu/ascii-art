#!/usr/bin/env python3
"""Save an image to ascii/tmp/ for processing. Outputs the saved path to stdout.

Two modes:
  save_image.py <source_path>   — copy a file from disk
  save_image.py --clipboard     — grab image from system clipboard (macOS)
"""

import os
import shutil
import sys
from datetime import datetime


def _out_dir():
    return os.path.join(os.getcwd(), "ascii", "tmp")


def _dest_path(out_dir, ext=".png"):
    os.makedirs(out_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%H%M%S")
    return os.path.join(out_dir, f"input_{timestamp}{ext}")


def save_from_clipboard(out_dir):
    """Grab image from system clipboard using PIL.ImageGrab (macOS/Windows)."""
    try:
        from PIL import ImageGrab
    except ImportError:
        print("Error: Pillow not installed. Run setup.sh first.", file=sys.stderr)
        sys.exit(1)

    from PIL import Image

    clip = ImageGrab.grabclipboard()
    if not isinstance(clip, Image.Image):
        print("Error: No image found in clipboard.", file=sys.stderr)
        print("Hint: Copy an image first, then run this script.", file=sys.stderr)
        sys.exit(1)

    dest = _dest_path(out_dir)
    clip.save(dest, "PNG")
    print(dest)


def save_from_path(source, out_dir):
    """Copy an image file to ascii/tmp/."""
    if not os.path.isfile(source):
        print(f"Error: Source file not found: {source}", file=sys.stderr)
        sys.exit(1)

    ext = os.path.splitext(source)[1].lower() or ".png"
    dest = _dest_path(out_dir, ext)
    shutil.copy2(source, dest)
    print(dest)


def main():
    if len(sys.argv) < 2:
        print("Usage:", file=sys.stderr)
        print("  save_image.py <source_path>   Copy file to ascii/tmp/", file=sys.stderr)
        print("  save_image.py --clipboard      Grab from system clipboard", file=sys.stderr)
        print("Prints saved path to stdout.", file=sys.stderr)
        sys.exit(1)

    out_dir = _out_dir()

    if sys.argv[1] == "--clipboard":
        save_from_clipboard(out_dir)
    else:
        save_from_path(sys.argv[1], out_dir)


if __name__ == "__main__":
    main()
