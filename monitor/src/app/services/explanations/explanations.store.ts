import { Injectable, computed, effect, inject, signal, untracked } from '@angular/core';

import { ExplanationsApiService } from './explanations-api.service';
import { MqttService } from '../mqtt/mqtt.service';
import { RabbitmqApiService } from '../rabbitmq/rabbitmq-api.service';
import type {
  AugmentResponse,
  ExplanationFeedback,
  ExplanationRecord,
  ExplainerSeverity,
} from '../../core/contracts';

const PAGE_SIZE = 10;

@Injectable({ providedIn: 'root' })
export class ExplanationsStore {
  private readonly api = inject(ExplanationsApiService);
  private readonly mqtt = inject(MqttService);
  private readonly rabbitmq = inject(RabbitmqApiService);

  readonly persisted = signal<ExplanationRecord[]>([]);
  readonly persistedTotal = signal(0);
  readonly persistedLoading = signal(false);
  readonly persistedError = signal<string | null>(null);

  readonly filterSeverity = signal<ExplainerSeverity | null>(null);
  readonly filterSourceKey = signal<string | null>(null);
  readonly sourceKeys = signal<string[]>([]);

  private readonly _offset = signal(0);
  readonly hasMore = computed(() => this.persisted().length < this.persistedTotal());

  readonly isAnalyzing = computed(() => {
    const queueInProgress = (this.rabbitmq.queueStats()?.messages_unacknowledged ?? 0) > 0;
    if (queueInProgress) return true;
    const events = this.mqtt.jobEvents();
    if (events.length === 0) return false;
    const latest = events[0];
    return latest.type === 'started' || latest.type === 'progress';
  });

  private readonly lastReloadedId = signal<string | null>(null);

  constructor() {
    this._loadSourceKeys();

    effect(
      () => {
        this.filterSeverity();
        this.filterSourceKey();
        untracked(() => {
          this._offset.set(0);
          this.persisted.set([]);
          this._fetch();
        });
      },
      { allowSignalWrites: true },
    );

    effect(
      () => {
        const events = this.mqtt.jobEvents();
        if (events.length === 0) return;
        const latest = events[0];
        if (
          (latest.type === 'completed' || latest.type === 'failed') &&
          latest.report_id !== this.lastReloadedId()
        ) {
          this.lastReloadedId.set(latest.report_id);
          untracked(() => this.reload());
        }
      },
      { allowSignalWrites: true },
    );
  }

  reload(): void {
    this._offset.set(0);
    this.persisted.set([]);
    this._loadSourceKeys();
    this._fetch();
  }

  loadMore(): void {
    this._offset.update((o) => o + PAGE_SIZE);
    this._fetch();
  }

  private _fetch(): void {
    this.persistedLoading.set(true);
    this.persistedError.set(null);
    const offset = this._offset();
    const severity = this.filterSeverity();
    const source_key = this.filterSourceKey();
    this.api
      .list({
        limit: PAGE_SIZE,
        offset,
        ...(severity && { severity }),
        ...(source_key && { source_key }),
      })
      .subscribe({
        next: (resp) => {
          if (offset === 0) {
            this.persisted.set(resp.items);
          } else {
            this.persisted.update((list) => [...list, ...resp.items]);
          }
          this.persistedTotal.set(resp.total);
          this.persistedLoading.set(false);
        },
        error: (err) => {
          this.persistedError.set(err?.message ?? 'Failed to load explanations');
          this.persistedLoading.set(false);
        },
      });
  }

  private _loadSourceKeys(): void {
    this.api.listSourceKeys().subscribe({
      next: (keys) => this.sourceKeys.set(keys),
    });
  }

  setFeedback(id: string, feedback: ExplanationFeedback): void {
    this.api.setFeedback(id, feedback).subscribe({
      next: (updated) => {
        this.persisted.update((list) => list.map((r) => (r.id === updated.id ? updated : r)));
      },
    });
  }

  augment(id: string): {
    loading: ReturnType<typeof signal<boolean>>;
    result: ReturnType<typeof signal<AugmentResponse | null>>;
    error: ReturnType<typeof signal<string | null>>;
  } {
    const loading = signal(true);
    const result = signal<AugmentResponse | null>(null);
    const error = signal<string | null>(null);

    this.api.augment(id).subscribe({
      next: (resp) => {
        result.set(resp);
        loading.set(false);
        this.persisted.update((list) =>
          list.map((r) => (r.id === id ? { ...r, augmented_result: resp } : r)),
        );
      },
      error: (err) => {
        error.set(err?.error?.detail ?? 'Augmentation failed');
        loading.set(false);
      },
    });

    return { loading, result, error };
  }
}
