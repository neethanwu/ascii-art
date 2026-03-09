"""Core image processing pipeline: load, crop, tile, luminance."""

import numpy as np
from PIL import Image, ImageOps
from dataclasses import dataclass
from typing import Optional


@dataclass
class TileGrid:
    """Grid of processed tiles ready for character mapping."""
    brightness: np.ndarray   # (rows, cols) float 0-255
    colors: np.ndarray       # (rows, cols, 3) uint8 RGB
    rows: int
    cols: int


# Aspect ratio presets: (width, height)
ASPECT_RATIOS = {
    "original": None,
    "16:9": (16, 9),
    "4:3": (4, 3),
    "1:1": (1, 1),
    "3:4": (3, 4),
    "9:16": (9, 16),
}

# Character aspect ratio: monospace chars are ~2x taller than wide
CHAR_ASPECT = 2.0


def load_image(path: str) -> Image.Image:
    """Load image, handle EXIF rotation, convert to RGB."""
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    if img.mode == "RGBA":
        # Composite onto black background
        bg = Image.new("RGB", img.size, (0, 0, 0))
        bg.paste(img, mask=img.split()[3])
        return bg
    return img.convert("RGB")


def crop_to_ratio(img: Image.Image, ratio: Optional[str] = None) -> Image.Image:
    """Center-crop image to target aspect ratio."""
    if ratio is None or ratio == "original" or ratio not in ASPECT_RATIOS:
        return img

    target = ASPECT_RATIOS[ratio]
    if target is None:
        return img

    target_w, target_h = target
    img_w, img_h = img.size
    img_aspect = img_w / img_h
    target_aspect = target_w / target_h

    if img_aspect > target_aspect:
        # Image is wider — crop width
        new_w = int(img_h * target_aspect)
        offset = (img_w - new_w) // 2
        return img.crop((offset, 0, offset + new_w, img_h))
    else:
        # Image is taller — crop height
        new_h = int(img_w / target_aspect)
        offset = (img_h - new_h) // 2
        return img.crop((0, offset, img_w, offset + new_h))


def process_image(
    img: Image.Image,
    cols: int = 80,
    ratio: Optional[str] = None,
    invert: bool = False,
) -> TileGrid:
    """
    Process image through the ASCII pipeline.

    1. Crop to aspect ratio
    2. Calculate tile dimensions with char aspect correction
    3. Downsample via Pillow resize (high quality)
    4. Compute per-tile brightness (BT.601) and average color
    """
    # Crop
    img = crop_to_ratio(img, ratio)

    # Calculate output dimensions
    img_w, img_h = img.size

    # Clamp cols to image width
    cols = min(cols, img_w)

    # Rows determined by aspect ratio correction
    tile_w = img_w / cols
    tile_h = tile_w * CHAR_ASPECT
    rows = max(1, int(img_h / tile_h))

    # Downsample using Pillow (high-quality Lanczos)
    resized = img.resize((cols, rows), Image.LANCZOS)
    pixels = np.array(resized, dtype=np.float64)  # (rows, cols, 3)

    # BT.601 luminance
    brightness = (
        0.299 * pixels[:, :, 0]
        + 0.587 * pixels[:, :, 1]
        + 0.114 * pixels[:, :, 2]
    )

    if invert:
        brightness = 255.0 - brightness

    colors = np.array(resized, dtype=np.uint8)

    return TileGrid(
        brightness=brightness,
        colors=colors,
        rows=rows,
        cols=cols,
    )


def process_image_for_braille(
    img: Image.Image,
    cols: int = 80,
    ratio: Optional[str] = None,
    invert: bool = False,
) -> tuple:
    """
    Process image for braille style.
    Returns higher-res brightness grid (2x cols, 4x rows) plus colors at normal res.
    Braille encodes a 2x4 dot grid per character.
    """
    img = crop_to_ratio(img, ratio)
    img_w, img_h = img.size
    cols = min(cols, img_w // 2)

    # Braille: each char is 2 dots wide, 4 dots tall
    dot_cols = cols * 2
    tile_w = img_w / dot_cols
    tile_h = tile_w * (CHAR_ASPECT / 2)  # Less correction since 4 rows per char
    dot_rows = max(4, int(img_h / tile_h))
    # Round to multiple of 4
    dot_rows = (dot_rows // 4) * 4

    # High-res for dot pattern
    resized_hi = img.resize((dot_cols, dot_rows), Image.LANCZOS)
    pixels_hi = np.array(resized_hi, dtype=np.float64)
    brightness_hi = (
        0.299 * pixels_hi[:, :, 0]
        + 0.587 * pixels_hi[:, :, 1]
        + 0.114 * pixels_hi[:, :, 2]
    )
    if invert:
        brightness_hi = 255.0 - brightness_hi

    # Normal-res for colors
    char_rows = dot_rows // 4
    resized_lo = img.resize((cols, char_rows), Image.LANCZOS)
    colors = np.array(resized_lo, dtype=np.uint8)

    return brightness_hi, colors, char_rows, cols


def process_image_for_edge(
    img: Image.Image,
    cols: int = 80,
    ratio: Optional[str] = None,
    invert: bool = False,
) -> tuple:
    """
    Process image for edge detection style.
    Returns gradient magnitude, direction, and colors.
    """
    img = crop_to_ratio(img, ratio)
    img_w, img_h = img.size
    cols = min(cols, img_w)

    tile_w = img_w / cols
    tile_h = tile_w * CHAR_ASPECT
    rows = max(1, int(img_h / tile_h))

    resized = img.resize((cols, rows), Image.LANCZOS)
    pixels = np.array(resized, dtype=np.float64)

    # Grayscale for edge detection
    gray = 0.299 * pixels[:, :, 0] + 0.587 * pixels[:, :, 1] + 0.114 * pixels[:, :, 2]

    # Sobel operator
    padded = np.pad(gray, 1, mode='edge')

    # Gx kernel: [[-1,0,1],[-2,0,2],[-1,0,1]]
    gx = (
        -padded[:-2, :-2] + padded[:-2, 2:]
        - 2 * padded[1:-1, :-2] + 2 * padded[1:-1, 2:]
        - padded[2:, :-2] + padded[2:, 2:]
    )

    # Gy kernel: [[-1,-2,-1],[0,0,0],[1,2,1]]
    gy = (
        -padded[:-2, :-2] - 2 * padded[:-2, 1:-1] - padded[:-2, 2:]
        + padded[2:, :-2] + 2 * padded[2:, 1:-1] + padded[2:, 2:]
    )

    magnitude = np.sqrt(gx ** 2 + gy ** 2)
    direction = np.arctan2(gy, gx)

    colors = np.array(resized, dtype=np.uint8)

    return magnitude, direction, colors, rows, cols
