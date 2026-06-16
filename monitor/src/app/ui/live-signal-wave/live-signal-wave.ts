import { Component, computed, DestroyRef, effect, inject, input, signal } from '@angular/core';
import type { SimulatorState } from '../../core/contracts';

const POINTS = 50;
const TICK_MS = 80;
const Y_FLOOR = 38;
const Y_CEIL = 3;

@Component({
  selector: 'app-live-signal-wave',
  styles: `
    :host {
      display: block;
      position: relative;
    }
    .grid-bg {
      position: absolute;
      inset: 0;
      --grid-color: color-mix(in srgb, var(--color-status-ok) 10%, transparent);
      background-image:
        linear-gradient(to right, var(--grid-color) 1px, transparent 1px),
        linear-gradient(to bottom, var(--grid-color) 1px, transparent 1px);
      background-size: 12.5% 20%;
    }
    :host-context(.light) .grid-bg {
      --grid-color: color-mix(in srgb, var(--color-status-ok) 25%, transparent);
    }
  `,
  template: `
    <div class="grid-bg"></div>
    <svg
      viewBox="0 0 100 40"
      preserveAspectRatio="none"
      class="relative h-full w-full"
      aria-hidden="true"
    >
      <polyline
        [attr.points]="svgPoints()"
        fill="none"
        stroke="var(--color-status-ok)"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        opacity="0.8"
      />
    </svg>
  `,
})
export class LiveSignalWave {
  readonly state = input.required<SimulatorState>();
  readonly value = input<number | null>(null);

  private readonly yValues = signal<number[]>(Array(POINTS).fill(Y_FLOOR));
  private currentY = Y_FLOOR;
  private velocity = 0;

  protected readonly svgPoints = computed(() => {
    const ys = this.yValues();
    const step = 100 / (POINTS - 1);
    return ys.map((y, i) => `${(i * step).toFixed(2)},${y.toFixed(2)}`).join(' ');
  });

  private intervalId: ReturnType<typeof setInterval> | null = null;
  private readonly destroyRef = inject(DestroyRef);

  constructor() {
    effect(() => {
      switch (this.state()) {
        case 'playing':
          this._start();
          break;
        case 'paused':
          this._freeze();
          break;
        case 'stopped':
          this._stop();
          break;
      }
    });

    this.destroyRef.onDestroy(() => this._clearInterval());
  }

  private _clearInterval(): void {
    if (this.intervalId !== null) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  private _start(): void {
    if (this.intervalId !== null) return;
    this.intervalId = setInterval(() => this._tick(), TICK_MS);
  }

  private _freeze(): void {
    this._clearInterval();
  }

  private _stop(): void {
    this._clearInterval();
    this.velocity = 0;
    const decay = setInterval(() => {
      this.currentY += (Y_FLOOR - this.currentY) * 0.15;
      this.yValues.update((prev) => [...prev.slice(1), this.currentY]);
      if (Math.abs(this.currentY - Y_FLOOR) < 0.3) {
        clearInterval(decay);
        this.yValues.set(Array(POINTS).fill(Y_FLOOR));
      }
    }, TICK_MS);
  }

  private _tick(): void {
    const v = this.value();

    if (v !== null) {
      const targetY = Y_FLOOR + v * (Y_CEIL - Y_FLOOR);
      this.currentY += (targetY - this.currentY) * 0.25;
      this.currentY += (Math.random() - 0.5) * 1.5;
    } else {
      this.velocity += (Math.random() - 0.5) * 5;
      this.velocity *= 0.75;
      this.currentY += this.velocity;
    }

    this.currentY = Math.min(Y_FLOOR, Math.max(Y_CEIL, this.currentY));
    this.yValues.update((prev) => [...prev.slice(1), this.currentY]);
  }
}
