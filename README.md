# ASCII Art Converter

An agent skill that converts text, images, and video to ASCII art. Works with any AI coding agent that supports the skill/tool format.

## Features

- **9 art styles**: classic, braille, block, edge, dot-cross, halftone, particles, retro-art, terminal
- **5 color modes**: grayscale, original (full RGB), matrix green, amber, custom (hex or named colors)
- **3 dithering algorithms**: Floyd-Steinberg, Bayer, Atkinson
- **9 export formats**: txt, md, html, svg, png, gif, clipboard, interactive (HTML+JS), tsx (React component)
- **3 background modes**: dark, light, transparent
- **Aspect ratio presets**: original, 16:9, 4:3, 1:1, 3:4, 9:16 (center-crop)
- **Adjustable character size**: `--font-size` controls density in image exports
- **Auto-sizing**: output matches original image dimensions by default
- **Text input**: FIGlet banners with 14 font choices (including ansi_shadow for block-style text)
- **Interactive mode**: canvas-based renderer with spring physics, mouse interaction (push/attract), and 5 animation presets
- **5 animation presets**: noise-field, intervals, beam-sweep, glitch, crt
- **React component**: self-contained `.tsx` with embedded data, SSR-safe, zero dependencies
- **Video input**: frame extraction with animated GIF or interactive export
- **Random mode**: curated style combinations for surprise results

## Install

```bash
npx skills add https://github.com/neethanwu/ascii-art --skill ascii-art
```

Or clone manually:

```bash
git clone https://github.com/neethanwu/ascii-art.git ~/.claude/skills/ascii-art
```

Optionally pre-install dependencies (otherwise runs automatically on first use):

```bash
bash ~/.claude/skills/ascii-art/scripts/setup.sh
```

The skill is defined in `SKILL.md` — any agent that reads skill files can use it.

## Usage

Trigger with `/ascii-art` in your agent:

```
/ascii-art convert photo.jpg to braille
/ascii-art "Hello World" in doom font
/ascii-art "SKILLS" in ansi_shadow font
/ascii-art video.mp4 in block style with matrix color
/ascii-art photo.png with transparent background
/ascii-art surprise me with photo.jpg
/ascii-art photo.jpg as interactive with glitch animation
/ascii-art photo.png as react component with crt effect
```

The skill parses natural language and presents all options interactively — just describe what you want, pick your settings, or reply "defaults" to go fast.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| Style | classic | Art style for images/video: classic, braille, block, edge, dot-cross, halftone, particles, retro-art, terminal |
| Font | standard | FIGlet font for text: standard, doom, banner, slant, big, small, block, lean, mini, script, shadow, speed, ansi_shadow, ansi_regular |
| Color | grayscale | Color mode: grayscale, original, matrix, amber, custom |
| Background | dark | Background: dark, light, transparent |
| Ratio | original | Aspect ratio crop: original, 16:9, 4:3, 1:1, 3:4, 9:16 |
| Font size | 14 | Character size in pixels for image exports (bigger = larger chars, smaller = denser) |
| Columns | auto (max 160 for interactive/tsx) | Output width in characters (auto preserves original image size) |
| Dither | none | Dithering: none, floyd-steinberg, bayer, atkinson |
| Export | auto (text→stdout, image→png, video→gif) | Format: txt, md, html, svg, png, gif, clipboard, interactive, tsx |
| Mouse mode | push | Mouse interaction for interactive/tsx: push, attract |
| Animation | none | Animation preset for interactive/tsx: none, noise-field, intervals, beam-sweep, glitch, crt |

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
| particles | Sparse scattered dots — darker areas denser, lighter areas empty |
| retro-art | Block chars + amber color + Atkinson dithering (preset) |
| terminal | Classic ASCII + matrix green (preset) |

## Requirements

- Python 3.8+
- macOS or Linux
- Optional: OpenCV for video support (installed automatically if available)

## License

MIT
