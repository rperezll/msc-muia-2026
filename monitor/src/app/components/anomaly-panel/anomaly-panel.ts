import { ChangeDetectionStrategy, Component, inject, signal, effect } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { MqttService } from '../../services/mqtt/mqtt.service';

import { LucideChevronRight, LucideShieldCheck } from '@lucide/angular';

@Component({
  selector: 'app-anomaly-panel',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DatePipe, DecimalPipe, LucideChevronRight, LucideShieldCheck],
  templateUrl: './anomaly-panel.html',
  styles: [
    `
      .animate-fade-in {
        animation: fade-in-up 0.3s ease-out;
      }

      .collapsible-grid {
        display: grid;
        grid-template-rows: 0fr;
        transition: grid-template-rows 0.3s ease;
      }

      .collapsible-grid.expanded {
        grid-template-rows: 1fr;
      }
    `,
  ],
})
export class AnomalyPanelComponent {
  protected readonly mqtt = inject(MqttService);
  protected readonly expandedId = signal<string | null>(null);

  constructor() {
    effect(() => {
      const list = this.mqtt.anomalies();
      if (list.length > 0) {
        this.expandedId.set(list[0].report_id);
      }
    });
  }

  protected toggle(reportId: string): void {
    this.expandedId.update((current) => (current === reportId ? null : reportId));
  }
}
