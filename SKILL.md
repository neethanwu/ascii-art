---
name: ascii-art
description: Converts text, images, or video to ASCII art with multiple styles and export formats. Use when the user asks to create ASCII art, convert images/videos to text art, or mentions ascii-art, braille art, or block art.
---

# ASCII Art Converter

Convert text, images, or video to ASCII art with multiple styles and export formats.

## Setup

Before first use, run the environment setup (idempotent, <1s after first run):

```bash
bash {{SKILL_DIR}}/scripts/setup.sh
```

## Input Detection

Determine input type from the user's message:

1. **File path** → check extension: `.jpg/.jpeg/.png/.webp/.bmp/.tiff` → **image**, `.mp4/.webm/.avi/.mov/.mkv` → **video**, `.gif` → check if animated (video) or static (image)
2. **Pasted/attached image** → save to temp file → **image**
3. **Plain text** (no file, or file doesn't exist) → **text** (FIGlet banner)
4. **Nothing provided** → ask what they want to convert

## Options Prompt

After detecting input, parse the user's message for any pre-specified options (style, color, ratio, etc. — Claude can infer these from natural language). Then prompt for **all unspecified options** using `AskUserQuestion`.

- If user said "defaults" or "just do it" → skip prompting, use all defaults
- If user said "random" or "surprise me" → skip prompting, use `--random`
- If all options already specified → skip prompting

### AskUserQuestion format

Use `questions` array (max 4 per call, 3 options per question). If >4 unresolved questions, split into multiple calls. List ALL available choices with numbers in the `question` text. Show the top 3 as selectable options — the user can also type a number or name in the free-text field for any other choice.

Priority order — **image/video**: Style → Color → Export → Ratio → Background → Dither. **Text**: Font → Color → Export → Background.

Example question for Style:

```json
{
  "question": "Art style? 1.Classic 2.Braille 3.Block 4.Edge 5.Dot-cross 6.Halftone 7.Retro-art 8.Terminal",
  "header": "Style",
  "options": [
    { "label": "1. Classic", "description": "Traditional ASCII density ramp" },
    { "label": "2. Braille", "description": "Unicode braille dots — high detail" },
    { "label": "3. Block", "description": "Unicode block elements (█▓▒░)" }
  ],
  "multiSelect": false
}
```

Do NOT include an "Other" option — the SDK always shows a free-text input where users can type a number or name for unlisted choices. Keep option descriptions short. Put the default as option 1.

### Available options by type

**Image/video options:**

| Option | Choices | Default |
|--------|---------|---------|
| Style | classic, braille, block, edge, dot-cross, halftone, retro-art, terminal | classic |
| Color | grayscale, original, matrix, amber, custom (hex/named) | grayscale |
| Ratio | original, 16:9, 4:3, 1:1, 3:4, 9:16 | original |
| Background | dark, light, transparent | dark |
| Dither | none, floyd-steinberg, bayer, atkinson | none |
| Font size | 6-30 px | 14 |
| Export | png, html, svg, txt, md, clipboard (image default: png, video default: gif) | auto |

**Text options:**

| Option | Choices | Default |
|--------|---------|---------|
| Font | standard, doom, banner, slant, big, small, block, lean, mini, script, shadow, speed, ansi_shadow, ansi_regular | standard |
| Color | grayscale, original, matrix, amber, custom | grayscale |
| Background | dark, light, transparent | dark |
| Export | terminal (stdout), txt, md, png, html, svg, clipboard | terminal |

Note: Style (block, braille, etc.) only applies to image/video. Font only applies to text. "block" as a font and "block" as a style are different things — the agent should pick based on input type. For block-like text art, use `--font ansi_shadow` or `--font block`.

Custom colors: supports hex (`#ff6600`) or named colors (`coral`, `skyblue`, `gold`). Translate creative descriptions ("sunset vibes") to hex.

## Running the Conversion

```bash
{{SKILL_DIR}}/scripts/.venv/bin/python {{SKILL_DIR}}/scripts/convert.py \
  --input "<input>" \
  --type <text|image|video> \
  --style <style> \
  --color <color> \
  --background <background> \
  --dither <dither> \
  --export <format> \
  [--cols <number>] \
  [--invert] \
  [--random] \
  [--font <font_name>] \
  [--fps <number>] \
  [--custom-color "<hex or named color>"] \
  [--ratio <ratio>] \
  [--dither-strength <0.0-1.0>] \
  [--font-size <pixels>] \
  [--filename <custom_name>]
```

## Output

All exported files are saved to an `ascii/` folder in the current working directory (created automatically).

- **Text**: the script prints to stdout (and auto-copies to clipboard). Show the result in your response inside a markdown code block (triple backticks) to preserve exact spacing. Do NOT paste it as plain text — whitespace will break.
- **Image**: show file path and use Read tool to display inline if possible.
- **Video**: first frame PNG + animated GIF. Show file paths.

## Follow-up

After showing the result, offer to: try a different style/color, adjust settings (ratio, font size, dithering), export in another format, or try random mode. Remember the previous input path for re-runs.
