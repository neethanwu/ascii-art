---
name: ascii-art
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

## Options Prompt

After detecting the input, **always ask the user to configure their options** using a single AskUserQuestion call. Pre-fill any options the user already specified in their message (via natural language parsing below), and present the rest with defaults highlighted.

Use this format:

```
Converting [filename/text] ([type]) to ASCII art.

Pick your options (or reply "defaults" for all defaults, "random" for a surprise):

1. Style: classic* | braille | block | edge | dot-cross | halftone | retro-art | terminal
2. Color: grayscale* | full | matrix | amber | custom
3. Background: dark* | light | transparent
4. Ratio: original* | 16:9 | 4:3 | 1:1 | 3:4 | 9:16
5. Font size: 14* (bigger = larger chars, smaller = denser art)
6. Dither: none* | floyd-steinberg | bayer | atkinson
7. Export: png* | html | svg | txt | gif | clipboard
[8. Font (text only): standard* | doom | banner | slant | big | small | block | lean | mini | script | shadow | speed]
[9. FPS (video only): 10*]

* = default. Just list the numbers you want to change, e.g. "1. braille 2. matrix" or "defaults".
```

Rules:
- Mark the default with `*` for each option
- If the user already specified an option in their original message, show it as pre-selected with a checkmark: e.g. `1. Style: ~~classic~~ braille ✓ (from your request)`
- Only show option 8 (Font) for text input and option 9 (FPS) for video input
- If the user replies "defaults" or "default", use all defaults immediately
- If the user replies "random" or "surprise me", use `--random` flag
- If the user replies with partial changes like "1. braille 3. transparent", apply those and use defaults for the rest
- Accept flexible response formats — numbered, comma-separated, or natural language like "braille with matrix color"

## Natural Language Parsing

When parsing the user's original message, detect any pre-specified options:

- "convert photo.jpg to braille" → style=braille
- "halftone style" → style=halftone
- "dot cross look" → style=dot-cross
- "retro art style" → style=retro-art
- "make it matrix green" → color=matrix
- "coral colored" → color=custom, custom_color=coral
- "sunset vibes" → color=custom, custom_color=#ff6347 (translate creative descriptions to hex)
- "wider, 120 columns" → cols=120
- "use doom font" → font=doom
- "surprise me" or "random" → skip options, use random mode
- "invert it" → invert=true
- "light background" → background=light
- "transparent background" or "no background" → background=transparent
- "with dithering" → dither=floyd-steinberg
- "export as html" → export=html
- "copy to clipboard" → export=clipboard
- "16:9 ratio" → ratio=16:9
- "bigger characters" or "larger text" → font-size=20
- "denser" or "more detail" → font-size=8
- "defaults" or "just do it" → skip options prompt, use all defaults

## Running the Conversion

Use the venv Python to run the converter:

```bash
{{SKILL_DIR}}/scripts/.venv/bin/python {{SKILL_DIR}}/scripts/convert.py \
  --input "<input>" \
  --type <text|image|video> \
  --style <classic|braille|block|edge|dot-cross|halftone|retro-art|terminal> \
  --cols <number> \
  --color <grayscale|full|matrix|amber|custom> \
  --background <dark|light|transparent> \
  --dither <none|floyd-steinberg|bayer|atkinson> \
  --export <txt|html|svg|png|gif|clipboard> \
  [--invert] \
  [--random] \
  [--font <font_name>] \
  [--fps <number>] \
  [--custom-color "#hex or named color"] \
  [--ratio <original|16:9|4:3|1:1|3:4|9:16>] \
  [--dither-strength <0.0-1.0>] \
  [--font-size <pixels>] \
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
> - Try a different style or color?
> - Adjust settings? (ratio, font size, dithering, etc.)
> - Export in another format? (txt, html, svg, png, gif, clipboard)
> - Try random mode for a surprise?"

If the user asks for changes, re-run with updated parameters. Remember the previous input path so they don't need to re-specify it.

## Valid Options Reference

**Art Styles**: classic, braille, block, edge, dot-cross, halftone, retro-art, terminal

**Color Modes**: grayscale, full, matrix, amber, custom

**Custom Colors**: Supports hex (`#ff6600`) or named colors (`coral`, `skyblue`, `gold`, `hotpink`, etc.). When users describe colors creatively (e.g., "sunset vibes", "ocean blue", "forest green"), translate to an appropriate hex value and pass it as `--custom-color`.

**Dither Algorithms**: none, floyd-steinberg, bayer, atkinson

**Aspect Ratios**: original, 16:9, 4:3, 1:1, 3:4, 9:16

**Font Size**: Default 14px. Range 6-30. Bigger = larger characters, smaller = denser art with more detail.

**FIGlet Fonts**: standard, doom, banner, slant, big, small, block, lean, mini, script, shadow, speed

**Export Formats**: txt, html, svg, png, gif, clipboard

**Background**: dark, light, transparent
