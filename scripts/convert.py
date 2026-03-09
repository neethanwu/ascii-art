#!/usr/bin/env python3
"""ASCII Art Converter — CLI entry point."""

import argparse
import random
import sys
import os

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
    RAMPS,
    DEFAULT_RAMP,
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
)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}
VIDEO_EXTS = {".mp4", ".webm", ".avi", ".mov", ".mkv"}

# Random mode: curated good combinations
RANDOM_COMBOS = [
    {"style": "classic", "color": "matrix", "dither": "none"},
    {"style": "classic", "color": "amber", "dither": "floyd-steinberg"},
    {"style": "braille", "color": "grayscale", "dither": "none"},
    {"style": "braille", "color": "matrix", "dither": "none"},
    {"style": "block", "color": "full", "dither": "none"},
    {"style": "block", "color": "grayscale", "dither": "bayer"},
    {"style": "classic", "color": "full", "dither": "atkinson"},
    {"style": "classic", "color": "grayscale", "dither": "floyd-steinberg"},
    {"style": "edge", "color": "grayscale", "dither": "none"},
    {"style": "edge", "color": "matrix", "dither": "none"},
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


def convert_image(args) -> None:
    """Convert image to ASCII art."""
    img = load_image(args.input)

    if args.style == "braille":
        brightness_hi, colors_lo, char_rows, char_cols = process_image_for_braille(
            img, cols=args.cols, ratio=args.ratio, invert=args.invert,
        )
        # Compute threshold (median brightness)
        threshold = float(brightness_hi.mean())
        chars = braille_style(brightness_hi, threshold=threshold)
        # Colors at char resolution
        colors = apply_color(
            brightness_hi[::4, ::2][:char_rows, :char_cols],
            colors_lo[:char_rows, :char_cols],
            mode=args.color, background=args.background,
            custom_color=args.custom_color,
        )

    elif args.style == "edge":
        magnitude, direction, colors_raw, rows, cols_out = process_image_for_edge(
            img, cols=args.cols, ratio=args.ratio, invert=args.invert,
        )
        chars = edge_style(magnitude, direction)
        # For edge mode, use simple brightness-based color
        brightness = magnitude / magnitude.max() * 255 if magnitude.max() > 0 else magnitude
        colors = apply_color(
            brightness, colors_raw,
            mode=args.color, background=args.background,
            custom_color=args.custom_color,
        )

    elif args.style == "block":
        grid = process_image(img, cols=args.cols, ratio=args.ratio, invert=args.invert)
        dithered = apply_dither(grid.brightness, args.dither, levels=5, strength=args.dither_strength)
        chars = block_style(dithered)
        colors = apply_color(
            grid.brightness, grid.colors,
            mode=args.color, background=args.background,
            custom_color=args.custom_color,
        )

    else:  # classic
        grid = process_image(img, cols=args.cols, ratio=args.ratio, invert=args.invert)
        ramp = DEFAULT_RAMP
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

    # Export
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

    frames = []
    for i, frame_img in enumerate(extract_frames(args.input, target_fps=args.fps)):
        if args.style == "braille":
            bh, cl, cr_count, cc = process_image_for_braille(
                frame_img, cols=args.cols, ratio=args.ratio, invert=args.invert,
            )
            threshold = float(bh.mean())
            chars = braille_style(bh, threshold=threshold)
            colors = apply_color(
                bh[::4, ::2][:cr_count, :cc], cl[:cr_count, :cc],
                mode=args.color, background=args.background,
                custom_color=args.custom_color,
            )
        elif args.style == "edge":
            mag, dirn, cr, rows, cols_out = process_image_for_edge(
                frame_img, cols=args.cols, ratio=args.ratio, invert=args.invert,
            )
            chars = edge_style(mag, dirn)
            brightness = mag / mag.max() * 255 if mag.max() > 0 else mag
            colors = apply_color(
                brightness, cr, mode=args.color, background=args.background,
                custom_color=args.custom_color,
            )
        elif args.style == "block":
            grid = process_image(frame_img, cols=args.cols, ratio=args.ratio, invert=args.invert)
            dithered = apply_dither(grid.brightness, args.dither, levels=5, strength=args.dither_strength)
            chars = block_style(dithered)
            colors = apply_color(
                grid.brightness, grid.colors, mode=args.color, background=args.background,
                custom_color=args.custom_color,
            )
        else:
            grid = process_image(frame_img, cols=args.cols, ratio=args.ratio, invert=args.invert)
            ramp = DEFAULT_RAMP
            dithered = apply_dither(grid.brightness, args.dither, levels=len(ramp), strength=args.dither_strength)
            chars = classic_ascii(dithered, ramp=ramp)
            colors = apply_color(
                grid.brightness, grid.colors, mode=args.color, background=args.background,
                custom_color=args.custom_color,
            )

        char_rows = len(chars)
        char_cols = len(chars[0]) if char_rows > 0 else 0
        colors = colors[:char_rows, :char_cols]
        frames.append((chars, colors))

    if not frames:
        print("Error: No frames extracted from video.", file=sys.stderr)
        sys.exit(1)

    input_name = os.path.basename(args.input)

    # Export
    if args.export == "gif":
        path = export_gif(frames, input_name, background=args.background, fps=args.fps, filename=args.filename)
        print(f"Exported: {path}")
    elif args.export == "txt":
        # Export first frame as txt + all frames in a folder
        path = export_txt(frames[0][0], input_name, filename=args.filename)
        print(f"Exported first frame: {path}")
        print(f"Total frames: {len(frames)}")
    elif args.export == "html":
        # Export first frame as HTML
        path = export_html(frames[0][0], frames[0][1], input_name,
                          background=args.background, filename=args.filename)
        print(f"Exported first frame: {path}")
    else:
        # Default: PNG preview of first frame
        path = export_png(frames[0][0], frames[0][1], input_name,
                         background=args.background, filename=args.filename)
        print(f"Preview (first frame): {path}")

        # Also export GIF if we have multiple frames
        if len(frames) > 1:
            gif_path = export_gif(frames, input_name, background=args.background, fps=args.fps)
            print(f"Animated: {gif_path}")


def convert_text(args) -> None:
    """Convert text to ASCII art banner."""
    result = render_text(args.input, font=args.font)

    if args.export == "clipboard":
        # Create simple char grid for clipboard
        lines = result.split("\n")
        if export_clipboard_text([list(line) for line in lines]):
            print("Copied to clipboard!")
        else:
            print(result)
    elif args.export in ("html", "svg", "png"):
        # Render text as image
        lines = result.split("\n")
        chars = [list(line) for line in lines]
        rows = len(chars)
        cols = max(len(row) for row in chars) if rows > 0 else 0
        # Pad rows to equal width
        for row in chars:
            while len(row) < cols:
                row.append(" ")

        import numpy as np
        # Simple white-on-black for text banners
        colors = np.full((rows, cols, 3), 255, dtype=np.uint8)
        if args.color == "matrix":
            colors[:, :, 0] = 0
            colors[:, :, 2] = 0
        elif args.color == "amber":
            colors[:, :, 0] = 255
            colors[:, :, 1] = 180
            colors[:, :, 2] = 0

        input_name = args.input[:20].replace(" ", "_")
        if args.export == "html":
            path = export_html(chars, colors, input_name, background=args.background, filename=args.filename)
        elif args.export == "svg":
            path = export_svg(chars, colors, input_name, filename=args.filename)
        else:
            path = export_png(chars, colors, input_name, background=args.background, font_size=14, filename=args.filename)
        print(f"Exported: {path}")
    elif args.export == "txt":
        input_name = args.input[:20].replace(" ", "_")
        lines = result.split("\n")
        chars = [list(line) for line in lines]
        path = export_txt(chars, input_name, filename=args.filename)
        print(f"Exported: {path}")
    else:
        # Default: print to stdout
        print(result)


def _do_export(args, chars, colors, input_name):
    """Handle export for image conversion."""
    if args.export == "txt":
        path = export_txt(chars, input_name, filename=args.filename)
        print(f"Exported: {path}")
    elif args.export == "html":
        path = export_html(chars, colors, input_name,
                          background=args.background, filename=args.filename)
        print(f"Exported: {path}")
    elif args.export == "svg":
        path = export_svg(chars, colors, input_name, filename=args.filename)
        print(f"Exported: {path}")
    elif args.export == "clipboard":
        png_path = export_png(chars, colors, input_name, background=args.background)
        if export_clipboard_image(png_path):
            print(f"Copied to clipboard! (also saved: {png_path})")
        else:
            print(f"Clipboard failed. Saved: {png_path}")
    elif args.export == "png":
        path = export_png(chars, colors, input_name,
                         background=args.background, filename=args.filename)
        print(f"Exported: {path}")
    else:
        # Default: PNG
        path = export_png(chars, colors, input_name,
                         background=args.background, filename=args.filename)
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
    parser.add_argument("--style", "-s", choices=["classic", "braille", "block", "edge"],
                        default="classic", help="Art style (default: classic)")
    parser.add_argument("--cols", "-c", type=int, default=80,
                        help="Output width in characters (default: 80)")
    parser.add_argument("--random", action="store_true",
                        help="Randomize style, color, and dither")

    # Crop & size
    parser.add_argument("--ratio", choices=["original", "16:9", "4:3", "1:1", "3:4", "9:16"],
                        default="original", help="Aspect ratio crop (default: original)")

    # Color
    parser.add_argument("--color", choices=["grayscale", "full", "matrix", "amber", "custom"],
                        default="grayscale", help="Color mode (default: grayscale)")
    parser.add_argument("--custom-color", help="Hex color for custom mode (e.g. #ff6600)")
    parser.add_argument("--background", "-bg", choices=["dark", "light"],
                        default="dark", help="Background theme (default: dark)")
    parser.add_argument("--invert", action="store_true", help="Invert brightness mapping")

    # Dither
    parser.add_argument("--dither", choices=["none", "floyd-steinberg", "bayer", "atkinson"],
                        default="none", help="Dithering algorithm (default: none)")
    parser.add_argument("--dither-strength", type=float, default=0.8,
                        help="Dither strength 0.0-1.0 (default: 0.8)")

    # Text only
    parser.add_argument("--font", choices=AVAILABLE_FONTS, default="standard",
                        help="FIGlet font for text mode (default: standard)")

    # Video only
    parser.add_argument("--fps", type=int, default=10,
                        help="Output frame rate for video (default: 10)")

    # Export
    parser.add_argument("--export", "-e",
                        choices=["txt", "html", "svg", "png", "gif", "clipboard"],
                        help="Export format (default: auto)")
    parser.add_argument("--filename", "-o", help="Custom output filename")

    args = parser.parse_args()

    # Random mode
    if args.random:
        combo = random.choice(RANDOM_COMBOS)
        args.style = combo["style"]
        args.color = combo["color"]
        args.dither = combo["dither"]
        print(f"Random mode: style={args.style}, color={args.color}, dither={args.dither}",
              file=sys.stderr)

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
