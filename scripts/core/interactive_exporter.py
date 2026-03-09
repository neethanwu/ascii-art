"""Export ASCII art as interactive self-contained HTML with canvas renderer."""

import base64
import json
import os
from pathlib import Path
from typing import Optional

import numpy as np

from .exporters import make_output_path

# Path to JS template
_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "interactive")


def _serialize_chars(chars: list[list[str]]) -> str:
    """Serialize char grid to newline-joined string."""
    return "\n".join("".join(row) for row in chars)


def _serialize_colors(colors: np.ndarray) -> str:
    """Serialize color array to base64 RGB bytes."""
    rows, cols = colors.shape[:2]
    flat = colors[:rows, :cols].reshape(-1).astype(np.uint8)
    return base64.b64encode(flat.tobytes()).decode("ascii")


def _build_ascii_data(
    frames: list[tuple[list[list[str]], np.ndarray]],
    rows: int,
    cols: int,
    config: dict,
    fps: int = 10,
) -> str:
    """Build the ASCII_DATA JavaScript object as a string."""
    frame_data = []
    for chars, colors in frames:
        frame_data.append({
            "chars": _serialize_chars(chars),
            "colors": _serialize_colors(colors),
        })

    data = {
        "cols": cols,
        "rows": rows,
        "frames": frame_data,
        "fps": fps,
        "config": config,
    }
    return json.dumps(data, separators=(",", ":"))


def _read_template(filename: str) -> str:
    """Read a JS template file."""
    path = os.path.join(_TEMPLATE_DIR, filename)
    return Path(path).read_text(encoding="utf-8")


def _bg_color_css(background: str) -> str:
    """Return CSS background color."""
    if background == "transparent":
        return "transparent"
    if background == "light":
        return "#ffffff"
    return "#000000"


def export_interactive_html(
    frames: list[tuple[list[list[str]], np.ndarray]],
    input_name: str,
    background: str = "dark",
    font_size: int = 14,
    mouse_mode: str = "push",
    hover_strength: int = 35,
    area_size: int = 300,
    spread: float = 1.1,
    animation: str = "none",
    filename: Optional[str] = None,
    source_aspect: Optional[float] = None,
) -> str:
    """Generate a self-contained interactive HTML file.

    Args:
        frames: List of (chars, colors) tuples. Single frame for images,
                multiple for video (max 60).
        input_name: Original input filename for output naming.
        background: 'dark', 'light', or 'transparent'.
        font_size: Character size in pixels.
        mouse_mode: 'push' or 'attract'.
        hover_strength: Mouse hover force 0-100.
        area_size: Mouse interaction radius in pixels.
        spread: Interaction spread multiplier.
        animation: Animation preset name.
        filename: Optional custom output filename.

    Returns:
        Path to the generated HTML file.
    """
    if not frames:
        raise ValueError("No frames to export")

    # Cap at 60 frames for interactive
    if len(frames) > 60:
        import sys
        print(
            f"Warning: Truncating {len(frames)} frames to 60 for interactive export.",
            file=sys.stderr,
        )
        frames = frames[:60]

    # Determine grid dimensions from first frame
    first_chars = frames[0][0]
    rows = len(first_chars)
    cols = max(len(row) for row in first_chars) if rows > 0 else 0

    # Ensure all char rows are padded to cols width
    padded_frames = []
    for chars, colors in frames:
        padded_chars = []
        for row in chars:
            padded = list(row)
            while len(padded) < cols:
                padded.append(" ")
            padded_chars.append(padded[:cols])
        # Ensure colors match
        c = colors[:rows, :cols]
        padded_frames.append((padded_chars, c))

    config = {
        "background": background,
        "fontSize": font_size,
        "mouseMode": mouse_mode,
        "hoverStrength": hover_strength,
        "areaSize": area_size,
        "spread": spread,
        "animation": animation,
    }
    if source_aspect is not None:
        config["sourceAspect"] = round(source_aspect, 6)

    ascii_data_json = _build_ascii_data(padded_frames, rows, cols, config)
    renderer_js = _read_template("renderer.js")
    animations_js = _read_template("animations.js") if animation != "none" else ""

    bg_css = _bg_color_css(background)

    # Noscript fallback: first frame as plain text
    noscript_text = _serialize_chars(padded_frames[0][0])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ASCII Art — Interactive</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ height: 100%; background: {bg_css}; overflow: hidden; }}
#ascii-container {{
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}}
#ascii-canvas {{
  display: block;
  max-width: 100%;
  max-height: 100vh;
}}
noscript pre {{
  font-family: monospace;
  font-size: {font_size}px;
  line-height: 1;
  color: {"#ffffff" if background == "dark" else "#000000"};
  padding: 20px;
  white-space: pre;
}}
</style>
</head>
<body>
<div id="ascii-container">
  <canvas id="ascii-canvas"></canvas>
</div>
<noscript>
<pre>{noscript_text}</pre>
</noscript>
<script>
var ASCII_DATA = {ascii_data_json};
</script>
<script>
{animations_js}
</script>
<script>
{renderer_js}
</script>
</body>
</html>"""

    path = make_output_path(input_name, "html", filename)
    Path(path).write_text(html, encoding="utf-8")
    return path
