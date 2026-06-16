import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { severityDotClass, severityTextClass, type ExplainerSeverity } from '../../core/contracts';

@Component({
  selector: 'app-severity-dot',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="flex items-center gap-1.5">
      <span class="inline-block size-2 rounded-full" [class]="dotClass()"></span>
      @if (showLabel()) {
        <span class="text-xs font-medium" [class]="textClass()">{{ severity() }}</span>
      }
    </div>
  `,
})
export class SeverityDotComponent {
  readonly severity = input.required<ExplainerSeverity>();
  readonly showLabel = input(true);

  protected dotClass = () => severityDotClass(this.severity());
  protected textClass = () => severityTextClass(this.severity());
}
