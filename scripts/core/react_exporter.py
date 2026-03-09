"""Export ASCII art as a React .tsx component with embedded data."""

from pathlib import Path
from typing import Optional

import numpy as np

from .exporters import make_output_path
from .interactive_exporter import (
    _build_ascii_data,
    _read_template,
)

# Simplex noise as TypeScript for embedding in React component
_SIMPLEX_NOISE_TS = '''
const SIMPLEX_NOISE = (() => {
  const grad3 = [[1,1,0],[-1,1,0],[1,-1,0],[-1,-1,0],[1,0,1],[-1,0,1],[1,0,-1],[-1,0,-1],[0,1,1],[0,-1,1],[0,1,-1],[0,-1,-1]];
  const p = [151,160,137,91,90,15,131,13,201,95,96,53,194,233,7,225,140,36,103,30,69,142,8,99,37,240,21,10,23,190,6,148,247,120,234,75,0,26,197,62,94,252,219,203,117,35,11,32,57,177,33,88,237,149,56,87,174,20,125,136,171,168,68,175,74,165,71,134,139,48,27,166,77,146,158,231,83,111,229,122,60,211,133,230,220,105,92,41,55,46,245,40,244,102,143,54,65,25,63,161,1,216,80,73,209,76,132,187,208,89,18,169,200,196,135,130,116,188,159,86,164,100,109,198,173,186,3,64,52,217,226,250,124,123,5,202,38,147,118,126,255,82,85,212,207,206,59,227,47,16,58,17,182,189,28,42,223,183,170,213,119,248,152,2,44,154,163,70,221,153,101,155,167,43,172,9,129,22,39,253,19,98,108,110,79,113,224,232,178,185,112,104,218,246,97,228,251,34,242,193,238,210,144,12,191,179,162,241,81,51,145,235,249,14,239,107,49,192,214,31,181,199,106,157,184,84,204,176,115,121,50,45,127,4,150,254,138,236,205,93,222,114,67,29,24,72,243,141,128,195,78,66,215,61,156,180];
  const perm = new Uint8Array(512);
  for (let i = 0; i < 512; i++) perm[i] = p[i & 255];
  const F2 = 0.5 * (Math.sqrt(3) - 1);
  const G2 = (3 - Math.sqrt(3)) / 6;
  function dot(g: number[], x: number, y: number) { return g[0]*x + g[1]*y; }
  return function noise2D(xin: number, yin: number): number {
    const s = (xin+yin)*F2; const i = Math.floor(xin+s); const j = Math.floor(yin+s);
    const t = (i+j)*G2; const x0 = xin-(i-t); const y0 = yin-(j-t);
    const [i1, j1] = x0 > y0 ? [1,0] : [0,1];
    const x1=x0-i1+G2, y1=y0-j1+G2, x2=x0-1+2*G2, y2=y0-1+2*G2;
    const ii=i&255, jj=j&255;
    let t0=0.5-x0*x0-y0*y0, n0=0; if(t0>=0){t0*=t0; n0=t0*t0*dot(grad3[perm[ii+perm[jj]]%12],x0,y0);}
    let t1=0.5-x1*x1-y1*y1, n1=0; if(t1>=0){t1*=t1; n1=t1*t1*dot(grad3[perm[ii+i1+perm[jj+j1]]%12],x1,y1);}
    let t2=0.5-x2*x2-y2*y2, n2=0; if(t2>=0){t2*=t2; n2=t2*t2*dot(grad3[perm[ii+1+perm[jj+1]]%12],x2,y2);}
    return 70*(n0+n1+n2);
  };
})();
'''

_ANIMATION_PRESETS_TS = '''
const GLITCH_CHARS = ['\\u2588','\\u2593','\\u2592','\\u2591','#','@','%','&','*'];

type AnimStates = { x: Float32Array; y: Float32Array; vx: Float32Array; vy: Float32Array };
type AnimFrame = { chars: string[][]; colors: number[][][]; _opacity: Float32Array | null; _colorMod: Float32Array | null; _origChars: string[][] | null };

const ANIMATION_PRESETS: Record<string, (s: AnimStates, rows: number, cols: number, cw: number, ch: number, t: number, f: AnimFrame) => void> = {
  'noise-field': (states, rows, cols, _cw, _ch, time) => {
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      const idx = r * cols + c;
      states.x[idx] += SIMPLEX_NOISE(c*0.05, r*0.05+time*0.5) * 3;
      states.y[idx] += SIMPLEX_NOISE(c*0.05+100, r*0.05+time*0.5+100) * 3;
    }
  },
  'intervals': (_states, rows, cols, _cw, _ch, time, frame) => {
    if (!frame._opacity) frame._opacity = new Float32Array(rows * cols);
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      frame._opacity[r*cols+c] = 0.3 + 0.7*(0.5+0.5*Math.sin(c*0.1+r*0.05+time*2.0));
    }
  },
  'beam-sweep': (_states, rows, cols, _cw, _ch, time, frame) => {
    const beamWidth = Math.max(3, Math.floor(cols*0.05));
    const beamCenter = ((time%3)/3) * cols;
    if (!frame._colorMod) frame._colorMod = new Float32Array(rows*cols);
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      const dist = Math.abs(c-beamCenter);
      frame._colorMod[r*cols+c] = dist < beamWidth ? 1.0+0.5*(1-dist/beamWidth) : 1.0;
    }
  },
  'glitch': (states, rows, cols, charW, _ch, _time, frame) => {
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      if (frame.chars[r][c]===' ') continue;
      if (Math.random()<0.002) {
        if (!frame._origChars) frame._origChars = frame.chars.map(row => row.slice());
        frame.chars[r][c] = GLITCH_CHARS[Math.floor(Math.random()*GLITCH_CHARS.length)];
      }
    }
    for (let r = 0; r < rows; r++) if (Math.random()<0.01) {
      const shift = (Math.floor(Math.random()*5)-2) || 1;
      for (let c = 0; c < cols; c++) states.x[r*cols+c] += shift*charW*0.5;
    }
  },
  'crt': (_states, rows, cols, _cw, _ch, _time, frame) => {
    if (!frame._colorMod) frame._colorMod = new Float32Array(rows*cols);
    const cR = rows*0.5, cC = cols*0.5;
    for (let r = 0; r < rows; r++) {
      const scanline = r%2===0 ? 1.0 : 0.7;
      for (let c = 0; c < cols; c++) {
        const dr=(r-cR)/cR, dc=(c-cC)/cC;
        frame._colorMod[r*cols+c] = scanline * (1.0-0.2*(dr*dr+dc*dc));
        if (c>0 && c<cols-1) {
          const rgb=frame.colors[r][c], rL=frame.colors[r][c-1], bR=frame.colors[r][c+1];
          rgb[0]=Math.min(255,Math.floor(rgb[0]*0.7+rL[0]*0.3));
          rgb[2]=Math.min(255,Math.floor(rgb[2]*0.7+bR[2]*0.3));
        }
      }
    }
  },
};
'''


def export_react_component(
    frames: list[tuple[list[list[str]], np.ndarray]],
    input_name: str,
    background: str = "dark",
    font_size: int = 14,
    mouse_mode: str = "push",
    hover_strength: int = 35,
    area_size: int = 300,
    spread: float = 1.1,
    animation: str = "none",
    filename: Optional[str] = None,
    source_aspect: Optional[float] = None,
) -> str:
    """Generate a self-contained React .tsx component file.

    Returns:
        Path to the generated .tsx file.
    """
    import sys

    if not frames:
        raise ValueError("No frames to export")

    if len(frames) > 60:
        print(
            f"Warning: Truncating {len(frames)} frames to 60 for React export.",
            file=sys.stderr,
        )
        frames = frames[:60]

    first_chars = frames[0][0]
    rows = len(first_chars)
    cols = max(len(row) for row in first_chars) if rows > 0 else 0

    # Pad frames
    padded_frames = []
    for chars, colors in frames:
        padded_chars = []
        for row in chars:
            padded = list(row)
            while len(padded) < cols:
                padded.append(" ")
            padded_chars.append(padded[:cols])
        c = colors[:rows, :cols]
        padded_frames.append((padded_chars, c))

    config = {
        "background": background,
        "fontSize": font_size,
        "mouseMode": mouse_mode,
        "hoverStrength": hover_strength,
        "areaSize": area_size,
        "spread": spread,
        "animation": animation,
    }
    if source_aspect is not None:
        config["sourceAspect"] = round(source_aspect, 6)

    ascii_data_json = _build_ascii_data(padded_frames, rows, cols, config)

    # Read template and inject data
    template = _read_template("react_template.tsx")

    # Replace placeholders
    data_section = f"const ASCII_DATA = {ascii_data_json};"

    # Include simplex noise if any animation needs it
    needs_noise = animation in ("noise-field",)
    simplex_section = _SIMPLEX_NOISE_TS if needs_noise else "const SIMPLEX_NOISE = (_x: number, _y: number) => 0;"

    # Include animation presets if animation is not none
    anim_section = _ANIMATION_PRESETS_TS if animation != "none" else "const ANIMATION_PRESETS: Record<string, never> = {};"

    tsx = template.replace(
        "// __ASCII_DATA_PLACEHOLDER__", data_section
    ).replace(
        "// __SIMPLEX_NOISE_PLACEHOLDER__", simplex_section
    ).replace(
        "// __ANIMATION_PRESETS_PLACEHOLDER__", anim_section
    )

    path = make_output_path(input_name, "tsx", filename)
    Path(path).write_text(tsx, encoding="utf-8")
    return path
