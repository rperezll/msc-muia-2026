import { Component, computed, inject } from '@angular/core';

import { LucideSparkles } from '@lucide/angular';
import { iconBgClass, NODE_STATUS } from '../../../../utils/shared-converters';
import { RabbitmqApiService } from '../../../../services/rabbitmq/rabbitmq-api.service';
import { MqttService } from '../../../../services/mqtt/mqtt.service';

@Component({
  selector: 'app-explainer-content',
  imports: [LucideSparkles],
  styles: `
    :host {
      display: flex;
      flex-direction: column;
      flex: 1;
      justify-content: space-between;
    }
  `,
  template: `
    <div class="flex justify-center">
      <div
        class="flex size-14 items-center justify-center rounded-lg text-neutral-200"
        [class]="iconBg()"
      >
        <svg lucideSparkles></svg>
      </div>
    </div>

    <div class="flex flex-col items-center gap-1">
      <p class="text-xs text-neutral-400">Status</p>
      @if (processing()) {
        <p class="font-mono text-sm text-status-warning">Processing</p>
      } @else {
        <p class="font-mono text-sm text-neutral-200">Idle</p>
      }
    </div>

    <div class="flex w-full justify-evenly">
      <div class="flex-1 text-center">
        <p class="font-mono text-sm text-status-ok">{{ mqtt.completedJobs() }}</p>
        <p class="text-xs text-neutral-400">Done</p>
      </div>
      <div class="flex-1 text-center">
        <p
          class="font-mono text-sm"
          [class.text-status-error]="mqtt.failedJobs() > 0"
          [class.text-neutral-200]="mqtt.failedJobs() === 0"
        >
          {{ mqtt.failedJobs() }}
        </p>
        <p class="text-xs text-neutral-400">Failed</p>
      </div>
    </div>
  `,
})
export class ExplainerNodeContent {
  protected readonly rabbitmq = inject(RabbitmqApiService);
  protected readonly mqtt = inject(MqttService);
  private readonly status = inject(NODE_STATUS);
  protected readonly iconBg = computed(() => iconBgClass(this.status()));
  protected readonly processing = computed(
    () => (this.rabbitmq.queueStats()?.messages_unacknowledged ?? 0) > 0,
  );
}
