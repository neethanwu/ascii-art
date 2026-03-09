---
name: ascii
description: Convert text, images, or video to ASCII art. Supports multiple art styles (classic, braille, block, edge), color modes, dithering, and export formats.
---

# ASCII Art Converter

Convert text, images, or video to ASCII art with multiple styles and export formats.

## Setup

Before first use, run the environment setup (idempotent, <1s after first run):

```bash
bash {{SKILL_DIR}}/scripts/setup.sh
```

## Input Detection

Determine what the user wants to convert:

1. **If the user provided a file path** → check the extension:
   - `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tiff` → **image**
   - `.gif` → check if animated (multiple frames) → **video** if animated, **image** if static
   - `.mp4`, `.webm`, `.avi`, `.mov`, `.mkv` → **video**
2. **If the user pasted/attached an image in conversation** → save it to a temp file, then treat as **image**
3. **If the user provided plain text** (no file path, or file doesn't exist) → **text** (FIGlet banner)
4. **If nothing provided** → ask: "What would you like to convert to ASCII art? You can provide text, an image path, or a video path."

## Smart Defaults

Apply these defaults. Only ask the user if they didn't specify and the choice significantly affects output:

| Option | Default | When to ask |
|--------|---------|-------------|
| Style | classic | Don't ask — user can request braille/block/edge |
| Columns | 80 | Don't ask — works for most terminals |
| Color | grayscale | Don't ask |
| Dither | none | Don't ask |
| Background | dark | Don't ask |
| Ratio | original | Don't ask |
| Font (text) | standard | Don't ask — user can specify |
| FPS (video) | 10 | Don't ask |
| Export | auto (text→stdout, image→png, video→gif) | Don't ask |

## Natural Language Parsing

Parse the user's message for preferences. Examples:

- "convert photo.jpg to braille" → style=braille
- "make it matrix green" → color=matrix
- "wider, 120 columns" → cols=120
- "use doom font" → font=doom
- "surprise me" or "random" → random mode
- "invert it" → invert=true
- "light background" → background=light
- "with dithering" → dither=floyd-steinberg
- "export as html" → export=html
- "copy to clipboard" → export=clipboard
- "16:9 ratio" → ratio=16:9

## Running the Conversion

Use the venv Python to run the converter:

```bash
{{SKILL_DIR}}/scripts/.venv/bin/python {{SKILL_DIR}}/scripts/convert.py \
  --input "<input>" \
  --type <text|image|video> \
  --style <classic|braille|block|edge> \
  --cols <number> \
  --color <grayscale|full|matrix|amber|custom> \
  --background <dark|light> \
  --dither <none|floyd-steinberg|bayer|atkinson> \
  --export <txt|html|svg|png|gif|clipboard> \
  [--invert] \
  [--random] \
  [--font <font_name>] \
  [--fps <number>] \
  [--custom-color "#hex"] \
  [--ratio <original|16:9|4:3|1:1|3:4|9:16>] \
  [--dither-strength <0.0-1.0>] \
  [--filename <custom_name>]
```

## Preview

After conversion:

- **Text input**: Print the FIGlet output directly to the user (it's already text)
- **Image input**: The converter outputs a PNG file. Show the file path and use the Read tool to display it inline if possible.
- **Video input**: First frame PNG + animated GIF. Show file paths.

## Follow-up

After showing the preview, offer:

> "Here's your ASCII art! Want me to:
> - Export in a different format? (txt, html, svg, png, gif, clipboard)
> - Try a different style? (classic, braille, block, edge)
> - Adjust settings? (wider/narrower, different color, add dithering)
> - Try random mode for a surprise?"

If the user asks for changes, re-run with updated parameters. Remember the previous input path so they don't need to re-specify it.

## Valid Options Reference

**Art Styles**: classic, braille, block, edge

**Color Modes**: grayscale, full, matrix, amber, custom

**Dither Algorithms**: none, floyd-steinberg, bayer, atkinson

**Aspect Ratios**: original, 16:9, 4:3, 1:1, 3:4, 9:16

**FIGlet Fonts**: standard, doom, banner, slant, big, small, block, lean, mini, script, shadow, speed

**Export Formats**: txt, html, svg, png, gif, clipboard

**Background**: dark, light
