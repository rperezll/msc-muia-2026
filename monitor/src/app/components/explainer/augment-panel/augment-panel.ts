import { ChangeDetectionStrategy, Component, Signal, input } from '@angular/core';
import { DecimalPipe } from '@angular/common';

import type { AugmentResponse } from '../../../core/contracts';

@Component({
  selector: 'app-augment-panel',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DecimalPipe],
  template: `
    @if (loading()()) {
      <div class="flex items-center gap-2 py-4 text-neutral-400">
        <span
          class="inline-block size-3 animate-spin rounded-full border-2 border-neutral-400 border-t-transparent"
        ></span>
        <span class="text-sm">Querying knowledge base...</span>
      </div>
    } @else if (error()()) {
      <div class="rounded-md border border-status-error/20 bg-status-error/5 p-3">
        <p class="text-sm text-status-error">{{ error()() }}</p>
      </div>
    } @else if (result()()) {
      <div class="flex flex-col gap-5 animate-[fade-in-up_0.15s_ease-out]">
        <div class="flex flex-col gap-2">
          <p class="text-xs font-medium uppercase tracking-wider text-neutral-300">
            Augmented explanation
            <span class="ml-1 font-mono text-[10px] text-neutral-500">{{ result()()!.model }}</span>
          </p>
          <p class="text-sm leading-relaxed text-neutral-100">
            {{ result()()!.augmented_summary }}
          </p>
        </div>

        @if (result()()!.retrieved.length > 0) {
          <div class="flex flex-col gap-2">
            <p class="text-xs font-medium uppercase tracking-wider text-neutral-300">
              Retrieved documentation ({{ result()()!.retrieved.length }})
            </p>
            <ul class="flex flex-col gap-2">
              @for (doc of result()()!.retrieved; track $index) {
                <li class="rounded-md border border-border-default bg-surface-overlay p-3">
                  <p class="text-sm font-medium text-neutral-100">{{ doc.title ?? 'Document' }}</p>
                  @if (doc.source) {
                    <p class="font-mono text-xs text-neutral-400">{{ doc.source }}</p>
                  }
                  <p class="mt-1 text-xs text-neutral-300">{{ doc.snippet }}</p>
                  @if (doc.score !== null) {
                    <p class="mt-1 font-mono text-[10px] text-neutral-500">
                      score: {{ doc.score | number: '1.3-3' }}
                    </p>
                  }
                </li>
              }
            </ul>
          </div>
        } @else {
          <p class="text-sm text-neutral-400 italic">
            No relevant documentation in the knowledge base. Document ingestion is a prerequisite.
          </p>
        }
      </div>
    }
  `,
})
export class AugmentPanelComponent {
  readonly loading = input.required<Signal<boolean>>();
  readonly result = input.required<Signal<AugmentResponse | null>>();
  readonly error = input.required<Signal<string | null>>();
}
