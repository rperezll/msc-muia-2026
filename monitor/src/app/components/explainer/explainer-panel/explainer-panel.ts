import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import {
  LucideChevronDown,
  LucideChevronRight,
  LucideSparkles,
  LucideTrash2,
} from '@lucide/angular';

import { DialogService } from '../../../ui/dialog/dialog.service';
import { ExplanationsStore } from '../../../services/explanations/explanations.store';
import { ExplanationCardComponent } from '../explanation-card/explanation-card';
import { ExplainerDetailComponent } from '../explainer-detail/explainer-detail';
import type { ExplanationRecord, ExplainerSeverity } from '../../../core/contracts';

const SEVERITY_OPTIONS: { value: ExplainerSeverity; label: string }[] = [
  { value: 'CRITICAL', label: 'Critical' },
  { value: 'HIGH', label: 'High' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'LOW', label: 'Low' },
];

@Component({
  selector: 'app-explainer-panel',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    LucideSparkles,
    LucideChevronDown,
    LucideChevronRight,
    LucideTrash2,
    ExplanationCardComponent,
  ],
  templateUrl: './explainer-panel.html',
})
export class ExplainerPanelComponent {
  protected readonly store = inject(ExplanationsStore);
  private readonly dialog = inject(DialogService);

  protected readonly severityOptions = SEVERITY_OPTIONS;

  protected onSeverityChange(event: Event): void {
    const value = (event.target as HTMLSelectElement).value;
    this.store.filterSeverity.set(value ? (value as ExplainerSeverity) : null);
  }

  protected onSourceKeyChange(event: Event): void {
    const value = (event.target as HTMLSelectElement).value;
    this.store.filterSourceKey.set(value || null);
  }

  protected clearFilters(): void {
    this.store.filterSeverity.set(null);
    this.store.filterSourceKey.set(null);
  }

  protected openDetail(record: ExplanationRecord): void {
    this.dialog.open(ExplainerDetailComponent, {
      data: { record },
      classNames: {
        showHeader: false,
        container: '!max-w-4xl',
        content: '!p-0 overflow-hidden',
      },
    });
  }
}
