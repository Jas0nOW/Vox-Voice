/* ============================================================
   WANDA MCC — Neural Field Canvas Renderer (TypeScript)
   Neural Nexus: 100 particles, distance-line rendering,
   globalCompositeOperation='screen', mouse gravity.
   60fps target via requestAnimationFrame.
   ============================================================ */

export interface NeuralColors {
  bg:        string;   // '#05050A'
  primary:   string;   // '#00F0FF'
  secondary: string;   // '#D600FF'
  particle:  string;   // '#FFFFFF'
}

export interface NeuralSignal {
  p1:       Particle;
  p2:       Particle;
  ts:       number;       // DOMHighResTimeStamp when started
  duration: number;       // ms
  color:    string;
}

interface Particle {
  x: number; y: number;
  vx: number; vy: number;
  size: number;
}

interface MouseState {
  x: number; y: number;
}

export interface NeuralFieldOptions {
  particleCount?:     number;   // default 100
  connectDist?:       number;   // default 150
  mouseAttractDist?:  number;   // default 200
  mouseAttractForce?: number;   // default 0.0004
  maxSpeed?:          number;   // default 2.2
}

export class NeuralField {
  private canvas: HTMLCanvasElement;
  private ctx:    CanvasRenderingContext2D;
  private colors: NeuralColors;
  private opts:   Required<NeuralFieldOptions>;

  private particles: Particle[]     = [];
  private signals:   NeuralSignal[] = [];
  private mouse:     MouseState     = { x: 0, y: 0 };
  private width      = 0;
  private height     = 0;
  private rafId: number | null = null;

  private _onMouseMove: (e: MouseEvent) => void;
  private _onResize:    ()              => void;

  constructor(
    canvas: HTMLCanvasElement,
    colors: NeuralColors,
    opts:   NeuralFieldOptions = {},
  ) {
    this.canvas = canvas;
    this.ctx    = canvas.getContext('2d', { alpha: false })!;
    this.colors = colors;
    this.opts   = {
      particleCount:     opts.particleCount     ?? 100,
      connectDist:       opts.connectDist       ?? 150,
      mouseAttractDist:  opts.mouseAttractDist  ?? 200,
      mouseAttractForce: opts.mouseAttractForce ?? 0.0004,
      maxSpeed:          opts.maxSpeed          ?? 2.2,
    };

    this._onMouseMove = (e: MouseEvent) => {
      this.mouse.x = e.clientX;
      this.mouse.y = e.clientY;
    };
    this._onResize = () => {
      this._resize();
      this._initParticles();
    };

    window.addEventListener('mousemove', this._onMouseMove);
    window.addEventListener('resize', this._onResize);

    this._resize();
    this._initParticles();
  }

  /** Start the animation loop */
  start(): void {
    if (this.rafId !== null) return;
    const loop = () => {
      this._render();
      this.rafId = requestAnimationFrame(loop);
    };
    this.rafId = requestAnimationFrame(loop);
  }

  /** Stop animation and remove event listeners */
  destroy(): void {
    if (this.rafId !== null) cancelAnimationFrame(this.rafId);
    window.removeEventListener('mousemove', this._onMouseMove);
    window.removeEventListener('resize', this._onResize);
  }

  /**
   * Emit N signal pulses along random active connections.
   * Call this when an event fires (mode switch, WS event, etc.)
   */
  emitSignals(count = 3, color?: string): void {
    const col = color ?? this.colors.primary;
    const { connectDist } = this.opts;
    const pairs: [number, number][] = [];

    // Collect connected pairs (limit search to first 1000 pairs)
    outer:
    for (let i = 0; i < this.particles.length; i++) {
      for (let j = i + 1; j < this.particles.length; j++) {
        const dx = this.particles[i].x - this.particles[j].x;
        const dy = this.particles[i].y - this.particles[j].y;
        if (dx * dx + dy * dy < connectDist * connectDist) {
          pairs.push([i, j]);
          if (pairs.length >= 50) break outer;
        }
      }
    }
    if (pairs.length === 0) return;

    const now = performance.now();
    for (let k = 0; k < count; k++) {
      const [i, j] = pairs[Math.floor(Math.random() * pairs.length)];
      const delay    = k * 90;
      const duration = 450 + Math.random() * 300;
      this.signals.push({ p1: this.particles[i], p2: this.particles[j], ts: now + delay, duration, color: col });
      // Return pulse
      if (Math.random() > 0.5) {
        this.signals.push({ p1: this.particles[j], p2: this.particles[i], ts: now + delay + 80, duration, color: col });
      }
    }
  }

  // ── Private ──────────────────────────────────────────────────

  private _resize(): void {
    this.width  = this.canvas.width  = window.innerWidth;
    this.height = this.canvas.height = window.innerHeight;
    this.mouse.x = this.width  / 2;
    this.mouse.y = this.height / 2;
  }

  private _initParticles(): void {
    this.particles = Array.from({ length: this.opts.particleCount }, () => ({
      x:    Math.random() * this.width,
      y:    Math.random() * this.height,
      vx:   (Math.random() - 0.5) * 1.4,
      vy:   (Math.random() - 0.5) * 1.4,
      size: Math.random() * 1.8 + 0.6,
    }));
  }

  private _render(): void {
    const { ctx, width, height, particles, signals, mouse, colors, opts } = this;
    const { connectDist, mouseAttractDist, mouseAttractForce, maxSpeed } = opts;
    const now = performance.now();

    // Trail fade (not full clear → ghosting effect)
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = `${colors.bg}40`;
    ctx.fillRect(0, 0, width, height);

    ctx.globalCompositeOperation = 'screen';

    // ── Particles ──
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];

      // Mouse gravity
      const mdx = mouse.x - p.x;
      const mdy = mouse.y - p.y;
      const md2 = mdx * mdx + mdy * mdy;
      if (md2 < mouseAttractDist * mouseAttractDist) {
        p.vx += mdx * mouseAttractForce;
        p.vy += mdy * mouseAttractForce;
      }

      // Speed cap
      const spd = Math.hypot(p.vx, p.vy);
      if (spd > maxSpeed) { p.vx = (p.vx / spd) * maxSpeed; p.vy = (p.vy / spd) * maxSpeed; }

      // Move + bounce
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > width)  { p.vx *= -1; p.x = Math.max(0, Math.min(width, p.x)); }
      if (p.y < 0 || p.y > height) { p.vy *= -1; p.y = Math.max(0, Math.min(height, p.y)); }

      // Particle glyph
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = colors.particle;
      ctx.fill();

      // Connections
      for (let j = i + 1; j < particles.length; j++) {
        const p2   = particles[j];
        const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
        if (dist < connectDist) {
          const alpha = Math.floor((1 - dist / connectDist) * 255).toString(16).padStart(2, '0');
          const grad  = ctx.createLinearGradient(p.x, p.y, p2.x, p2.y);
          grad.addColorStop(0, colors.primary   + alpha);
          grad.addColorStop(1, colors.secondary + alpha);
          ctx.beginPath();
          ctx.moveTo(p.x, p.y); ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = grad;
          ctx.lineWidth   = (1 - dist / connectDist) * 1.5;
          ctx.stroke();
        }
      }
    }

    // ── Signal pulses ──
    this.signals = signals.filter(sig => {
      const elapsed = now - sig.ts;
      if (elapsed < 0) return true; // scheduled, not yet started
      const t = Math.min(elapsed / sig.duration, 1);
      if (t >= 1) return false;

      const x   = sig.p1.x + (sig.p2.x - sig.p1.x) * t;
      const y   = sig.p1.y + (sig.p2.y - sig.p1.y) * t;
      const opa = Math.sin(t * Math.PI);

      ctx.beginPath();
      ctx.arc(x, y, 4 * opa + 1, 0, Math.PI * 2);
      ctx.fillStyle    = sig.color + Math.floor(opa * 220).toString(16).padStart(2, '0');
      ctx.shadowBlur   = 14;
      ctx.shadowColor  = sig.color;
      ctx.fill();
      ctx.shadowBlur   = 0;
      return true;
    });
  }
}
