"""Dithering algorithms for ASCII art conversion."""

import numpy as np


def floyd_steinberg(brightness: np.ndarray, levels: int, strength: float = 0.8) -> np.ndarray:
    """
    Floyd-Steinberg error diffusion dithering.
    Distributes quantization error to 4 neighbors: 7/16, 3/16, 5/16, 1/16.

    Args:
        brightness: (rows, cols) float 0-255
        levels: number of output levels (e.g. len(ramp))
        strength: 0.0-1.0, how much error to distribute
    """
    data = brightness.astype(np.float64).copy()
    rows, cols = data.shape
    step = 255.0 / max(levels - 1, 1)

    for y in range(rows):
        for x in range(cols):
            old_val = data[y, x]
            new_val = round(old_val / step) * step
            new_val = max(0.0, min(255.0, new_val))
            data[y, x] = new_val
            error = (old_val - new_val) * strength

            if x + 1 < cols:
                data[y, x + 1] = max(0.0, min(255.0, data[y, x + 1] + error * 7 / 16))
            if y + 1 < rows:
                if x - 1 >= 0:
                    data[y + 1, x - 1] = max(0.0, min(255.0, data[y + 1, x - 1] + error * 3 / 16))
                data[y + 1, x] = max(0.0, min(255.0, data[y + 1, x] + error * 5 / 16))
                if x + 1 < cols:
                    data[y + 1, x + 1] = max(0.0, min(255.0, data[y + 1, x + 1] + error * 1 / 16))

    return np.clip(data, 0, 255)


# 4x4 Bayer matrix
BAYER_4 = np.array([
    [0,  8,  2, 10],
    [12, 4,  14, 6],
    [3,  11, 1,  9],
    [15, 7,  13, 5],
], dtype=np.float64) / 16.0


def bayer(brightness: np.ndarray, levels: int, strength: float = 0.8) -> np.ndarray:
    """
    Ordered dithering using 4x4 Bayer matrix.
    No error propagation — parallelizable, no directional artifacts.
    """
    data = brightness.astype(np.float64).copy()
    rows, cols = data.shape
    step = 255.0 / max(levels - 1, 1)

    # Tile the Bayer matrix across the image
    threshold = np.tile(BAYER_4, (rows // 4 + 1, cols // 4 + 1))[:rows, :cols]

    # Apply threshold offset
    offset = (threshold - 0.5) * step * strength
    data += offset

    # Quantize
    data = np.round(data / step) * step
    return np.clip(data, 0, 255)


def atkinson(brightness: np.ndarray, levels: int, strength: float = 0.8) -> np.ndarray:
    """
    Atkinson dithering — diffuses only 75% (6/8) of error.
    Produces crisper, higher-contrast results. Retro Macintosh aesthetic.
    """
    data = brightness.astype(np.float64).copy()
    rows, cols = data.shape
    step = 255.0 / max(levels - 1, 1)

    for y in range(rows):
        for x in range(cols):
            old_val = data[y, x]
            new_val = round(old_val / step) * step
            new_val = max(0.0, min(255.0, new_val))
            data[y, x] = new_val
            error = (old_val - new_val) * strength / 8  # Each neighbor gets 1/8

            # 6 neighbors (only 6/8 = 75% of error distributed)
            if x + 1 < cols:
                data[y, x + 1] = max(0.0, min(255.0, data[y, x + 1] + error))
            if x + 2 < cols:
                data[y, x + 2] = max(0.0, min(255.0, data[y, x + 2] + error))
            if y + 1 < rows:
                if x - 1 >= 0:
                    data[y + 1, x - 1] = max(0.0, min(255.0, data[y + 1, x - 1] + error))
                data[y + 1, x] = max(0.0, min(255.0, data[y + 1, x] + error))
                if x + 1 < cols:
                    data[y + 1, x + 1] = max(0.0, min(255.0, data[y + 1, x + 1] + error))
            if y + 2 < rows:
                data[y + 2, x] = max(0.0, min(255.0, data[y + 2, x] + error))

    return np.clip(data, 0, 255)


DITHER_ALGORITHMS = {
    "none": None,
    "floyd-steinberg": floyd_steinberg,
    "bayer": bayer,
    "atkinson": atkinson,
}


def apply_dither(
    brightness: np.ndarray,
    algorithm: str = "none",
    levels: int = 10,
    strength: float = 0.8,
) -> np.ndarray:
    """Apply dithering to brightness grid."""
    if algorithm == "none" or algorithm not in DITHER_ALGORITHMS:
        return brightness

    fn = DITHER_ALGORITHMS[algorithm]
    if fn is None:
        return brightness
    return fn(brightness, levels, strength)
