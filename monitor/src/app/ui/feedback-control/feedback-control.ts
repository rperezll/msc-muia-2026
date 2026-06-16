import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { LucideThumbsUp, LucideThumbsDown } from '@lucide/angular';

import type { ExplanationFeedback } from '../../core/contracts';

@Component({
  selector: 'app-feedback-control',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [LucideThumbsUp, LucideThumbsDown],
  template: `
    <div class="flex items-center gap-1">
      <button
        type="button"
        title="Helpful"
        (click)="onVote('up')"
        class="cursor-pointer rounded p-1.5 transition-colors"
        [class]="
          feedback() === 'up'
            ? 'text-status-ok bg-status-ok/10'
            : 'text-neutral-400 hover:text-status-ok hover:bg-status-ok/10'
        "
      >
        <svg lucideThumbsUp [size]="16" [strokeWidth]="2"></svg>
      </button>
      <button
        type="button"
        title="Not helpful"
        (click)="onVote('down')"
        class="cursor-pointer rounded p-1.5 transition-colors"
        [class]="
          feedback() === 'down'
            ? 'text-status-error bg-status-error/10'
            : 'text-neutral-400 hover:text-status-error hover:bg-status-error/10'
        "
      >
        <svg lucideThumbsDown [size]="16" [strokeWidth]="2"></svg>
      </button>
    </div>
  `,
})
export class FeedbackControlComponent {
  readonly feedback = input<ExplanationFeedback>(null);
  readonly vote = output<ExplanationFeedback>();

  onVote(v: 'up' | 'down'): void {
    this.vote.emit(this.feedback() === v ? null : v);
  }
}
