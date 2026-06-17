import { ChangeDetectionStrategy, Component, Signal, input, signal } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { LucideFileText, LucideSparkles } from '@lucide/angular';

import type { AugmentResponse } from '../../../core/contracts';
import { EmbeddingCanvasComponent } from '../embedding-canvas/embedding-canvas';

@Component({
  selector: 'app-augment-panel',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DecimalPipe, LucideFileText, LucideSparkles, EmbeddingCanvasComponent],
  template: `
    <div class="grid transition-[grid-template-rows] duration-500 ease-in-out" [style.grid-template-rows]="result()() || error()() ? '0fr' : '1fr'">
      <!-- fila colapsable: canvas idle/loading -->
      <div class="overflow-hidden">
        <div class="relative h-52 w-full overflow-hidden rounded-md">
          <app-embedding-canvas [loading]="loading()()" class="absolute inset-0 h-full w-full" />
          <div class="absolute inset-0 z-10 flex flex-col items-center justify-center gap-2 px-6 text-center">
            @if (!loading()()) {
              <svg lucideSparkles [size]="32" [strokeWidth]="1.5" class="text-neutral-300 filter-[drop-shadow(0_1px_6px_rgba(0,0,0,0.9))] animate-[fade-in-up_0.2s_ease-out]"></svg>
              <p class="text-sm font-semibold text-white [text-shadow:0_1px_8px_rgba(0,0,0,0.9)] animate-[fade-in-up_0.2s_ease-out]">
                Augment with Knowledge Base
              </p>
              <p class="text-xs text-neutral-300 [text-shadow:0_1px_6px_rgba(0,0,0,0.9)] animate-[fade-in-up_0.2s_ease-out]">
                Search the documentary knowledge base to enrich this explanation.
              </p>
            } @else {
              <p class="text-sm font-semibold text-neutral-300 [text-shadow:0_1px_6px_rgba(0,0,0,0.9)] animate-[fade-in-up_0.2s_ease-out]">
                Augmenting…
              </p>
            }
          </div>
        </div>
      </div>
    </div>

    @if (error()()) {
      <div class="rounded-md border border-status-error/20 bg-status-error/5 p-3 animate-[fade-in-up_0.3s_ease-out]">
        <p class="text-sm text-status-error">{{ error()() }}</p>
      </div>
    } @else if (result()()) {
      <div class="flex flex-col gap-5 animate-[fade-in-up_0.3s_ease-out]">
        <div class="flex flex-col gap-2">
          <p class="text-xs font-medium uppercase tracking-wider text-neutral-300">
            Augmented explanation
          </p>
          <p class="text-sm leading-relaxed text-neutral-100">
            {{ result()()!.augmented_summary }}
          </p>
        </div>

        @if (result()()!.retrieved.length > 0) {
          <div class="flex flex-col gap-2">
            <p class="text-xs font-medium uppercase tracking-wider text-neutral-300">
              Sources ({{ result()()!.retrieved.length }})
            </p>
            <ul class="flex flex-col gap-1.5">
              @for (doc of result()()!.retrieved; track $index) {
                <li class="overflow-hidden rounded-md border border-border-default bg-surface-overlay">
                  <button
                    type="button"
                    (click)="toggleDoc($index)"
                    class="flex w-full cursor-pointer items-center justify-between gap-3 px-3 py-2 text-left transition-colors hover:bg-white/5"
                  >
                    <div class="flex min-w-0 items-center gap-2">
                      <svg
                        lucideFileText
                        [size]="14"
                        [strokeWidth]="1.5"
                        class="shrink-0 transition-colors"
                        [class]="openDocIdx() === $index ? 'text-neutral-300' : 'text-neutral-500'"
                      ></svg>
                      <span class="truncate font-mono text-xs text-neutral-100">
                        {{ doc.source ?? doc.title ?? 'Document' }}
                      </span>
                    </div>
                    <div class="flex shrink-0 items-center gap-2">
                      @if (doc.score !== null) {
                        <span class="font-mono text-[10px] text-neutral-500">
                          {{ doc.score | number: '1.2-2' }}
                        </span>
                      }
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="12"
                        height="12"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        class="text-neutral-400 transition-transform duration-150"
                        [class.rotate-180]="openDocIdx() === $index"
                      >
                        <polyline points="6 9 12 15 18 9" />
                      </svg>
                    </div>
                  </button>
                  @if (openDocIdx() === $index) {
                    <div
                      class="border-t border-border-default px-3 py-2.5 animate-[fade-in-up_0.1s_ease-out]"
                    >
                      <p class="text-xs leading-relaxed text-neutral-300">{{ doc.snippet }}</p>
                    </div>
                  }
                </li>
              }
            </ul>
          </div>
        } @else {
          <p class="text-sm italic text-neutral-400">
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

  protected readonly openDocIdx = signal<number | null>(null);

  protected toggleDoc(idx: number): void {
    this.openDocIdx.update((current) => (current === idx ? null : idx));
  }
}
