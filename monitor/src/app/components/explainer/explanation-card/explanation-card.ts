import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { LucideThumbsUp, LucideThumbsDown } from '@lucide/angular';

import {
  ANOMALY_CLASSIFICATION_LABELS,
  formatDetectedAt,
  formatDuration,
  severityBorderClass,
  worstSeverity,
  type ExplanationRecord,
  type ExplainerSeverity,
} from '../../../core/contracts';
import { SeverityBadgeComponent } from '../../../ui/severity-badge/severity-badge';

@Component({
  selector: 'app-explanation-card',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [SeverityBadgeComponent, LucideThumbsUp, LucideThumbsDown],
  styles: `
    @keyframes card-enter {
      from {
        opacity: 0;
        transform: translateX(-24px) scale(0.95);
      }
      to {
        opacity: 1;
        transform: translateX(0) scale(1);
      }
    }
    .card-enter {
      animation: card-enter 350ms ease-out both;
    }

    button {
      will-change: transform;
      transition:
        transform 220ms ease,
        box-shadow 220ms ease,
        background-color 150ms ease;
    }
    button:hover {
      transform: perspective(700px) rotateY(6deg) rotateX(-2deg) translateY(-3px) scale(1.02);
      box-shadow: 6px 14px 28px rgba(0, 0, 0, 0.4);
    }
    button:active {
      transform: perspective(700px) rotateY(3deg) rotateX(-1deg) translateY(-1px) scale(0.99);
      transition-duration: 80ms;
    }
  `,
  templateUrl: './explanation-card.html',
})
export class ExplanationCardComponent {
  readonly record = input.required<ExplanationRecord>();
  readonly recordSelect = output<ExplanationRecord>();

  protected severity(): ExplainerSeverity | null {
    return worstSeverity(this.record().result ?? []);
  }

  protected borderClass(): string {
    const s = this.severity();
    return s ? severityBorderClass(s) : 'border-border-default';
  }

  protected classificationLabel(): string | null {
    const first = this.record().result?.[0];
    const type = first?.rag_search_parameters?.anomaly_type;
    return type ? (ANOMALY_CLASSIFICATION_LABELS[type] ?? type) : null;
  }

  protected detectedAt(): string | null {
    const ts =
      this.record().report?.detections?.[0]?.timestamp ??
      this.record().result?.[0]?.event_metadata?.timestamp ??
      null;
    return ts ? formatDetectedAt(ts) : null;
  }

  protected durationLabel(): string {
    return this.record().duration_ms != null ? formatDuration(this.record().duration_ms!) : '—';
  }
}
