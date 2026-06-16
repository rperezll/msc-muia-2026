import { ChangeDetectionStrategy, Component, computed, inject, input, signal } from '@angular/core';
import { DecimalPipe, DatePipe } from '@angular/common';
import { LucideSearch, LucideX, LucideSparkles } from '@lucide/angular';
import { DialogRef } from '@angular/cdk/dialog';

import {
  ANOMALY_CLASSIFICATION_LABELS,
  formatDuration,
  worstSeverity,
  type AnomalyDetection,
  type AnomalyClassification,
  type ExplanationFeedback,
  type ExplanationRecord,
  type ExplainerSeverity,
} from '../../../core/contracts';
import { ExplanationsStore } from '../../../services/explanations/explanations.store';
import { FeedbackControlComponent } from '../../../ui/feedback-control/feedback-control';
import { AugmentPanelComponent } from '../augment-panel/augment-panel';
import { SeverityBadgeComponent } from '../../../ui/severity-badge/severity-badge';

type Tab = 1 | 2 | 3;

@Component({
  selector: 'app-explainer-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DecimalPipe,
    DatePipe,
    LucideSearch,
    LucideX,
    LucideSparkles,
    FeedbackControlComponent,
    AugmentPanelComponent,
    SeverityBadgeComponent,
  ],
  templateUrl: './explainer-detail.html',
})
export class ExplainerDetailComponent {
  readonly record = input.required<ExplanationRecord>();

  readonly dialogRef = inject(DialogRef);
  private readonly store = inject(ExplanationsStore);

  readonly activeTab = signal<Tab>(1);

  readonly tabs = [
    { id: 1 as Tab, label: 'Explanation' },
    { id: 2 as Tab, label: 'Telemetry Sources' },
    { id: 3 as Tab, label: 'Augment' },
  ];

  readonly incidents = computed(() => this.record().result ?? []);
  readonly topSeverity = computed<ExplainerSeverity | null>(() => worstSeverity(this.incidents()));
  readonly detections = computed<AnomalyDetection[]>(() => this.record().report?.detections ?? []);

  readonly liveFeedback = computed<ExplanationFeedback>(() => {
    const id = this.record().id;
    const live = this.store.persisted().find((r) => r.id === id);
    return (live?.feedback ?? this.record().feedback) as ExplanationFeedback;
  });
  readonly detectedAt = computed<string | null>(() => {
    const ts =
      this.record().report?.detections?.[0]?.timestamp ??
      this.incidents()[0]?.event_metadata?.timestamp ??
      null;
    if (!ts) return null;
    try {
      const d = new Date(ts);
      const day = d.getDate().toString().padStart(2, '0');
      const month = d.toLocaleString('en-GB', { month: 'short' });
      const time = d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
      return `${day} ${month} ${time}`;
    } catch {
      return ts;
    }
  });

  protected augmentState = signal<ReturnType<ExplanationsStore['augment']> | null>(null);

  protected runAugment(): void {
    this.augmentState.set(this.store.augment(this.record().id));
  }

  protected onFeedback(feedback: ExplanationFeedback): void {
    this.store.setFeedback(this.record().id, feedback);
  }

  protected classificationLabel(type: AnomalyClassification | string): string {
    return ANOMALY_CLASSIFICATION_LABELS[type as AnomalyClassification] ?? type;
  }

  protected readonly formatDuration = formatDuration;
}
