"""Color mode implementations."""

import numpy as np
from typing import Optional


# CSS named colors (subset of most common ones)
NAMED_COLORS = {
    "red": "#ff0000", "green": "#008000", "blue": "#0000ff",
    "yellow": "#ffff00", "cyan": "#00ffff", "magenta": "#ff00ff",
    "orange": "#ffa500", "purple": "#800080", "pink": "#ffc0cb",
    "lime": "#00ff00", "teal": "#008080", "navy": "#000080",
    "maroon": "#800000", "olive": "#808000", "coral": "#ff7f50",
    "salmon": "#fa8072", "gold": "#ffd700", "indigo": "#4b0082",
    "violet": "#ee82ee", "crimson": "#dc143c", "turquoise": "#40e0d0",
    "tomato": "#ff6347", "chocolate": "#d2691e", "firebrick": "#b22222",
    "dodgerblue": "#1e90ff", "limegreen": "#32cd32", "hotpink": "#ff69b4",
    "skyblue": "#87ceeb", "springgreen": "#00ff7f", "white": "#ffffff",
    "silver": "#c0c0c0", "gray": "#808080", "grey": "#808080",
}


def parse_hex_color(hex_str: str) -> tuple[int, int, int]:
    """Parse hex color string like '#ff6600', 'ff6600', or named color like 'coral'."""
    # Check if it's a named color
    name = hex_str.lower().strip().lstrip("#")
    if name in NAMED_COLORS:
        hex_str = NAMED_COLORS[name]
    hex_str = hex_str.lstrip("#")
    if len(hex_str) != 6:
        raise ValueError(f"Invalid color: '{hex_str}'. Use hex (#ff6600) or a named color (coral, red, skyblue, etc.)")
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
        mode: grayscale, original (or full), matrix, amber, custom
        background: dark or light
        custom_color: hex color for custom mode

    Returns:
        (rows, cols, 3) uint8 array of RGB colors per character
    """
    rows, cols = brightness.shape
    result = np.zeros((rows, cols, 3), dtype=np.uint8)
    norm = np.clip(brightness / 255.0, 0, 1)

    if mode in ("original", "full"):
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
