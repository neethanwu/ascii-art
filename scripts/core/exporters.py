"""Export ASCII art to various formats: txt, html, svg, png, gif, clipboard."""

import html as html_module
import os
import re
import sys
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional
from xml.sax.saxutils import escape as xml_escape

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def sanitize_filename(name: str) -> str:
    """Sanitize input name for use in filenames."""
    name = Path(name).stem  # Remove extension
    name = re.sub(r'[^\w\-]', '_', name)  # Replace non-alphanumeric
    name = re.sub(r'_+', '_', name).strip('_')  # Collapse underscores
    return name or "output"


def _ensure_output_dir() -> str:
    """Ensure ./ascii/ output directory exists and return its path."""
    out_dir = os.path.join(os.getcwd(), "ascii")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def make_output_path(input_name: str, ext: str, filename: Optional[str] = None) -> str:
    """Generate timestamped output filename in ./ascii/ directory."""
    out_dir = _ensure_output_dir()

    if filename:
        filename = os.path.basename(filename)  # Strip directory components
        if not filename.endswith(f".{ext}"):
            filename = f"{filename}.{ext}"
        return os.path.join(out_dir, filename)

    safe_name = sanitize_filename(input_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(out_dir, f"{safe_name}_ascii_{timestamp}.{ext}")


def export_txt(chars: list[list[str]], input_name: str, filename: Optional[str] = None) -> str:
    """Export as plain text file."""
    text = "\n".join("".join(row) for row in chars)
    path = make_output_path(input_name, "txt", filename)
    Path(path).write_text(text, encoding="utf-8")
    return path


def export_md(chars: list[list[str]], input_name: str, filename: Optional[str] = None) -> str:
    """Export as markdown file with ASCII art in a fenced code block."""
    text = "\n".join("".join(row) for row in chars)
    md = f"```\n{text}\n```\n"
    path = make_output_path(input_name, "md", filename)
    Path(path).write_text(md, encoding="utf-8")
    return path


def export_html(
    chars: list[list[str]],
    colors: np.ndarray,
    input_name: str,
    background: str = "dark",
    font_size: int = 8,
    filename: Optional[str] = None,
) -> str:
    """Export as self-contained HTML with colored characters."""
    if background == "transparent":
        bg_color = "transparent"
    elif background == "dark":
        bg_color = "#000000"
    else:
        bg_color = "#ffffff"

    lines = []
    rows = len(chars)
    for r in range(rows):
        line_parts = []
        cols = len(chars[r])
        for c in range(cols):
            ch = chars[r][c]
            if ch == " ":
                line_parts.append(" ")
                continue
            ch = html_module.escape(ch)

            cr, cg, cb = int(colors[r, c, 0]), int(colors[r, c, 1]), int(colors[r, c, 2])
            line_parts.append(f'<span style="color:rgb({cr},{cg},{cb})">{ch}</span>')
        lines.append("".join(line_parts))

    body = "\n".join(lines)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ASCII Art</title>
<style>
body {{ margin: 0; background: {bg_color}; display: flex; justify-content: center; padding: 20px; }}
pre {{
  font-family: 'Courier New', 'Consolas', monospace;
  font-size: {font_size}px;
  line-height: 1;
  letter-spacing: 0;
  white-space: pre;
}}
</style>
</head>
<body>
<pre>{body}</pre>
</body>
</html>"""

    path = make_output_path(input_name, "html", filename)
    Path(path).write_text(html, encoding="utf-8")
    return path


def export_svg(
    chars: list[list[str]],
    colors: np.ndarray,
    input_name: str,
    background: str = "dark",
    font_size: int = 8,
    filename: Optional[str] = None,
) -> str:
    """Export as SVG with colored text."""
    rows = len(chars)
    cols = len(chars[0]) if rows > 0 else 0
    char_w = font_size * 0.6  # Approximate monospace width
    char_h = font_size

    svg_w = cols * char_w
    svg_h = rows * char_h

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w:.0f} {svg_h:.0f}" '
        f'width="{svg_w:.0f}" height="{svg_h:.0f}">',
    ]
    if background != "transparent":
        bg_fill = "#000" if background == "dark" else "#fff"
        lines.append(f'<rect width="100%" height="100%" fill="{bg_fill}"/>')
    lines.append(
        f'<text font-family="Courier New, Consolas, monospace" font-size="{font_size}px">'
    )

    for r in range(rows):
        y = (r + 1) * char_h
        row_chars = []
        for c in range(len(chars[r])):
            ch = chars[r][c]
            if ch == " ":
                continue
            ch = xml_escape(ch)

            x = c * char_w
            cr, cg, cb = int(colors[r, c, 0]), int(colors[r, c, 1]), int(colors[r, c, 2])
            row_chars.append(
                f'<tspan x="{x:.1f}" y="{y:.1f}" fill="rgb({cr},{cg},{cb})">{ch}</tspan>'
            )
        lines.extend(row_chars)

    lines.append("</text>")
    lines.append("</svg>")

    path = make_output_path(input_name, "svg", filename)
    Path(path).write_text("\n".join(lines), encoding="utf-8")
    return path


def _get_mono_font(size: int) -> ImageFont.FreeTypeFont:
    """Try to load a monospace font, fall back to default."""
    font_paths = [
        "/System/Library/Fonts/Menlo.ttc",             # macOS
        "/System/Library/Fonts/Courier.dfont",          # macOS fallback
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",  # Linux
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",     # Arch Linux
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def get_font_metrics(font_size: int = 10) -> tuple[int, float]:
    """Return (char_width_px, char_aspect) for the monospace font at given size."""
    font = _get_mono_font(font_size)
    bbox = font.getbbox("M")
    char_w = bbox[2] - bbox[0]
    char_h = bbox[3] - bbox[1]
    line_h = int(char_h * 1.1)
    if char_w == 0:
        return 8, 2.0  # fallback
    return char_w, line_h / char_w


def get_font_char_aspect(font_size: int = 10) -> float:
    """Return the actual height/width ratio of the monospace font at given size."""
    _, aspect = get_font_metrics(font_size)
    return aspect


def export_png(
    chars: list[list[str]],
    colors: np.ndarray,
    input_name: str,
    background: str = "dark",
    font_size: int = 10,
    filename: Optional[str] = None,
) -> str:
    """Render ASCII art as PNG image using Pillow."""
    font = _get_mono_font(font_size)

    # Measure character dimensions
    bbox = font.getbbox("M")
    char_w = bbox[2] - bbox[0]
    char_h = bbox[3] - bbox[1]
    # Add small line spacing
    line_h = int(char_h * 1.1)

    rows = len(chars)
    cols = max(len(row) for row in chars) if rows > 0 else 0

    img_w = cols * char_w + 20  # padding
    img_h = rows * line_h + 20

    if background == "transparent":
        img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    elif background == "dark":
        img = Image.new("RGB", (img_w, img_h), (0, 0, 0))
    else:
        img = Image.new("RGB", (img_w, img_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    for r in range(rows):
        for c in range(len(chars[r])):
            ch = chars[r][c]
            if ch == " ":
                continue
            x = 10 + c * char_w
            y = 10 + r * line_h
            cr, cg, cb = int(colors[r, c, 0]), int(colors[r, c, 1]), int(colors[r, c, 2])
            draw.text((x, y), ch, fill=(cr, cg, cb), font=font)

    path = make_output_path(input_name, "png", filename)
    img.save(path)
    return path


def export_gif(
    frames: list[tuple[list[list[str]], np.ndarray]],
    input_name: str,
    background: str = "dark",
    font_size: int = 8,
    fps: int = 10,
    filename: Optional[str] = None,
) -> str:
    """Render animated ASCII art as GIF."""
    if not frames:
        raise ValueError("No frames to export")

    font = _get_mono_font(font_size)
    bbox = font.getbbox("M")
    char_w = bbox[2] - bbox[0]
    char_h = bbox[3] - bbox[1]
    line_h = int(char_h * 1.1)

    # Use first frame dimensions
    first_chars, _ = frames[0]
    rows = len(first_chars)
    cols = max(len(row) for row in first_chars) if rows > 0 else 0
    img_w = cols * char_w + 20
    img_h = rows * line_h + 20
    bg_color = (0, 0, 0) if background == "dark" else (255, 255, 255)

    pil_frames = []
    for chars, colors in frames:
        img = Image.new("RGB", (img_w, img_h), bg_color)
        draw = ImageDraw.Draw(img)
        for r in range(len(chars)):
            for c in range(len(chars[r])):
                ch = chars[r][c]
                if ch == " ":
                    continue
                x = 10 + c * char_w
                y = 10 + r * line_h
                cr = int(colors[r, c, 0])
                cg = int(colors[r, c, 1])
                cb = int(colors[r, c, 2])
                draw.text((x, y), ch, fill=(cr, cg, cb), font=font)
        # Convert to palette mode for GIF
        pil_frames.append(img.quantize(method=Image.Quantize.MEDIANCUT))

    path = make_output_path(input_name, "gif", filename)
    duration = int(1000 / fps)
    pil_frames[0].save(
        path,
        save_all=True,
        append_images=pil_frames[1:],
        duration=duration,
        loop=0,
    )
    return path


def export_clipboard_text(chars: list[list[str]]) -> bool:
    """Copy ASCII art text to clipboard."""
    text = "\n".join("".join(row) for row in chars)
    system = platform.system()

    try:
        if system == "Darwin":
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            proc.communicate(text.encode("utf-8"))
            return proc.returncode == 0
        elif system == "Linux":
            for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
                try:
                    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                    proc.communicate(text.encode("utf-8"))
                    if proc.returncode == 0:
                        return True
                except FileNotFoundError:
                    continue
            print("Warning: No clipboard tool found. Install xclip or xsel.", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Warning: Clipboard copy failed: {e}", file=sys.stderr)
        return False


def export_clipboard_image(png_path: str) -> bool:
    """Copy PNG image to clipboard (macOS only)."""
    system = platform.system()

    try:
        if system == "Darwin":
            safe_path = os.path.abspath(png_path).replace('\\', '\\\\').replace('"', '\\"')
            script = f'set the clipboard to (read (POSIX file "{safe_path}") as «class PNGf»)'
            proc = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True,
            )
            return proc.returncode == 0
        else:
            print("Warning: Image clipboard not supported on this platform.", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Warning: Image clipboard failed: {e}", file=sys.stderr)
        return False
