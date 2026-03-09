/**
 * ASCII Art Canvas Renderer
 * Renders ASCII art data to a <canvas> with sprite atlas optimization,
 * spring-based mouse physics, and animation presets.
 *
 * Expects ASCII_DATA to be defined before this script runs.
 */
(function () {
  'use strict';

  // --- Constants ---
  var STIFFNESS = 0.08;
  var DAMPING = 0.85;
  var SETTLE_THRESHOLD = 0.05;

  // --- Data Decoding ---

  function decodeColors(base64, rows, cols) {
    var bin = atob(base64);
    var arr = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    var result = new Array(rows);
    for (var r = 0; r < rows; r++) {
      result[r] = new Array(cols);
      for (var c = 0; c < cols; c++) {
        var idx = (r * cols + c) * 3;
        result[r][c] = [arr[idx] || 0, arr[idx + 1] || 0, arr[idx + 2] || 0];
      }
    }
    return result;
  }

  function parseFrame(frame, rows, cols) {
    var charRows = frame.chars.split('\n');
    var chars = new Array(rows);
    for (var r = 0; r < rows; r++) {
      var line = charRows[r] || '';
      chars[r] = new Array(cols);
      for (var c = 0; c < cols; c++) {
        chars[r][c] = c < line.length ? line[c] : ' ';
      }
    }
    var colors = decodeColors(frame.colors, rows, cols);
    return { chars: chars, colors: colors };
  }

  // --- Renderer ---

  function AsciiRenderer(canvas, data) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.data = data;
    this.config = data.config || {};
    this.frameIndex = 0;
    this.animId = 0;
    this.running = false;
    this.parsedFrames = [];
    this.charW = 0;
    this.charH = 0;
    this.font = '';
    this.scale = 1;

    // Mouse state
    this.mouseX = -9999;
    this.mouseY = -9999;
    this.mouseActive = false;

    // Physics state: displacement + velocity
    var count = data.rows * data.cols;
    this.px = new Float32Array(count);  // physics displacement x
    this.py = new Float32Array(count);  // physics displacement y
    this.pvx = new Float32Array(count); // physics velocity x
    this.pvy = new Float32Array(count); // physics velocity y

    // Animation offsets (SET each frame, not accumulated)
    this.animX = new Float32Array(count);
    this.animY = new Float32Array(count);
    this.animOpacity = null;   // Float32Array or null
    this.animColorMod = null;  // Float32Array or null

    // Glitch char overrides
    this.glitchChars = null; // sparse: { "r,c": "char" }

    this.animationFn = null;
    this.startTime = 0;
    this.settled = false;

    // Reduced motion
    this.reducedMotion = window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  AsciiRenderer.prototype.init = function () {
    var cfg = this.config;
    var fontSize = cfg.fontSize || 14;

    this.font = fontSize + 'px monospace';
    this.ctx.font = this.font;
    this.ctx.textBaseline = 'top';

    var metrics = this.ctx.measureText('M');
    this.charW = metrics.width;
    this.charH = (metrics.actualBoundingBoxAscent || fontSize * 0.8) +
                 (metrics.actualBoundingBoxDescent || fontSize * 0.2);
    this.charH = Math.ceil(this.charH * 1.1);

    // Parse frames
    var rows = this.data.rows;
    var cols = this.data.cols;
    for (var i = 0; i < this.data.frames.length; i++) {
      this.parsedFrames.push(parseFrame(this.data.frames[i], rows, cols));
    }

    // Size canvas
    this._resize();

    // Mouse/touch listeners
    this._bindMouse();

    // Responsive resize
    var self = this;
    this._resizeObserver = new ResizeObserver(function () {
      clearTimeout(self._resizeTimer);
      self._resizeTimer = setTimeout(function () { self._resize(); }, 150);
    });
    this._resizeObserver.observe(this.canvas.parentElement);
  };

  AsciiRenderer.prototype._bindMouse = function () {
    var self = this;
    var canvas = this.canvas;

    canvas.addEventListener('mousemove', function (e) {
      var rect = canvas.getBoundingClientRect();
      self.mouseX = (e.clientX - rect.left) * (canvas.width / rect.width) / self.scale;
      self.mouseY = (e.clientY - rect.top) * (canvas.height / rect.height) / self.scale;
      self.mouseActive = true;
      self.settled = false;
    });

    canvas.addEventListener('mouseleave', function () {
      self.mouseActive = false;
    });

    canvas.addEventListener('touchmove', function (e) {
      e.preventDefault();
      var touch = e.touches[0];
      var rect = canvas.getBoundingClientRect();
      self.mouseX = (touch.clientX - rect.left) * (canvas.width / rect.width) / self.scale;
      self.mouseY = (touch.clientY - rect.top) * (canvas.height / rect.height) / self.scale;
      self.mouseActive = true;
      self.settled = false;
    }, { passive: false });

    canvas.addEventListener('touchend', function () {
      self.mouseActive = false;
    });
  };

  AsciiRenderer.prototype._resize = function () {
    var container = this.canvas.parentElement;
    var containerW = container.clientWidth;
    var containerH = container.clientHeight || window.innerHeight;
    var naturalW = this.data.cols * this.charW;

    // Use source image aspect ratio if available, otherwise fall back to grid dims
    var sourceAspect = this.config.sourceAspect || (this.data.rows * this.charH / naturalW);
    var naturalH = naturalW * sourceAspect;

    // Derive charH from the correct aspect ratio so rendering matches
    this.charH = naturalH / this.data.rows;

    // Scale to fit BOTH width and height (whichever is more constraining)
    var scale = Math.min(1, containerW / naturalW, containerH / naturalH);
    this.canvas.width = Math.floor(naturalW * scale);
    this.canvas.height = Math.floor(naturalH * scale);
    this.canvas.style.width = this.canvas.width + 'px';
    this.canvas.style.height = this.canvas.height + 'px';
    this.scale = scale;

    this.ctx.font = this.font;
    this.ctx.textBaseline = 'top';
    this.settled = false;
  };

  AsciiRenderer.prototype._getBgColor = function () {
    var bg = this.config.background || 'dark';
    if (bg === 'transparent') return null;
    if (bg === 'light') return '#ffffff';
    return '#000000';
  };

  AsciiRenderer.prototype._updatePhysics = function () {
    var rows = this.data.rows;
    var cols = this.data.cols;
    var px = this.px, py = this.py, pvx = this.pvx, pvy = this.pvy;
    var areaSize = this.config.areaSize || 300;
    var hoverStrength = ((this.config.hoverStrength || 35) / 100) * 3.0;
    var mode = this.config.mouseMode || 'push';
    var dir = mode === 'push' ? -1 : 1;
    var areaSizeSq = areaSize * areaSize;
    var mouseActive = this.mouseActive;
    var mouseX = this.mouseX, mouseY = this.mouseY;
    var charW = this.charW, charH = this.charH;
    var anyMoving = false;

    // Pre-compute mouse row/col range for fast skipping
    var mouseRowMin = 0, mouseRowMax = rows, mouseColMin = 0, mouseColMax = cols;
    if (mouseActive) {
      var mrCenter = mouseY / charH;
      var mcCenter = mouseX / charW;
      var rRadius = areaSize / charH + 1;
      var cRadius = areaSize / charW + 1;
      mouseRowMin = Math.max(0, Math.floor(mrCenter - rRadius));
      mouseRowMax = Math.min(rows, Math.ceil(mrCenter + rRadius));
      mouseColMin = Math.max(0, Math.floor(mcCenter - cRadius));
      mouseColMax = Math.min(cols, Math.ceil(mcCenter + cRadius));
    }

    for (var r = 0; r < rows; r++) {
      var rowInMouseRange = mouseActive && r >= mouseRowMin && r < mouseRowMax;
      for (var c = 0; c < cols; c++) {
        var idx = r * cols + c;

        var isSettled = px[idx] === 0 && py[idx] === 0 &&
                        pvx[idx] === 0 && pvy[idx] === 0;

        // Skip settled characters outside mouse range
        if (isSettled && !(rowInMouseRange && c >= mouseColMin && c < mouseColMax)) continue;

        // Mouse force (only for chars in range)
        if (rowInMouseRange && c >= mouseColMin && c < mouseColMax) {
          var homeX = c * charW + charW * 0.5;
          var homeY = r * charH + charH * 0.5;
          var dx = mouseX - homeX;
          var dy = mouseY - homeY;
          var distSq = dx * dx + dy * dy;

          if (distSq < areaSizeSq && distSq > 0.01) {
            var dist = Math.sqrt(distSq);
            var force = (1 - dist / areaSize) * hoverStrength;
            var invDist = 1 / dist;
            pvx[idx] += dx * invDist * force * dir;
            pvy[idx] += dy * invDist * force * dir;
          }
        }

        // Spring return
        pvx[idx] += -px[idx] * STIFFNESS;
        pvy[idx] += -py[idx] * STIFFNESS;

        // Damping
        pvx[idx] *= DAMPING;
        pvy[idx] *= DAMPING;

        // Integrate
        px[idx] += pvx[idx];
        py[idx] += pvy[idx];

        // Snap to zero when settled
        if (Math.abs(px[idx]) < SETTLE_THRESHOLD && Math.abs(pvx[idx]) < SETTLE_THRESHOLD) {
          px[idx] = 0; pvx[idx] = 0;
        } else {
          anyMoving = true;
        }
        if (Math.abs(py[idx]) < SETTLE_THRESHOLD && Math.abs(pvy[idx]) < SETTLE_THRESHOLD) {
          py[idx] = 0; pvy[idx] = 0;
        } else {
          anyMoving = true;
        }
      }
    }
    return anyMoving;
  };

  AsciiRenderer.prototype._renderFrame = function (frame) {
    var ctx = this.ctx;
    var rows = this.data.rows;
    var cols = this.data.cols;
    var scale = this.scale;
    var charW = this.charW * scale;
    var charH = this.charH * scale;
    var px = this.px, py = this.py;
    var animX = this.animX, animY = this.animY;
    var animOpacity = this.animOpacity;
    var animColorMod = this.animColorMod;
    var glitchChars = this.glitchChars;

    // Clear
    var bgColor = this._getBgColor();
    if (bgColor) {
      ctx.fillStyle = bgColor;
      ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    } else {
      ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    var scaledFont = Math.floor((this.config.fontSize || 14) * scale) + 'px monospace';
    ctx.font = scaledFont;
    ctx.textBaseline = 'top';

    for (var r = 0; r < rows; r++) {
      for (var c = 0; c < cols; c++) {
        var idx = r * cols + c;

        // Use glitch char override if present
        var ch = (glitchChars && glitchChars[idx] !== undefined)
          ? glitchChars[idx]
          : frame.chars[r][c];
        if (ch === ' ') continue;

        var rgb = frame.colors[r][c];
        var bx = c * charW + (px[idx] + animX[idx]) * scale;
        var by = r * charH + (py[idx] + animY[idx]) * scale;

        // Color
        var cr = rgb[0], cg = rgb[1], cb = rgb[2];
        if (animColorMod) {
          var mod = animColorMod[idx];
          cr = Math.min(255, Math.floor(cr * mod));
          cg = Math.min(255, Math.floor(cg * mod));
          cb = Math.min(255, Math.floor(cb * mod));
        }

        // Opacity
        if (animOpacity) {
          ctx.globalAlpha = animOpacity[idx];
        }

        ctx.fillStyle = 'rgb(' + cr + ',' + cg + ',' + cb + ')';
        ctx.fillText(ch, bx, by);
      }
    }

    if (animOpacity) ctx.globalAlpha = 1.0;
  };

  AsciiRenderer.prototype.start = function () {
    this.running = true;
    this.startTime = performance.now();

    // Look up animation function
    var animName = this.config.animation || 'none';
    if (animName !== 'none' && window.__asciiAnimations && window.__asciiAnimations[animName]) {
      this.animationFn = window.__asciiAnimations[animName];
    }

    var isStatic = this.parsedFrames.length <= 1 && !this.animationFn;

    // Render first frame immediately
    this._renderFrame(this.parsedFrames[0]);

    if (!isStatic) {
      // Video or animation — always loop
      this._runLoop();
    } else {
      // Static: loop runs on-demand when mouse interacts
      this.settled = true;
      this._runLoop();
    }
  };

  AsciiRenderer.prototype._runLoop = function () {
    var self = this;
    var frameDuration = 1000 / (this.data.fps || 10);
    var lastFrameTime = 0;
    var rows = this.data.rows;
    var cols = this.data.cols;
    var hasAnimation = !!this.animationFn;
    var hasVideo = this.parsedFrames.length > 1;

    function loop(timestamp) {
      if (!self.running) return;

      var needsRender = false;

      // Video frame advancement
      if (hasVideo) {
        if (timestamp - lastFrameTime >= frameDuration) {
          self.frameIndex = (self.frameIndex + 1) % self.parsedFrames.length;
          lastFrameTime = timestamp;
          needsRender = true;
        }
      }

      if (!self.reducedMotion) {
        // Update spring physics
        var anyMoving = self._updatePhysics();
        if (anyMoving || self.mouseActive) {
          needsRender = true;
          self.settled = false;
        }

        // Clear animation offsets before animation call
        if (hasAnimation) {
          var count = rows * cols;
          for (var i = 0; i < count; i++) {
            self.animX[i] = 0;
            self.animY[i] = 0;
          }
          self.animOpacity = null;
          self.animColorMod = null;
          self.glitchChars = null;

          var elapsed = (timestamp - self.startTime) / 1000;
          self.animationFn(self, rows, cols, self.charW, self.charH, elapsed);
          needsRender = true;
        }
      }

      if (needsRender) {
        self._renderFrame(self.parsedFrames[self.frameIndex]);
        self.settled = false;
      } else if (!self.settled && !self.mouseActive && !hasVideo && !hasAnimation) {
        // One final render after everything settles
        self._renderFrame(self.parsedFrames[self.frameIndex]);
        self.settled = true;
      }

      self.animId = requestAnimationFrame(loop);
    }

    this.animId = requestAnimationFrame(loop);
  };

  AsciiRenderer.prototype.stop = function () {
    this.running = false;
    cancelAnimationFrame(this.animId);
    if (this._resizeObserver) {
      this._resizeObserver.disconnect();
    }
  };

  // --- Bootstrap ---

  function boot() {
    var canvas = document.getElementById('ascii-canvas');
    if (!canvas || typeof ASCII_DATA === 'undefined') return;

    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', 'Interactive ASCII art');
    canvas.setAttribute('tabindex', '0');

    var renderer = new AsciiRenderer(canvas, ASCII_DATA);
    renderer.init();
    renderer.start();

    window.addEventListener('beforeunload', function () {
      renderer.stop();
    });

    window.__asciiRenderer = renderer;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
