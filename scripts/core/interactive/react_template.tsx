'use client';

import { useRef, useEffect } from 'react';

// --- Types ---

interface AsciiArtProps {
  width?: number | string;
  height?: number | string;
  className?: string;
  style?: React.CSSProperties;
  interactive?: boolean;
  mouseMode?: 'push' | 'attract';
  hoverStrength?: number;
  areaSize?: number;
  spread?: number;
  animation?: 'none' | 'noise-field' | 'intervals' | 'beam-sweep' | 'glitch' | 'crt';
  onReady?: () => void;
}

// --- Embedded Data ---
// __ASCII_DATA_PLACEHOLDER__

// --- Simplex Noise ---
// __SIMPLEX_NOISE_PLACEHOLDER__

// --- Constants ---
const STIFFNESS = 0.08;
const DAMPING = 0.85;
const SETTLE_THRESHOLD = 0.01;

// --- Helpers ---

function decodeColors(base64: string, rows: number, cols: number): number[][][] {
  const bin = atob(base64);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  const result: number[][][] = new Array(rows);
  for (let r = 0; r < rows; r++) {
    result[r] = new Array(cols);
    for (let c = 0; c < cols; c++) {
      const idx = (r * cols + c) * 3;
      result[r][c] = [arr[idx] || 0, arr[idx + 1] || 0, arr[idx + 2] || 0];
    }
  }
  return result;
}

function parseFrame(frame: { chars: string; colors: string }, rows: number, cols: number) {
  const charRows = frame.chars.split('\n');
  const chars: string[][] = new Array(rows);
  for (let r = 0; r < rows; r++) {
    const line = charRows[r] || '';
    chars[r] = new Array(cols);
    for (let c = 0; c < cols; c++) {
      chars[r][c] = c < line.length ? line[c] : ' ';
    }
  }
  const colors = decodeColors(frame.colors, rows, cols);
  return { chars, colors, _opacity: null as Float32Array | null, _colorMod: null as Float32Array | null, _origChars: null as string[][] | null };
}

type ParsedFrame = ReturnType<typeof parseFrame>;

// --- Animation Presets ---
// __ANIMATION_PRESETS_PLACEHOLDER__

// --- Component ---

export function AsciiArt({
  width = '100%',
  height = 'auto',
  className,
  style,
  interactive = true,
  mouseMode,
  hoverStrength,
  areaSize,
  spread,
  animation,
  onReady,
}: AsciiArtProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const runningRef = useRef(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const config = {
      ...ASCII_DATA.config,
      ...(mouseMode !== undefined && { mouseMode }),
      ...(hoverStrength !== undefined && { hoverStrength }),
      ...(areaSize !== undefined && { areaSize }),
      ...(spread !== undefined && { spread }),
      ...(animation !== undefined && { animation }),
    };

    const fontSize = config.fontSize || 14;
    const font = fontSize + 'px monospace';
    ctx.font = font;
    ctx.textBaseline = 'top';

    const metrics = ctx.measureText('M');
    const charW = metrics.width;
    let charH = (metrics.actualBoundingBoxAscent || fontSize * 0.8) +
                (metrics.actualBoundingBoxDescent || fontSize * 0.2);
    charH = Math.ceil(charH * 1.1);

    const { rows, cols } = ASCII_DATA;
    const parsedFrames: ParsedFrame[] = ASCII_DATA.frames.map(
      (f: { chars: string; colors: string }) => parseFrame(f, rows, cols)
    );

    // Physics state
    const count = rows * cols;
    const states = {
      x: new Float32Array(count),
      y: new Float32Array(count),
      vx: new Float32Array(count),
      vy: new Float32Array(count),
    };

    // Mouse state
    let mouseX = -9999, mouseY = -9999, mouseActive = false;
    let frameIndex = 0;
    const startTime = performance.now();

    const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

    // Canvas sizing
    const naturalW = cols * charW;
    const naturalH = rows * charH;

    function resize() {
      const container = canvas!.parentElement;
      if (!container) return;
      const containerW = container.clientWidth;
      const scale = Math.min(1, containerW / naturalW);
      canvas!.width = Math.floor(naturalW * scale);
      canvas!.height = Math.floor(naturalH * scale);
      return scale;
    }

    let scale = resize() || 1;

    // Look up animation
    const animName = config.animation || 'none';
    let animFn: ((s: typeof states, r: number, c: number, cw: number, ch: number, t: number, f: ParsedFrame) => void) | null = null;
    if (animName !== 'none' && typeof ANIMATION_PRESETS !== 'undefined') {
      animFn = (ANIMATION_PRESETS as Record<string, typeof animFn>)[animName] || null;
    }

    const isStatic = parsedFrames.length <= 1 && !animFn;

    function getBgColor() {
      const bg = config.background || 'dark';
      if (bg === 'transparent') return null;
      if (bg === 'light') return '#ffffff';
      return '#000000';
    }

    function renderFrame(frame: ParsedFrame) {
      if (!ctx || !canvas) return;
      const cW = charW * scale;
      const cH = charH * scale;

      const bgColor = getBgColor();
      if (bgColor) {
        ctx.fillStyle = bgColor;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      } else {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }

      ctx.font = Math.floor(fontSize * scale) + 'px monospace';
      ctx.textBaseline = 'top';

      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const ch = frame.chars[r][c];
          if (ch === ' ') continue;
          const rgb = frame.colors[r][c];
          const idx = r * cols + c;
          let bx = c * cW + states.x[idx] * scale;
          let by = r * cH + states.y[idx] * scale;

          let cr = rgb[0], cg = rgb[1], cb = rgb[2];
          if (frame._colorMod) {
            const mod = frame._colorMod[idx];
            cr = Math.min(255, Math.floor(cr * mod));
            cg = Math.min(255, Math.floor(cg * mod));
            cb = Math.min(255, Math.floor(cb * mod));
          }
          if (frame._opacity) ctx.globalAlpha = frame._opacity[idx];

          ctx.fillStyle = `rgb(${cr},${cg},${cb})`;
          ctx.fillText(ch, bx, by);
        }
      }
      if (frame._opacity) ctx.globalAlpha = 1.0;
    }

    function updatePhysics() {
      const cfgAreaSize = config.areaSize || 268;
      const cfgStrength = ((config.hoverStrength || 22) / 100) * 3.0;
      const mode = config.mouseMode || 'push';
      const dir = mode === 'push' ? -1 : 1;
      const areaSizeSq = cfgAreaSize * cfgAreaSize;
      let anyMoving = false;

      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const idx = r * cols + c;
          if (mouseActive && interactive) {
            const homeX = c * charW + charW * 0.5;
            const homeY = r * charH + charH * 0.5;
            const dx = mouseX - homeX;
            const dy = mouseY - homeY;
            const distSq = dx * dx + dy * dy;
            if (distSq < areaSizeSq && distSq > 0.01) {
              const dist = Math.sqrt(distSq);
              const force = (1 - dist / cfgAreaSize) * cfgStrength;
              const invDist = 1 / dist;
              states.vx[idx] += dx * invDist * force * dir;
              states.vy[idx] += dy * invDist * force * dir;
            }
          }
          states.vx[idx] += -states.x[idx] * STIFFNESS;
          states.vy[idx] += -states.y[idx] * STIFFNESS;
          states.vx[idx] *= DAMPING;
          states.vy[idx] *= DAMPING;
          states.x[idx] += states.vx[idx];
          states.y[idx] += states.vy[idx];
          if (Math.abs(states.x[idx]) > SETTLE_THRESHOLD ||
              Math.abs(states.y[idx]) > SETTLE_THRESHOLD) {
            anyMoving = true;
          }
        }
      }
      return anyMoving;
    }

    // Event handlers
    function getPos(e: MouseEvent) {
      const rect = canvas!.getBoundingClientRect();
      const sx = canvas!.width / rect.width;
      const sy = canvas!.height / rect.height;
      return { x: (e.clientX - rect.left) * sx / scale, y: (e.clientY - rect.top) * sy / scale };
    }

    function onMouseMove(e: MouseEvent) {
      const pos = getPos(e);
      mouseX = pos.x; mouseY = pos.y;
      mouseActive = true;
    }
    function onMouseLeave() { mouseActive = false; }
    function onTouchMove(e: TouchEvent) {
      e.preventDefault();
      const t = e.touches[0];
      const rect = canvas!.getBoundingClientRect();
      mouseX = (t.clientX - rect.left) * (canvas!.width / rect.width) / scale;
      mouseY = (t.clientY - rect.top) * (canvas!.height / rect.height) / scale;
      mouseActive = true;
    }
    function onTouchEnd() { mouseActive = false; }

    if (interactive) {
      canvas.addEventListener('mousemove', onMouseMove);
      canvas.addEventListener('mouseleave', onMouseLeave);
      canvas.addEventListener('touchmove', onTouchMove, { passive: false });
      canvas.addEventListener('touchend', onTouchEnd);
    }

    // Resize observer
    const ro = new ResizeObserver(() => {
      scale = resize() || 1;
    });
    ro.observe(canvas.parentElement!);

    runningRef.current = true;

    if (isStatic && !interactive) {
      renderFrame(parsedFrames[0]);
      onReady?.();
    } else {
      const frameDuration = 1000 / (ASCII_DATA.fps || 10);
      let lastFrameTime = 0;

      function loop(timestamp: number) {
        if (!runningRef.current) return;

        if (parsedFrames.length > 1) {
          if (timestamp - lastFrameTime >= frameDuration) {
            frameIndex = (frameIndex + 1) % parsedFrames.length;
            lastFrameTime = timestamp;
          }
        }

        if (!reducedMotion) {
          updatePhysics();
          if (animFn) {
            const elapsed = (timestamp - startTime) / 1000;
            const cf = parsedFrames[frameIndex];
            if (cf._origChars) {
              for (let r = 0; r < rows; r++)
                for (let c = 0; c < cols; c++)
                  cf.chars[r][c] = cf._origChars[r][c];
            }
            animFn(states, rows, cols, charW, charH, elapsed, cf);
          }
        }

        renderFrame(parsedFrames[frameIndex]);
        animRef.current = requestAnimationFrame(loop);
      }

      animRef.current = requestAnimationFrame(loop);
      onReady?.();
    }

    return () => {
      runningRef.current = false;
      cancelAnimationFrame(animRef.current);
      ro.disconnect();
      if (interactive) {
        canvas.removeEventListener('mousemove', onMouseMove);
        canvas.removeEventListener('mouseleave', onMouseLeave);
        canvas.removeEventListener('touchmove', onTouchMove);
        canvas.removeEventListener('touchend', onTouchEnd);
      }
    };
  }, []);

  const containerStyle: React.CSSProperties = {
    width,
    height: height === 'auto' ? undefined : height,
    ...style,
  };

  return (
    <div className={className} style={containerStyle}>
      <canvas
        ref={canvasRef}
        role="img"
        aria-label="Interactive ASCII art"
        style={{ display: 'block', maxWidth: '100%' }}
      />
    </div>
  );
}
