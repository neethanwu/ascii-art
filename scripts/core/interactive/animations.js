/**
 * ASCII Art Animation Presets
 *
 * NEW API: Each preset receives the renderer object directly.
 * Presets SET animation offsets (animX, animY, animOpacity, animColorMod, glitchChars)
 * on the renderer — they do NOT modify physics state or frame data.
 *
 * Signature: (renderer, rows, cols, charW, charH, time) => void
 */

// --- Simplex Noise (2D) ---
// Based on Stefan Gustavson's implementation (public domain)

var SIMPLEX = (function () {
  var grad3 = [
    [1,1,0],[-1,1,0],[1,-1,0],[-1,-1,0],
    [1,0,1],[-1,0,1],[1,0,-1],[-1,0,-1],
    [0,1,1],[0,-1,1],[0,1,-1],[0,-1,-1]
  ];

  var perm = new Uint8Array(512);
  var p = [151,160,137,91,90,15,131,13,201,95,96,53,194,233,7,225,140,36,103,30,
    69,142,8,99,37,240,21,10,23,190,6,148,247,120,234,75,0,26,197,62,94,252,
    219,203,117,35,11,32,57,177,33,88,237,149,56,87,174,20,125,136,171,168,
    68,175,74,165,71,134,139,48,27,166,77,146,158,231,83,111,229,122,60,211,
    133,230,220,105,92,41,55,46,245,40,244,102,143,54,65,25,63,161,1,216,
    80,73,209,76,132,187,208,89,18,169,200,196,135,130,116,188,159,86,164,
    100,109,198,173,186,3,64,52,217,226,250,124,123,5,202,38,147,118,126,
    255,82,85,212,207,206,59,227,47,16,58,17,182,189,28,42,223,183,170,213,
    119,248,152,2,44,154,163,70,221,153,101,155,167,43,172,9,129,22,39,253,
    19,98,108,110,79,113,224,232,178,185,112,104,218,246,97,228,251,34,242,
    193,238,210,144,12,191,179,162,241,81,51,145,235,249,14,239,107,49,192,
    214,31,181,199,106,157,184,84,204,176,115,121,50,45,127,4,150,254,138,
    236,205,93,222,114,67,29,24,72,243,141,128,195,78,66,215,61,156,180];
  for (var i = 0; i < 512; i++) perm[i] = p[i & 255];

  function dot(g, x, y) { return g[0] * x + g[1] * y; }

  var F2 = 0.5 * (Math.sqrt(3) - 1);
  var G2 = (3 - Math.sqrt(3)) / 6;

  return function noise2D(xin, yin) {
    var s = (xin + yin) * F2;
    var i = Math.floor(xin + s);
    var j = Math.floor(yin + s);
    var t = (i + j) * G2;
    var x0 = xin - (i - t);
    var y0 = yin - (j - t);

    var i1, j1;
    if (x0 > y0) { i1 = 1; j1 = 0; }
    else { i1 = 0; j1 = 1; }

    var x1 = x0 - i1 + G2;
    var y1 = y0 - j1 + G2;
    var x2 = x0 - 1 + 2 * G2;
    var y2 = y0 - 1 + 2 * G2;

    var ii = i & 255;
    var jj = j & 255;

    var n0, n1, n2;
    var t0 = 0.5 - x0 * x0 - y0 * y0;
    if (t0 < 0) n0 = 0;
    else { t0 *= t0; n0 = t0 * t0 * dot(grad3[perm[ii + perm[jj]] % 12], x0, y0); }

    var t1 = 0.5 - x1 * x1 - y1 * y1;
    if (t1 < 0) n1 = 0;
    else { t1 *= t1; n1 = t1 * t1 * dot(grad3[perm[ii + i1 + perm[jj + j1]] % 12], x1, y1); }

    var t2 = 0.5 - x2 * x2 - y2 * y2;
    if (t2 < 0) n2 = 0;
    else { t2 *= t2; n2 = t2 * t2 * dot(grad3[perm[ii + 1 + perm[jj + 1]] % 12], x2, y2); }

    return 70 * (n0 + n1 + n2);
  };
})();

// --- Preset: Noise Field ---
// Characters drift with organic simplex noise displacement (SET, not ADD)

function noiseField(renderer, rows, cols, charW, charH, time) {
  var ax = renderer.animX;
  var ay = renderer.animY;
  var strength = charW * 0.8; // Scale to char size for visible effect
  var speed = 1.5;
  var scale = 0.03;
  for (var r = 0; r < rows; r++) {
    for (var c = 0; c < cols; c++) {
      var idx = r * cols + c;
      ax[idx] = SIMPLEX(c * scale, r * scale + time * speed) * strength;
      ay[idx] = SIMPLEX(c * scale + 100, r * scale + time * speed + 100) * strength;
    }
  }
}

// --- Preset: Intervals ---
// Sine wave opacity modulation

function intervals(renderer, rows, cols, charW, charH, time) {
  var count = rows * cols;
  if (!renderer.animOpacity) renderer.animOpacity = new Float32Array(count);
  var op = renderer.animOpacity;
  var speed = 3.0;
  var scaleC = 0.06;
  var scaleR = 0.03;
  for (var r = 0; r < rows; r++) {
    for (var c = 0; c < cols; c++) {
      var idx = r * cols + c;
      op[idx] = 0.2 + 0.8 * (0.5 + 0.5 * Math.sin(c * scaleC + r * scaleR + time * speed));
    }
  }
}

// --- Preset: Beam Sweep ---
// Vertical bright line sweeps left-to-right

function beamSweep(renderer, rows, cols, charW, charH, time) {
  var count = rows * cols;
  if (!renderer.animColorMod) renderer.animColorMod = new Float32Array(count);
  var cm = renderer.animColorMod;
  var beamWidth = Math.max(5, Math.floor(cols * 0.08));
  var cycleTime = 2.0; // faster sweep
  var beamCenter = ((time % cycleTime) / cycleTime) * cols;

  for (var r = 0; r < rows; r++) {
    for (var c = 0; c < cols; c++) {
      var idx = r * cols + c;
      var dist = Math.abs(c - beamCenter);
      cm[idx] = dist < beamWidth ? 1.0 + 1.0 * (1 - dist / beamWidth) : 1.0;
    }
  }
}

// --- Preset: Glitch ---
// Random char replacement + horizontal tear (via animation offsets, not physics)

var GLITCH_CHARS = ['\u2588', '\u2593', '\u2592', '\u2591', '#', '@', '%', '&', '*'];

function glitch(renderer, rows, cols, charW, charH, time) {
  var ax = renderer.animX;

  // Character substitution: 0.8% chance per char
  var gc = {};
  for (var r = 0; r < rows; r++) {
    for (var c = 0; c < cols; c++) {
      if (Math.random() < 0.008) {
        gc[r * cols + c] = GLITCH_CHARS[Math.floor(Math.random() * GLITCH_CHARS.length)];
      }
    }
  }
  renderer.glitchChars = gc;

  // Horizontal tear: 3% chance per row
  for (var r = 0; r < rows; r++) {
    if (Math.random() < 0.03) {
      var shift = (Math.floor(Math.random() * 7) - 3) || 1;
      for (var c = 0; c < cols; c++) {
        ax[r * cols + c] = shift * charW;
      }
    }
  }
}

// --- Preset: CRT Monitor ---
// Scanlines, vignette, color fringe (via colorMod — no source data mutation)

function crt(renderer, rows, cols, charW, charH, time) {
  var count = rows * cols;
  if (!renderer.animColorMod) renderer.animColorMod = new Float32Array(count);
  var cm = renderer.animColorMod;
  var centerR = rows * 0.5;
  var centerC = cols * 0.5;

  for (var r = 0; r < rows; r++) {
    var scanline = (r % 2 === 0) ? 1.0 : 0.5;
    for (var c = 0; c < cols; c++) {
      var dr = (r - centerR) / centerR;
      var dc = (c - centerC) / centerC;
      var vignette = 1.0 - 0.35 * (dr * dr + dc * dc);
      cm[r * cols + c] = scanline * vignette;
    }
  }
}

// --- Registry ---

var PRESETS = {
  'noise-field': noiseField,
  'intervals': intervals,
  'beam-sweep': beamSweep,
  'glitch': glitch,
  'crt': crt,
};

window.__asciiAnimations = PRESETS;
