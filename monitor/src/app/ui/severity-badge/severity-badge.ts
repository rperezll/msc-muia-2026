import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { severityBadgeClass, type ExplainerSeverity } from '../../core/contracts';

@Component({
  selector: 'app-severity-badge',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span
      class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold uppercase tracking-wide"
      [class]="badgeClass()"
    >
      {{ severity() }}
    </span>
  `,
})
export class SeverityBadgeComponent {
  readonly severity = input.required<ExplainerSeverity>();

  protected badgeClass = () => severityBadgeClass(this.severity());
}
