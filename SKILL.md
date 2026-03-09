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

After detecting the input, **always ask the user to configure their options** using a single `AskUserQuestion` call with a `questions` array. Each question becomes a tab the user can fill out. Use type-specific questions.

**AskUserQuestion constraints**: 1-4 questions per call, 2-4 options per question. Use "Other" option for free-text input where the choices exceed 4.

### For image input (4 questions):

```json
{
  "questions": [
    {
      "question": "What art style do you want?",
      "header": "Style",
      "options": [
        { "label": "Classic", "description": "Traditional ASCII density ramp (@%#*+=-:. )" },
        { "label": "Braille", "description": "Unicode braille dots — high detail, smooth look" },
        { "label": "Block", "description": "Unicode block elements (█▓▒░) — bold, chunky" },
        { "label": "Other", "description": "Type: edge, dot-cross, halftone, retro-art, or terminal" }
      ],
      "multiSelect": false
    },
    {
      "question": "What color mode?",
      "header": "Color",
      "options": [
        { "label": "Grayscale", "description": "White on dark — clean, classic look" },
        { "label": "Full color", "description": "Preserve original image colors" },
        { "label": "Matrix", "description": "Green on black — hacker terminal vibes" },
        { "label": "Other", "description": "Type: amber, or custom color (e.g. coral, #ff6600)" }
      ],
      "multiSelect": false
    },
    {
      "question": "What aspect ratio?",
      "header": "Ratio",
      "options": [
        { "label": "Original", "description": "Keep the image's original proportions" },
        { "label": "16:9", "description": "Widescreen crop" },
        { "label": "1:1", "description": "Square crop" },
        { "label": "Other", "description": "Type: 4:3, 3:4, or 9:16" }
      ],
      "multiSelect": false
    },
    {
      "question": "What export format?",
      "header": "Export",
      "options": [
        { "label": "PNG", "description": "Image file — best for sharing (default)" },
        { "label": "HTML", "description": "Colored text in a web page" },
        { "label": "SVG", "description": "Scalable vector — crisp at any size" },
        { "label": "Other", "description": "Type: txt, clipboard" }
      ],
      "multiSelect": false
    }
  ]
}
```

### For text input (3 questions):

```json
{
  "questions": [
    {
      "question": "What font style for your banner?",
      "header": "Font",
      "options": [
        { "label": "Standard", "description": "Clean, readable default font" },
        { "label": "Doom", "description": "Bold, dramatic block letters" },
        { "label": "Slant", "description": "Italic-style angled text" },
        { "label": "Other", "description": "Type: banner, big, small, block, lean, mini, script, shadow, speed" }
      ],
      "multiSelect": false
    },
    {
      "question": "What color mode?",
      "header": "Color",
      "options": [
        { "label": "Grayscale", "description": "White on dark — classic terminal look" },
        { "label": "Matrix", "description": "Green on black — hacker vibes" },
        { "label": "Amber", "description": "Warm orange on dark — retro monitor" },
        { "label": "Other", "description": "Type: full, or custom color (e.g. coral, #ff6600)" }
      ],
      "multiSelect": false
    },
    {
      "question": "What export format?",
      "header": "Export",
      "options": [
        { "label": "Terminal", "description": "Print directly to stdout (default)" },
        { "label": "TXT", "description": "Save as plain text file" },
        { "label": "PNG", "description": "Render as image file" },
        { "label": "Other", "description": "Type: html, svg, clipboard" }
      ],
      "multiSelect": false
    }
  ]
}
```

### For video input (4 questions):

```json
{
  "questions": [
    {
      "question": "What art style do you want?",
      "header": "Style",
      "options": [
        { "label": "Classic", "description": "Traditional ASCII density ramp" },
        { "label": "Braille", "description": "Unicode braille dots — high detail" },
        { "label": "Block", "description": "Unicode block elements — bold, chunky" },
        { "label": "Other", "description": "Type: edge, dot-cross, halftone, retro-art, or terminal" }
      ],
      "multiSelect": false
    },
    {
      "question": "What color mode?",
      "header": "Color",
      "options": [
        { "label": "Grayscale", "description": "White on dark — clean, classic look" },
        { "label": "Full color", "description": "Preserve original video colors" },
        { "label": "Matrix", "description": "Green on black — hacker terminal vibes" },
        { "label": "Other", "description": "Type: amber, or custom color" }
      ],
      "multiSelect": false
    },
    {
      "question": "What aspect ratio?",
      "header": "Ratio",
      "options": [
        { "label": "Original", "description": "Keep the video's original proportions" },
        { "label": "16:9", "description": "Widescreen crop" },
        { "label": "1:1", "description": "Square crop" },
        { "label": "Other", "description": "Type: 4:3, 3:4, or 9:16" }
      ],
      "multiSelect": false
    },
    {
      "question": "What export format?",
      "header": "Export",
      "options": [
        { "label": "GIF", "description": "Animated ASCII art (default)" },
        { "label": "PNG", "description": "First frame as image" },
        { "label": "HTML", "description": "First frame as colored web page" },
        { "label": "Other", "description": "Type: svg, txt" }
      ],
      "multiSelect": false
    }
  ]
}
```

### Rules

- If the user already specified an option in their message (via natural language parsing), pre-select it and skip that question
- If all options are already specified or user says "defaults" / "just do it", skip the prompt entirely
- If user says "random" or "surprise me", skip the prompt and use `--random` flag
- When user selects "Other", use their typed text to determine the value
- For options not covered by questions (dither, font-size, invert), use defaults. The user can request these in follow-up.
- Map selected labels to CLI flags: "Classic" → `--style classic`, "Full color" → `--color full`, "Terminal" → no `--export` flag (stdout), etc.

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

## Output

All exported files are saved to an `ascii/` folder in the current working directory (created automatically if it doesn't exist).

After conversion:

- **Text input**: Print the FIGlet output directly to the user (it's already text). If exported, show the file path.
- **Image input**: The converter outputs a file to `ascii/`. Show the file path and use the Read tool to display it inline if possible.
- **Video input**: First frame PNG + animated GIF saved to `ascii/`. Show file paths.

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
