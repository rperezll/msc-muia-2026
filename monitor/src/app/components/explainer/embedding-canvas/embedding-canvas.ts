import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
  afterNextRender,
  effect,
  input,
} from '@angular/core';

interface SpherePoint {
  bx: number;
  by: number;
  bz: number;
  r: number;
}

@Component({
  selector: 'app-embedding-canvas',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: true,
  template: `<canvas #canvas class="block h-full w-full"></canvas>`,
})
export class EmbeddingCanvasComponent implements OnDestroy {
  @ViewChild('canvas', { static: true }) private canvasRef!: ElementRef<HTMLCanvasElement>;

  readonly loading = input<boolean>(false);

  private points: SpherePoint[] = [];
  private rotX = 0.3;
  private rotY = 0.2;
  private speedX = 0;
  private speedY = 0;
  private targetSpeedX = 0;
  private targetSpeedY = 0;
  private raf = 0;

  constructor() {
    afterNextRender(() => this.init());

    effect(() => {
      if (this.loading()) {
        this.targetSpeedX = 0.004;
        this.targetSpeedY = 0.009;
      } else {
        this.targetSpeedX = 0;
        this.targetSpeedY = 0;
      }
    });
  }

  ngOnDestroy(): void {
    cancelAnimationFrame(this.raf);
  }

  private init(): void {
    const canvas = this.canvasRef.nativeElement;
    const parent = canvas.parentElement!;
    canvas.width = parent.offsetWidth;
    canvas.height = parent.offsetHeight;

    const COUNT = 52;
    const golden = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < COUNT; i++) {
      const y = 1 - (i / (COUNT - 1)) * 2;
      const rho = Math.sqrt(Math.max(0, 1 - y * y));
      const theta = golden * i;
      const jitter = 0.82 + Math.random() * 0.36;
      this.points.push({
        bx: Math.cos(theta) * rho * jitter,
        by: y * jitter,
        bz: Math.sin(theta) * rho * jitter,
        r: 2.8 + Math.random() * 2.2,
      });
    }

    this.loop();
  }

  private loop(): void {
    const canvas = this.canvasRef.nativeElement;
    const ctx = canvas.getContext('2d')!;
    const W = canvas.width;
    const H = canvas.height;
    const cx = W / 2;
    const cy = H / 2;
    const SR = Math.min(W, H) * 0.36;
    const FOV = 480;
    const LINK3D = 0.72;

    this.speedX += (this.targetSpeedX - this.speedX) * 0.035;
    this.speedY += (this.targetSpeedY - this.speedY) * 0.035;
    this.rotX += this.speedX;
    this.rotY += this.speedY;

    const cosX = Math.cos(this.rotX);
    const sinX = Math.sin(this.rotX);
    const cosY = Math.cos(this.rotY);
    const sinY = Math.sin(this.rotY);

    const proj = this.points.map((p) => {
      // rotación Y
      const x1 = p.bx * cosY + p.bz * sinY;
      const z1 = -p.bx * sinY + p.bz * cosY;
      // rotación X
      const y2 = p.by * cosX - z1 * sinX;
      const z2 = p.by * sinX + z1 * cosX;

      const scale = FOV / (FOV + z2 * SR);
      return {
        px: cx + x1 * SR * scale,
        py: cy + y2 * SR * scale,
        rx: x1,
        ry: y2,
        rz: z2,
        scale,
        depth: (z2 + 1) / 2,
        r: p.r,
      };
    });

    ctx.clearRect(0, 0, W, H);

    const isLight = document.documentElement.classList.contains('light');
    const rgb = isLight ? '60,60,60' : '180,180,180';

    for (let i = 0; i < proj.length; i++) {
      for (let j = i + 1; j < proj.length; j++) {
        const a = proj[i];
        const b = proj[j];
        const dx = a.rx - b.rx;
        const dy = a.ry - b.ry;
        const dz = a.rz - b.rz;
        const d = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (d < LINK3D) {
          const nearness = 1 - d / LINK3D;
          const avgDepth = (a.depth + b.depth) / 2;
          const lineBase = this.loading() ? 0.22 : isLight ? 0.025 : 0.015;
          const alpha = nearness * (lineBase + avgDepth * lineBase);
          ctx.strokeStyle = `rgba(${rgb},${alpha})`;
          ctx.lineWidth = 0.6;
          ctx.beginPath();
          ctx.moveTo(a.px, a.py);
          ctx.lineTo(b.px, b.py);
          ctx.stroke();
        }
      }
    }

    const baseAlpha = this.loading() ? 1.0 : isLight ? 0.09 : 0.06;
    const sorted = [...proj].sort((a, b) => a.depth - b.depth);
    for (const p of sorted) {
      const alpha = baseAlpha * (0.25 + p.depth * 0.75);
      const r = p.r * (0.6 + p.depth * 0.6) * p.scale;
      ctx.fillStyle = `rgba(${rgb},${alpha})`;
      ctx.beginPath();
      ctx.arc(p.px, p.py, r, 0, Math.PI * 2);
      ctx.fill();
    }

    this.raf = requestAnimationFrame(() => this.loop());
  }
}
