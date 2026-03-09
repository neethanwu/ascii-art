# ASCII Art Converter

A Claude Code skill that converts text, images, and video to ASCII art.

## Features

- **8 art styles**: classic, braille, block, edge, dot-cross, halftone, retro-art, terminal
- **5 color modes**: grayscale, full color, matrix green, amber, custom (hex or named colors)
- **3 dithering algorithms**: Floyd-Steinberg, Bayer, Atkinson
- **6 export formats**: txt, html, svg, png, gif, clipboard
- **3 background modes**: dark, light, transparent
- **Aspect ratio presets**: original, 16:9, 4:3, 1:1, 3:4, 9:16
- **Text input**: FIGlet banners with 12 font choices
- **Video input**: frame extraction with animated GIF export
- **Random mode**: curated style combinations for surprise results

## Install

```bash
# Add as a Claude Code skill
claude skill add https://github.com/yourname/ascii-gen
```

Or clone manually:

```bash
git clone https://github.com/yourname/ascii-gen ~/.claude/skills/ascii-gen
```

## Usage

Trigger with `/ascii` in Claude Code:

```
/ascii convert photo.jpg to braille
/ascii "Hello World" in doom font
/ascii video.mp4 in block style with matrix color
/ascii photo.png with transparent background
/ascii surprise me with photo.jpg
```

The skill parses natural language — no need to remember flags. Just describe what you want.

## How It Works

On first use, the skill automatically sets up a Python virtual environment and installs dependencies (Pillow, NumPy, pyfiglet). This takes ~10 seconds the first time and is instant after that.

The conversion pipeline:

1. **Input** — detect type (text, image, or video)
2. **Process** — downsample, crop to ratio, compute brightness
3. **Style** — map to characters using the chosen art style
4. **Color** — apply color mode (grayscale, full, matrix, etc.)
5. **Dither** — optionally apply dithering for texture
6. **Export** — render to the chosen format

## Art Styles

| Style | Description |
|-------|-------------|
| classic | Traditional ASCII density ramp (`@%#*+=-:. `) |
| braille | Unicode braille characters (2x4 dot grid per char) |
| block | Unicode block elements (`█▓▒░`) |
| edge | Sobel edge detection with directional characters |
| dot-cross | Dot/cross/star symbols for a stippled look |
| halftone | Varying-size dot characters simulating print halftone |
| retro-art | Block chars + amber color + Atkinson dithering (preset) |
| terminal | Classic ASCII + matrix green (preset) |

## Requirements

- Python 3.8+
- macOS or Linux
- Optional: OpenCV for video support (installed automatically if available)

## License

MIT
