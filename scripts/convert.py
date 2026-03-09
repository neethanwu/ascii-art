#!/usr/bin/env python3
"""ASCII Art Converter — CLI entry point."""

import argparse
import random
import sys
import os

import numpy as np

# Add scripts dir to path so core package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.pipeline import (
    load_image,
    process_image,
    process_image_for_braille,
    process_image_for_edge,
)
from core.styles import (
    classic_ascii,
    braille_style,
    block_style,
    edge_style,
    dot_cross_style,
    halftone_style,
    particles_style,
    DEFAULT_RAMP,
    PRESETS,
)
from core.colors import apply_color
from core.dither import apply_dither
from core.text_render import render_text, AVAILABLE_FONTS
from core.exporters import (
    export_txt,
    export_html,
    export_svg,
    export_png,
    export_gif,
    export_clipboard_text,
    export_clipboard_image,
    export_md,
    get_font_metrics,
)
from core.interactive_exporter import export_interactive_html
from core.react_exporter import export_react_component

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}
VIDEO_EXTS = {".mp4", ".webm", ".avi", ".mov", ".mkv"}

ALL_STYLES = [
    "classic", "braille", "block", "edge",
    "dot-cross", "halftone", "particles",
    "retro-art", "terminal",
]

# Random mode: curated good combinations
RANDOM_COMBOS = [
    {"style": "classic", "color": "matrix", "dither": "none"},
    {"style": "classic", "color": "amber", "dither": "floyd-steinberg"},
    {"style": "braille", "color": "grayscale", "dither": "none"},
    {"style": "braille", "color": "matrix", "dither": "none"},
    {"style": "block", "color": "original", "dither": "none"},
    {"style": "block", "color": "grayscale", "dither": "bayer"},
    {"style": "classic", "color": "original", "dither": "atkinson"},
    {"style": "classic", "color": "grayscale", "dither": "floyd-steinberg"},
    {"style": "edge", "color": "grayscale", "dither": "none"},
    {"style": "edge", "color": "matrix", "dither": "none"},
    {"style": "dot-cross", "color": "original", "dither": "bayer"},
    {"style": "halftone", "color": "grayscale", "dither": "floyd-steinberg"},
    {"style": "particles", "color": "original", "dither": "none"},
    {"style": "particles", "color": "matrix", "dither": "none"},
    {"style": "retro-art", "color": "amber", "dither": "atkinson"},
    {"style": "terminal", "color": "matrix", "dither": "none"},
]


def detect_type(input_str: str) -> str:
    """Auto-detect input type from string content."""
    if os.path.exists(input_str):
        ext = os.path.splitext(input_str)[1].lower()
        if ext in IMAGE_EXTS:
            # Check if GIF is animated → treat as video
            if ext == ".gif":
                from PIL import Image
                try:
                    img = Image.open(input_str)
                    if getattr(img, "n_frames", 1) > 1:
                        return "video"
                except Exception:
                    pass
            return "image"
        if ext in VIDEO_EXTS:
            return "video"
    # If it's not a file path, treat as text
    return "text"


def _apply_preset(args) -> None:
    """Apply themed preset overrides if style is a preset."""
    if args.style in PRESETS:
        preset = PRESETS[args.style]
        # Only override color/dither if user didn't explicitly set them
        # (None means the user did not pass the flag)
        if args.color is None:
            args.color = preset.get("color", "grayscale")
        if args.dither is None:
            args.dither = preset.get("dither", "none")
        if args.dither_strength is None:
            args.dither_strength = preset.get("dither_strength", 0.8)
    # Apply real defaults for non-preset styles (or any still-None values)
    if args.color is None:
        args.color = "grayscale"
    if args.dither is None:
        args.dither = "none"
    if args.dither_strength is None:
        args.dither_strength = 0.8


def _get_font_params(args):
    """Return (char_pixel_width, char_aspect) for pixel exports, (0, None) for text."""
    if args.export in (None, "png", "gif", "clipboard", "html", "svg", "interactive", "tsx"):
        return get_font_metrics(font_size=args.font_size)
    return 0, None  # txt — use terminal defaults


def _convert_with_style(args, img):
    """Core conversion logic shared by image and video paths."""
    char_pixel_width, char_aspect = _get_font_params(args)

    if args.style == "braille":
        brightness_hi, colors_lo, char_rows, char_cols = process_image_for_braille(
            img, cols=args.cols, ratio=args.ratio, invert=args.invert,
            char_aspect=char_aspect, char_pixel_width=char_pixel_width,
        )
        threshold = float(brightness_hi.mean())
        chars = braille_style(brightness_hi, threshold=threshold)
        colors = apply_color(
            brightness_hi[::4, ::2][:char_rows, :char_cols],
            colors_lo[:char_rows, :char_cols],
            mode=args.color, background=args.background,
            custom_color=args.custom_color,
        )

    elif args.style == "edge":
        magnitude, direction, colors_raw, rows, cols_out = process_image_for_edge(
            img, cols=args.cols, ratio=args.ratio, invert=args.invert,
            char_aspect=char_aspect, char_pixel_width=char_pixel_width,
        )
        chars = edge_style(magnitude, direction)
        brightness = magnitude / magnitude.max() * 255 if magnitude.max() > 0 else magnitude
        colors = apply_color(
            brightness, colors_raw,
            mode=args.color, background=args.background,
            custom_color=args.custom_color,
        )

    elif args.style == "block":
        grid = process_image(img, cols=args.cols, ratio=args.ratio, invert=args.invert, char_aspect=char_aspect, char_pixel_width=char_pixel_width)
        dithered = apply_dither(grid.brightness, args.dither, levels=5, strength=args.dither_strength)
        chars = block_style(dithered)
        colors = apply_color(
            grid.brightness, grid.colors,
            mode=args.color, background=args.background,
            custom_color=args.custom_color,
        )

    elif args.style == "dot-cross":
        grid = process_image(img, cols=args.cols, ratio=args.ratio, invert=args.invert, char_aspect=char_aspect, char_pixel_width=char_pixel_width)
        dithered = apply_dither(grid.brightness, args.dither, levels=10, strength=args.dither_strength)
        chars = dot_cross_style(dithered)
        colors = apply_color(
            grid.brightness, grid.colors,
            mode=args.color, background=args.background,
            custom_color=args.custom_color,
        )

    elif args.style == "halftone":
        grid = process_image(img, cols=args.cols, ratio=args.ratio, invert=args.invert, char_aspect=char_aspect, char_pixel_width=char_pixel_width)
        dithered = apply_dither(grid.brightness, args.dither, levels=7, strength=args.dither_strength)
        chars = halftone_style(dithered)
        colors = apply_color(
            grid.brightness, grid.colors,
            mode=args.color, background=args.background,
            custom_color=args.custom_color,
        )

    elif args.style == "particles":
        grid = process_image(img, cols=args.cols, ratio=args.ratio, invert=args.invert, char_aspect=char_aspect, char_pixel_width=char_pixel_width)
        chars = particles_style(grid.brightness)
        colors = apply_color(
            grid.brightness, grid.colors,
            mode=args.color, background=args.background,
            custom_color=args.custom_color,
        )

    else:
        # classic + themed presets (claude-code, retro-art, terminal)
        # Presets use custom ramps; classic uses default
        if args.style in PRESETS:
            ramp = PRESETS[args.style]["ramp"]
        else:
            ramp = DEFAULT_RAMP
        grid = process_image(img, cols=args.cols, ratio=args.ratio, invert=args.invert, char_aspect=char_aspect, char_pixel_width=char_pixel_width)
        dithered = apply_dither(grid.brightness, args.dither, levels=len(ramp), strength=args.dither_strength)
        chars = classic_ascii(dithered, ramp=ramp)
        colors = apply_color(
            grid.brightness, grid.colors,
            mode=args.color, background=args.background,
            custom_color=args.custom_color,
        )

    # Ensure colors match char dimensions
    char_rows = len(chars)
    char_cols = len(chars[0]) if char_rows > 0 else 0
    colors = colors[:char_rows, :char_cols]
    return chars, colors


def convert_image(args) -> None:
    """Convert image to ASCII art."""
    img = load_image(args.input)
    # Capture post-crop aspect ratio for interactive renderer
    from core.pipeline import crop_to_ratio
    cropped = crop_to_ratio(img, args.ratio)
    args._source_aspect = cropped.size[1] / cropped.size[0]  # h/w
    chars, colors = _convert_with_style(args, img)
    input_name = os.path.basename(args.input)
    _do_export(args, chars, colors, input_name)


def convert_video(args) -> None:
    """Convert video to ASCII art frames."""
    from core.video_extract import extract_frames, check_opencv

    if not check_opencv():
        print(
            "Error: Video support requires opencv-python.\n"
            "Install with: pip install opencv-python-headless",
            file=sys.stderr,
        )
        sys.exit(1)

    input_name = os.path.basename(args.input)

    # For non-GIF/non-interactive/non-tsx exports, only need first frame
    if args.export and args.export not in ("gif", "interactive", "tsx"):
        first_frame = next(extract_frames(args.input, target_fps=args.fps), None)
        if first_frame is None:
            print("Error: No frames extracted from video.", file=sys.stderr)
            sys.exit(1)
        chars, colors = _convert_with_style(args, first_frame)
        _do_export(args, chars, colors, input_name)
        return

    # GIF or default (PNG preview + GIF): need all frames
    frames = []
    for frame_img in extract_frames(args.input, target_fps=args.fps):
        chars, colors = _convert_with_style(args, frame_img)
        frames.append((chars, colors))

    if not frames:
        print("Error: No frames extracted from video.", file=sys.stderr)
        sys.exit(1)

    # Default export: PNG preview of first frame + GIF if multiple frames
    fs = args.font_size
    source_aspect = getattr(args, '_source_aspect', None)
    if args.export == "interactive":
        path = export_interactive_html(
            frames, input_name,
            background=args.background, font_size=fs,
            mouse_mode=args.mouse_mode, hover_strength=args.hover_strength,
            area_size=args.area_size, spread=args.spread,
            animation=args.animation, filename=args.filename,
            source_aspect=source_aspect,
        )
        print(f"Exported: {path}")
    elif args.export == "tsx":
        path = export_react_component(
            frames, input_name,
            background=args.background, font_size=fs,
            mouse_mode=args.mouse_mode, hover_strength=args.hover_strength,
            area_size=args.area_size, spread=args.spread,
            animation=args.animation, filename=args.filename,
            source_aspect=source_aspect,
        )
        print(f"Exported: {path}")
    elif args.export is None:
        path = export_png(frames[0][0], frames[0][1], input_name,
                         background=args.background, font_size=fs, filename=args.filename)
        print(f"Preview (first frame): {path}")
        if len(frames) > 1:
            gif_path = export_gif(frames, input_name, background=args.background,
                                 font_size=fs, fps=args.fps)
            print(f"Animated: {gif_path}")
    else:
        # args.export == "gif"
        path = export_gif(frames, input_name, background=args.background,
                         font_size=fs, fps=args.fps, filename=args.filename)
        print(f"Exported: {path}")


def _figlet_to_grid(result: str) -> tuple[list[list[str]], int, int]:
    """Convert FIGlet string to padded 2D char grid. Returns (chars, rows, cols)."""
    lines = result.split("\n")
    chars = [list(line) for line in lines]
    rows = len(chars)
    cols = max(len(row) for row in chars) if rows > 0 else 0
    for row in chars:
        while len(row) < cols:
            row.append(" ")
    return chars, rows, cols


def convert_text(args) -> None:
    """Convert text to ASCII art banner."""
    if args.export in ("interactive", "tsx"):
        print("Error: Interactive/React export requires image or video input.", file=sys.stderr)
        sys.exit(1)
    result = render_text(args.input, font=args.font)
    input_name = args.input[:20].replace(" ", "_")
    chars, rows, cols = _figlet_to_grid(result)

    if args.export == "clipboard":
        if export_clipboard_text(chars):
            print("Copied to clipboard!")
        else:
            print(result)
    elif args.export in ("html", "svg", "png"):
        brightness = np.full((rows, cols), 255.0)
        pixel_colors = np.full((rows, cols, 3), 255, dtype=np.uint8)
        colors = apply_color(brightness, pixel_colors, mode=args.color,
                             background=args.background, custom_color=args.custom_color)

        fs = args.font_size
        if args.export == "html":
            path = export_html(chars, colors, input_name, background=args.background,
                              font_size=fs, filename=args.filename)
        elif args.export == "svg":
            path = export_svg(chars, colors, input_name, background=args.background,
                             font_size=fs, filename=args.filename)
        else:
            path = export_png(chars, colors, input_name, background=args.background,
                             font_size=fs, filename=args.filename)
        print(f"Exported: {path}")
    elif args.export == "txt":
        path = export_txt(chars, input_name, filename=args.filename)
        print(f"Exported: {path}")
    elif args.export == "md":
        path = export_md(chars, input_name, filename=args.filename)
        print(f"Exported: {path}")
    else:
        # Default: print to stdout and auto-copy to clipboard
        print(result)
        if export_clipboard_text(chars):
            print("(Copied to clipboard)")


def _do_export(args, chars, colors, input_name):
    """Handle export for image conversion."""
    fs = args.font_size
    source_aspect = getattr(args, '_source_aspect', None)
    if args.export == "interactive":
        path = export_interactive_html(
            [(chars, colors)], input_name,
            background=args.background, font_size=fs,
            mouse_mode=args.mouse_mode, hover_strength=args.hover_strength,
            area_size=args.area_size, spread=args.spread,
            animation=args.animation, filename=args.filename,
            source_aspect=source_aspect,
        )
        print(f"Exported: {path}")
    elif args.export == "tsx":
        path = export_react_component(
            [(chars, colors)], input_name,
            background=args.background, font_size=fs,
            mouse_mode=args.mouse_mode, hover_strength=args.hover_strength,
            area_size=args.area_size, spread=args.spread,
            animation=args.animation, filename=args.filename,
            source_aspect=source_aspect,
        )
        print(f"Exported: {path}")
    elif args.export == "txt":
        path = export_txt(chars, input_name, filename=args.filename)
        print(f"Exported: {path}")
    elif args.export == "md":
        path = export_md(chars, input_name, filename=args.filename)
        print(f"Exported: {path}")
    elif args.export == "html":
        path = export_html(chars, colors, input_name,
                          background=args.background, font_size=fs, filename=args.filename)
        print(f"Exported: {path}")
    elif args.export == "svg":
        path = export_svg(chars, colors, input_name, background=args.background,
                         font_size=fs, filename=args.filename)
        print(f"Exported: {path}")
    elif args.export == "clipboard":
        png_path = export_png(chars, colors, input_name, background=args.background,
                             font_size=fs)
        if export_clipboard_image(png_path):
            print(f"Copied to clipboard! (also saved: {png_path})")
        else:
            print(f"Clipboard failed. Saved: {png_path}")
    elif args.export == "png":
        path = export_png(chars, colors, input_name,
                         background=args.background, font_size=fs, filename=args.filename)
        print(f"Exported: {path}")
    else:
        # Default: PNG
        path = export_png(chars, colors, input_name,
                         background=args.background, font_size=fs, filename=args.filename)
        print(f"Preview: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert text, images, or video to ASCII art.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Core
    parser.add_argument("--input", "-i", required=True, help="Text string, image path, or video path")
    parser.add_argument("--type", "-t", choices=["text", "image", "video"],
                        help="Input type (auto-detected if omitted)")
    parser.add_argument("--style", "-s", choices=ALL_STYLES,
                        default="classic", help="Art style (default: classic)")
    parser.add_argument("--cols", "-c", type=int, default=0,
                        help="Output width in characters (default: auto, preserves original image size)")
    parser.add_argument("--random", action="store_true",
                        help="Randomize style, color, and dither")

    # Crop & size
    parser.add_argument("--ratio", choices=["original", "16:9", "4:3", "1:1", "3:4", "9:16"],
                        default="original", help="Aspect ratio crop (default: original)")

    # Color
    parser.add_argument("--color", choices=["grayscale", "original", "full", "matrix", "amber", "custom"],
                        default=None, help="Color mode (default: grayscale)")
    parser.add_argument("--custom-color", help="Hex color for custom mode (e.g. #ff6600)")
    parser.add_argument("--background", "-bg", choices=["dark", "light", "transparent"],
                        default="dark", help="Background theme (default: dark)")
    parser.add_argument("--invert", action="store_true", help="Invert brightness mapping")

    # Dither
    parser.add_argument("--dither", choices=["none", "floyd-steinberg", "bayer", "atkinson"],
                        default=None, help="Dithering algorithm (default: none)")
    parser.add_argument("--dither-strength", type=float, default=None,
                        help="Dither strength 0.0-1.0 (default: 0.8)")

    # Text only
    parser.add_argument("--font", choices=AVAILABLE_FONTS, default="standard",
                        help="FIGlet font for text mode (default: standard)")

    # Video only
    parser.add_argument("--fps", type=int, default=10,
                        help="Output frame rate for video (default: 10)")

    # Export
    parser.add_argument("--export", "-e",
                        choices=["terminal", "txt", "md", "html", "svg", "png", "gif",
                                 "clipboard", "interactive", "tsx"],
                        help="Export format (default: auto)")
    parser.add_argument("--filename", "-o", help="Custom output filename")
    parser.add_argument("--font-size", type=int, default=14,
                        help="Character size in pixels for image exports (default: 14)")

    # Interactive options
    parser.add_argument("--mouse-mode", choices=["push", "attract"],
                        default="push", help="Mouse interaction mode (default: push)")
    parser.add_argument("--hover-strength", type=int, default=35,
                        help="Mouse hover force 0-100 (default: 35)")
    parser.add_argument("--area-size", type=int, default=300,
                        help="Mouse interaction radius in pixels (default: 300)")
    parser.add_argument("--spread", type=float, default=1.1,
                        help="Interaction spread multiplier (default: 1.1)")
    parser.add_argument("--animation",
                        choices=["none", "noise-field", "intervals", "beam-sweep", "glitch", "crt"],
                        default="none", help="Animation preset (default: none)")

    args = parser.parse_args()

    # Random mode
    if args.random:
        combo = random.choice(RANDOM_COMBOS)
        args.style = combo["style"]
        args.color = combo["color"]
        args.dither = combo["dither"]
        print(f"Random mode: style={args.style}, color={args.color}, dither={args.dither}",
              file=sys.stderr)

    # Normalize "terminal" export to None (stdout)
    if args.export == "terminal":
        args.export = None

    # Interactive: cap auto-cols at 200 for canvas performance.
    # Rows are derived from cols + font-size char_aspect in the pipeline,
    # so everything stays proportionally linked.
    if args.export in ("interactive", "tsx") and args.cols == 0:
        args.cols = 160

    # Apply preset overrides (must come after random mode, before routing)
    _apply_preset(args)

    # Auto-detect type
    if not args.type:
        args.type = detect_type(args.input)

    # Route to handler
    if args.type == "text":
        convert_text(args)
    elif args.type == "image":
        convert_image(args)
    elif args.type == "video":
        convert_video(args)
    else:
        print(f"Error: Unknown type: {args.type}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
