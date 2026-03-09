"""Art style implementations: classic, braille, block, edge, dot-cross, halftone, particles, and themed presets."""

import numpy as np
from numpy.random import default_rng

# Default density ramp (dark → light, 70 chars — Paulbourke standard)
DEFAULT_RAMP = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`. "

# Dot Cross ramp: uses dot/cross/star symbols for a different aesthetic
DOT_CROSS_RAMP = "\u2588\u2593#X*x+:\u00b7 "  # █▓#X*x+:· (space)

# Halftone ramp: simulates varying dot sizes
HALFTONE_RAMP = "@O0o\u00b7. "  # @O0o·. (space)

# Particles chars: small symbols scattered by brightness
PARTICLE_CHARS = ["\u2022", "\u00b7", "\u2027", "*", "\u2219", "+"]  # •·‧*∙+

# Themed preset definitions
PRESETS = {
    "retro-art": {
        "ramp": "\u2588\u2593\u2592\u2591#%=+:. ",
        "color": "amber",
        "dither": "atkinson",
        "dither_strength": 0.9,
        "description": "Block characters with amber tint and Atkinson dithering for retro CRT look",
    },
    "terminal": {
        "ramp": "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`. ",
        "color": "matrix",
        "dither": "none",
        "description": "Classic ASCII in green terminal monochrome",
    },
}

# Braille dot map: position (row, col) → bit value
BRAILLE_DOT_MAP = [
    [0x01, 0x08],  # row 0
    [0x02, 0x10],  # row 1
    [0x04, 0x20],  # row 2
    [0x40, 0x80],  # row 3
]

# Edge detection character mapping
EDGE_CHARS = {
    "horizontal": "\u2014",  # —
    "diagonal_up": "/",
    "vertical": "|",
    "diagonal_down": "\\",
}


def classic_ascii(brightness: np.ndarray, ramp: str = DEFAULT_RAMP) -> list[list[str]]:
    """
    Map brightness values to characters from density ramp.
    brightness: (rows, cols) float array 0-255
    Returns: 2D list of characters
    """
    ramp_len = len(ramp)
    ramp_arr = np.array(list(ramp))
    indices = np.clip(brightness / 255.0, 0, 1)
    indices = (indices * (ramp_len - 1)).astype(int)
    indices = np.clip(indices, 0, ramp_len - 1)
    return ramp_arr[indices].tolist()


def braille_style(brightness_hi: np.ndarray, threshold: float = 128.0) -> list[list[str]]:
    """
    Convert high-res brightness grid to braille characters.
    brightness_hi: (dot_rows, dot_cols) — must be divisible by 4 rows, 2 cols
    Each 4x2 block maps to one braille character.
    """
    dot_rows, dot_cols = brightness_hi.shape
    char_rows = dot_rows // 4
    char_cols = dot_cols // 2

    # Threshold: pixels below threshold are "on" (dark = filled dot)
    on = brightness_hi < threshold

    result = []
    for cr in range(char_rows):
        row = []
        for cc in range(char_cols):
            codepoint = 0x2800
            for dr in range(4):
                for dc in range(2):
                    py = cr * 4 + dr
                    px = cc * 2 + dc
                    if py < dot_rows and px < dot_cols and on[py, px]:
                        codepoint |= BRAILLE_DOT_MAP[dr][dc]
            row.append(chr(codepoint))
        result.append(row)
    return result


def block_style(brightness: np.ndarray) -> list[list[str]]:
    """
    Map brightness to Unicode block elements: \u2588\u2593\u2592\u2591 (space)
    5 levels of fill.
    """
    blocks = "\u2588\u2593\u2592\u2591 "
    blocks_arr = np.array(list(blocks))
    indices = np.clip((255.0 - brightness) / 255.0, 0, 1)
    indices = (indices * (len(blocks) - 1)).astype(int)
    indices = np.clip(indices, 0, len(blocks) - 1)
    return blocks_arr[indices].tolist()


def edge_style(
    magnitude: np.ndarray,
    direction: np.ndarray,
    threshold: float = 30.0,
) -> list[list[str]]:
    """
    Map edge magnitude and direction to directional characters.
    magnitude: (rows, cols) float
    direction: (rows, cols) float in radians
    """
    rows, cols = magnitude.shape
    result = []

    for r in range(rows):
        row = []
        for c in range(cols):
            mag = magnitude[r, c]
            if mag < threshold:
                row.append(" ")
                continue

            # Normalize angle to 0-180 degrees
            deg = np.degrees(direction[r, c]) % 180

            if deg < 22.5 or deg >= 157.5:
                row.append(EDGE_CHARS["horizontal"])
            elif deg < 67.5:
                row.append(EDGE_CHARS["diagonal_up"])
            elif deg < 112.5:
                row.append(EDGE_CHARS["vertical"])
            else:
                row.append(EDGE_CHARS["diagonal_down"])
        result.append(row)
    return result


def dot_cross_style(brightness: np.ndarray) -> list[list[str]]:
    """
    Map brightness using dot/cross symbols for a graphic, stippled look.
    Uses: █▓#X*x+:· (space)
    """
    return classic_ascii(brightness, ramp=DOT_CROSS_RAMP)


def halftone_style(brightness: np.ndarray) -> list[list[str]]:
    """
    Simulate print halftone with varying-size dot characters.
    Uses: @O0o·. (space) — large dots for dark, small for light.
    """
    return classic_ascii(brightness, ramp=HALFTONE_RAMP)


def particles_style(brightness: np.ndarray, seed: int = 42) -> list[list[str]]:
    """
    Sparse scattered dots — darker pixels have higher chance of placing a particle.
    Lighter areas become empty space, creating an organic dispersed look.
    """
    rows, cols = brightness.shape
    rng = default_rng(seed)

    # Probability of placing a particle: dark=high, light=low
    # Invert and normalize: 0 (white) → 0% chance, 255 (black) → 90% chance
    prob = (255.0 - brightness) / 255.0 * 0.9

    # Random roll per cell
    rolls = rng.random((rows, cols))

    result = []
    for r in range(rows):
        row = []
        for c in range(cols):
            if rolls[r, c] < prob[r, c]:
                # Pick char based on brightness: darker = bigger particle
                dark = (255.0 - brightness[r, c]) / 255.0
                idx = min(int(dark * len(PARTICLE_CHARS)), len(PARTICLE_CHARS) - 1)
                row.append(PARTICLE_CHARS[idx])
            else:
                row.append(" ")
        result.append(row)
    return result
