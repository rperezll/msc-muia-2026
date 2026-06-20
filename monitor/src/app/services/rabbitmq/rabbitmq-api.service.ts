import { Injectable, DestroyRef, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import type { RabbitMqQueueStats } from '../../core/contracts';

const RABBITMQ_API = '/api/rabbitmq';
const QUEUE_NAME = 'anomalies';
const POLL_INTERVAL = 2000;

@Injectable({ providedIn: 'root' })
export class RabbitmqApiService {
  private readonly http = inject(HttpClient);
  private readonly destroyRef = inject(DestroyRef);

  readonly connected = signal(false);
  readonly queueStats = signal<RabbitMqQueueStats | null>(null);
  readonly queuePulse = signal(false);

  private previousMessages = 0;
  private intervalId: ReturnType<typeof setInterval> | null = null;
  private readonly headers = {
    Authorization: 'Basic ' + btoa('broker:mypassopt*!'),
  };

  constructor() {
    this.startPolling();
    this.destroyRef.onDestroy(() => {
      if (this.intervalId) clearInterval(this.intervalId);
    });
  }

  private startPolling(): void {
    this.fetchStats();
    this.intervalId = setInterval(() => this.fetchStats(), POLL_INTERVAL);
  }

  refresh(): void {
    this.fetchStats();
  }

  private fetchStats(): void {
    this.http
      .get<RabbitMqQueueStats>(`${RABBITMQ_API}/queues/%2F/${QUEUE_NAME}`, {
        headers: this.headers,
      })
      .subscribe({
        next: (stats) => {
          this.connected.set(true);
          if (stats.messages > this.previousMessages) this.triggerPulse();
          this.previousMessages = stats.messages;
          this.queueStats.set(stats);
        },
        error: () => {
          this.connected.set(false);
          this.queueStats.set(null);
        },
      });
  }

  private triggerPulse(): void {
    this.queuePulse.set(true);
    setTimeout(() => this.queuePulse.set(false), 2000);
  }

  purgeQueue(): void {
    this.http
      .delete(`${RABBITMQ_API}/queues/%2F/${QUEUE_NAME}/contents`, { headers: this.headers })
      .subscribe({
        next: () => {
          this.previousMessages = 0;
          this.fetchStats();
        },
      });
  }
}
