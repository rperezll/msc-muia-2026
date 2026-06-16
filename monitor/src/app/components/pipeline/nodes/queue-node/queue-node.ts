import { Component, computed, inject } from '@angular/core';
import { RabbitmqApiService } from '../../../../services/rabbitmq/rabbitmq-api.service';

import { LucideLogs, LucideTrash } from '@lucide/angular';
import { iconBgClass, NODE_STATUS } from '../../../../utils/shared-converters';
import { DialogService } from '../../../../ui/dialog/dialog.service';

@Component({
  selector: 'app-queue-content',
  imports: [LucideLogs, LucideTrash],
  styles: `
    :host {
      display: flex;
      flex-direction: column;
      flex: 1;
      justify-content: space-between;
    }
    .purge-btn {
      background: var(--color-surface-overlay);
      color: var(--color-neutral-300);
    }
    .purge-btn:hover:not(:disabled) {
      background: var(--color-border-default);
      color: var(--color-neutral-200);
    }
  `,
  template: `
    <div class="flex justify-center">
      <div
        class="flex size-14 items-center justify-center rounded-lg text-neutral-200"
        [class]="iconBg()"
      >
        <svg lucideLogs></svg>
      </div>
    </div>

    @if (rabbitmq.queueStats(); as rb) {
      <div class="flex w-full justify-evenly">
        <div class="flex-1 text-center">
          <p class="font-mono text-sm text-neutral-200">{{ rb.messages_ready }}</p>
          <p class="text-xs text-neutral-400">Ready</p>
        </div>
        <div class="flex-1 text-center">
          <p class="font-mono text-sm text-neutral-200">{{ rb.messages_unacknowledged }}</p>
          <p class="text-xs text-neutral-400">In progress</p>
        </div>
      </div>

      <button
        (click)="purgeAction()"
        [disabled]="rb.messages === 0"
        class="purge-btn cursor-pointer flex w-full items-center justify-center gap-2 rounded-md px-3 py-1.5 text-xs transition-colors disabled:pointer-events-none disabled:opacity-40"
      >
        <svg lucideTrash [size]="14"></svg>
        <span>Clean jobs</span>
      </button>
    } @else {
      <div class="flex flex-col items-center gap-1">
        <p class="text-xs text-neutral-400">Offline</p>
      </div>
      <div></div>
    }
  `,
})
export class QueueNodeContent {
  protected readonly rabbitmq = inject(RabbitmqApiService);
  private readonly status = inject(NODE_STATUS);
  protected readonly iconBg = computed(() => iconBgClass(this.status()));
  private readonly dialog = inject(DialogService);

  protected executePurge(): void {
    this.rabbitmq.purgeQueue();
  }

  protected purgeAction(): void {
    const purgeDialog = this.dialog.confirm({
      title: 'Clean Jobs',
      description:
        'Are you sure you want to purge the RabbitMQ job queue? This will permanently delete all pending messages and cannot be undone.',
      confirmLabel: 'Yes, purge it',
    });

    purgeDialog.closed.subscribe((result) => {
      if (result) {
        this.executePurge();
      }
    });
  }
}
