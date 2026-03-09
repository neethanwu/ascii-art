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

After detecting the input and parsing the user's message for pre-specified options, prompt the user for any **remaining** options using `AskUserQuestion`.

**AskUserQuestion constraints**: 1-4 questions per call, 2-4 options per question.

### Strategy

1. **Parse first** — extract any options the user already specified via natural language (see Natural Language Parsing section)
2. **Build question list** — include ALL questions for the input type, skipping only options the user **explicitly** specified in their message
3. **Always prompt** — never silently apply defaults. Every unspecified option must be presented to the user for confirmation. The only exceptions:
   - User explicitly said "defaults" or "just do it" → use all defaults, skip prompting
   - User explicitly said "random" or "surprise me" → skip prompting, use `--random`
4. **Batch into calls** — if ≤4 questions remain, use one `AskUserQuestion` call. If >4, split across multiple calls (ask the most impactful ones first: style, color, export).

### Question Templates

Pick from these templates based on input type. Include all questions except those the user explicitly specified. The first option in each question is always the default — the user can simply confirm to accept it.

**Style** (image/video only):
```json
{
  "question": "What art style? All options: 1.classic 2.braille 3.block 4.edge 5.dot-cross 6.halftone 7.retro-art 8.terminal",
  "header": "Style",
  "options": [
    { "label": "Classic", "description": "Traditional ASCII density ramp (@%#*+=-:. )" },
    { "label": "Braille", "description": "Unicode braille dots — high detail, smooth" },
    { "label": "Block", "description": "Unicode block elements (█▓▒░) — bold, chunky" },
    { "label": "Other", "description": "Type a number or name: 4.edge 5.dot-cross 6.halftone 7.retro-art 8.terminal" }
  ],
  "multiSelect": false
}
```

**Color** (all types):
```json
{
  "question": "What color mode? All options: 1.grayscale 2.full 3.matrix 4.amber 5.custom",
  "header": "Color",
  "options": [
    { "label": "Grayscale", "description": "White on dark — clean, classic look" },
    { "label": "Full color", "description": "Preserve original colors from source" },
    { "label": "Matrix", "description": "Green on black — hacker terminal vibes" },
    { "label": "Other", "description": "Type: 4.amber, or 5.custom with a color name/hex (e.g. coral, #ff6600)" }
  ],
  "multiSelect": false
}
```

**Ratio** (image/video only):
```json
{
  "question": "What aspect ratio? All options: 1.original 2.16:9 3.4:3 4.1:1 5.3:4 6.9:16",
  "header": "Ratio",
  "options": [
    { "label": "Original", "description": "Keep the original proportions" },
    { "label": "16:9", "description": "Widescreen crop (landscape)" },
    { "label": "1:1", "description": "Square center crop" },
    { "label": "Other", "description": "Type a number or name: 3.4:3 5.3:4 6.9:16" }
  ],
  "multiSelect": false
}
```

**Background** (all types):
```json
{
  "question": "What background?",
  "header": "Background",
  "options": [
    { "label": "Dark", "description": "Black background — default, works best for most styles" },
    { "label": "Light", "description": "White background — good for printing or light UIs" },
    { "label": "Transparent", "description": "No background — for overlaying on other content" }
  ],
  "multiSelect": false
}
```

**Export — image**:
```json
{
  "question": "What export format? All options: 1.png 2.html 3.svg 4.txt 5.clipboard",
  "header": "Export",
  "options": [
    { "label": "PNG", "description": "Image file — best for sharing (default)" },
    { "label": "HTML", "description": "Colored characters in a web page" },
    { "label": "SVG", "description": "Scalable vector — crisp at any size" },
    { "label": "Other", "description": "Type: 4.txt (plain text) or 5.clipboard (copy to clipboard)" }
  ],
  "multiSelect": false
}
```

**Export — text**:
```json
{
  "question": "What export format? All options: 1.terminal 2.txt 3.png 4.html 5.svg 6.clipboard",
  "header": "Export",
  "options": [
    { "label": "Terminal", "description": "Print to stdout — instant preview (default)" },
    { "label": "TXT", "description": "Save as plain text file" },
    { "label": "PNG", "description": "Render as image file" },
    { "label": "Other", "description": "Type: 4.html 5.svg 6.clipboard" }
  ],
  "multiSelect": false
}
```

**Export — video**:
```json
{
  "question": "What export format? All options: 1.gif 2.png 3.html 4.svg 5.txt",
  "header": "Export",
  "options": [
    { "label": "GIF", "description": "Animated ASCII art (default)" },
    { "label": "PNG", "description": "First frame as static image" },
    { "label": "HTML", "description": "First frame as colored web page" },
    { "label": "Other", "description": "Type: 4.svg 5.txt" }
  ],
  "multiSelect": false
}
```

**Font** (text only):
```json
{
  "question": "What font? All options: 1.standard 2.doom 3.banner 4.slant 5.big 6.small 7.block 8.lean 9.mini 10.script 11.shadow 12.speed",
  "header": "Font",
  "options": [
    { "label": "Standard", "description": "Clean, readable default font" },
    { "label": "Doom", "description": "Bold, dramatic block letters" },
    { "label": "Slant", "description": "Italic-style angled text" },
    { "label": "Other", "description": "Type a number or name: 3.banner 4-12 see question above" }
  ],
  "multiSelect": false
}
```

**Dither** (image/video only):
```json
{
  "question": "What dithering? Adds texture/grain to the output.",
  "header": "Dither",
  "options": [
    { "label": "None", "description": "No dithering — clean output (default)" },
    { "label": "Floyd-Steinberg", "description": "Error diffusion — natural, organic texture" },
    { "label": "Bayer", "description": "Ordered pattern — retro, grid-like texture" },
    { "label": "Atkinson", "description": "Classic Mac dithering — high contrast, sharp" }
  ],
  "multiSelect": false
}
```

### Priority Order

When building the question list, prioritize in this order (most impactful first):

**Image/video**: Style → Color → Export → Ratio → Background → Dither
**Text**: Font → Color → Export → Background

If >4 questions remain after filtering out pre-specified options, split into two calls:
- **Call 1**: first 4 questions (highest priority)
- **Call 2**: remaining questions

### Handling "Other" Responses

When the user selects "Other" and types free text:
- If they type a number (e.g. "4"), map it to the numbered option in the question text
- If they type a name (e.g. "edge", "amber"), use it directly
- If they type a custom color (e.g. "coral", "#ff6600"), set `--color custom --custom-color <value>`

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
