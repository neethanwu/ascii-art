"""Color mode implementations."""

import numpy as np
from typing import Optional


def parse_hex_color(hex_str: str) -> tuple[int, int, int]:
    """Parse hex color string like '#ff6600' or 'ff6600'."""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) != 6:
        raise ValueError(f"Invalid hex color: #{hex_str}")
    return (
        int(hex_str[0:2], 16),
        int(hex_str[2:4], 16),
        int(hex_str[4:6], 16),
    )


def apply_color(
    brightness: np.ndarray,
    colors: np.ndarray,
    mode: str = "grayscale",
    background: str = "dark",
    custom_color: Optional[str] = None,
) -> np.ndarray:
    """
    Compute per-character RGB colors based on color mode.

    Args:
        brightness: (rows, cols) float 0-255
        colors: (rows, cols, 3) uint8 original tile colors
        mode: grayscale, full, matrix, amber, custom
        background: dark or light
        custom_color: hex color for custom mode

    Returns:
        (rows, cols, 3) uint8 array of RGB colors per character
    """
    rows, cols = brightness.shape
    result = np.zeros((rows, cols, 3), dtype=np.uint8)
    norm = np.clip(brightness / 255.0, 0, 1)

    if mode == "full":
        # Use original tile colors directly
        result = colors.copy()

    elif mode == "matrix":
        # Green tint: rgb(0, brightness, 0)
        result[:, :, 1] = np.clip(brightness, 0, 255).astype(np.uint8)

    elif mode == "amber":
        # Amber tint: rgb(brightness, brightness*0.6, 0)
        result[:, :, 0] = np.clip(brightness, 0, 255).astype(np.uint8)
        result[:, :, 1] = np.clip(brightness * 0.6, 0, 255).astype(np.uint8)

    elif mode == "custom" and custom_color:
        # User hex color, modulated by brightness
        r, g, b = parse_hex_color(custom_color)
        result[:, :, 0] = np.clip(norm * r, 0, 255).astype(np.uint8)
        result[:, :, 1] = np.clip(norm * g, 0, 255).astype(np.uint8)
        result[:, :, 2] = np.clip(norm * b, 0, 255).astype(np.uint8)

    else:
        # Grayscale (default)
        if background == "dark":
            # Light chars on dark background
            gray = np.clip(brightness, 0, 255).astype(np.uint8)
        else:
            # Dark chars on light background
            gray = np.clip(255 - brightness, 0, 255).astype(np.uint8)
        result[:, :, 0] = gray
        result[:, :, 1] = gray
        result[:, :, 2] = gray

    return result
