import { Component, computed, input } from '@angular/core';

const SUNRISE_MINUTES = 5 * 60 + 45;
const SUNSET_MINUTES = 18 * 60 + 45;

const P0 = { x: 60, y: 160 };
const P1 = { x: 400, y: 5 };
const P2 = { x: 740, y: 160 };

function bezier(t: number): { x: number; y: number } {
  const inv = 1 - t;
  return {
    x: inv * inv * P0.x + 2 * inv * t * P1.x + t * t * P2.x,
    y: inv * inv * P0.y + 2 * inv * t * P1.y + t * t * P2.y,
  };
}

function formatTime(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

@Component({
  selector: 'app-sun-cycle',
  templateUrl: './sun-cycle.html',
  styles: `
    :host {
      display: block;

      --arc-color: #52525b;
      --trail-color: #78350f;
      --horizon-color: #52525b;
      --label-color: #a1a1aa;
      --badge-bg: rgba(10, 10, 11, 0.82);
      --badge-border: rgba(255, 255, 255, 0.13);
      --badge-text: #e4e4e7;
    }

    :host-context(.light) {
      --arc-color: #94a3b8;
      --trail-color: #b45309;
      --horizon-color: #94a3b8;
      --label-color: #71717a;
      --badge-bg: rgba(250, 250, 250, 0.9);
      --badge-border: rgba(0, 0, 0, 0.1);
      --badge-text: #09090b;
    }

    .stroke-arc {
      stroke: var(--arc-color);
    }
    .stroke-trail {
      stroke: var(--trail-color);
    }
    .stroke-horizon {
      stroke: var(--horizon-color);
    }
    .fill-label {
      fill: var(--label-color);
    }
    .fill-surface {
      fill: var(--color-surface-base);
    }
    .badge-bg {
      fill: var(--badge-bg);
      stroke: var(--badge-border);
      stroke-width: 0.5;
    }
    .fill-time {
      fill: var(--badge-text);
    }
  `,
})
export class SunCycleComponent {
  readonly currentTime = input<string | null>(null);

  readonly sunriseLabel = formatTime(SUNRISE_MINUTES);
  readonly sunsetLabel = formatTime(SUNSET_MINUTES);

  readonly currentTimeLabel = computed(() => {
    const time = this.currentTime();
    if (!time) return '—';
    return time.substring(11, 16);
  });

  readonly progress = computed(() => {
    const time = this.currentTime();
    if (!time) return -1;
    const minutes = this.parseMinutes(time);
    if (minutes === null) return -1;
    const raw = (minutes - SUNRISE_MINUTES) / (SUNSET_MINUTES - SUNRISE_MINUTES);
    return Math.max(0, Math.min(1, raw));
  });

  readonly isNight = computed(() => {
    const time = this.currentTime();
    if (!time) return true;
    const minutes = this.parseMinutes(time);
    if (minutes === null) return true;
    return minutes < SUNRISE_MINUTES || minutes > SUNSET_MINUTES;
  });

  readonly sunPos = computed(() => {
    if (this.isNight()) {
      const time = this.currentTime();
      const minutes = time ? this.parseMinutes(time) : null;
      if (minutes !== null && minutes > SUNSET_MINUTES) return bezier(1);
      return bezier(0);
    }
    return bezier(this.progress());
  });

  readonly trailDash = computed(() => {
    const arcLength = 703;
    const drawn = this.progress() * arcLength;
    return `${drawn} ${arcLength}`;
  });

  private parseMinutes(datetime: string): number | null {
    const timePart = datetime?.substring(11, 16);
    if (!timePart || !timePart.includes(':')) return null;
    const [h, m] = timePart.split(':').map(Number);
    if (isNaN(h) || isNaN(m)) return null;
    return h * 60 + m;
  }
}
