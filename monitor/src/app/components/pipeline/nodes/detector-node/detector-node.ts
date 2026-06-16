import { Component, computed, inject } from '@angular/core';
import { MqttService } from '../../../../services/mqtt/mqtt.service';

import { LucideRadar } from '@lucide/angular';
import { DatePipe } from '@angular/common';
import { iconBgClass, NODE_STATUS } from '../../../../utils/shared-converters';

@Component({
  selector: 'app-detector-content',
  imports: [DatePipe, LucideRadar],
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
        <svg lucideRadar></svg>
      </div>
    </div>

    <div class="flex flex-col items-center gap-1">
      <p class="font-mono text-sm text-neutral-200">
        {{
          (mqtt.anomalies().at(-1)?.detections?.at(-1)?.timestamp | date: 'dd MMM HH:mm') ?? 'N/A'
        }}
      </p>
      <p class="text-xs text-neutral-400">Last timestamp</p>
    </div>

    <div class="flex w-full justify-evenly">
      <div class="flex-1 text-center">
        <p class="font-mono text-sm text-neutral-200">{{ mqtt.anomalyCount() }}</p>
        <p class="text-xs text-neutral-400">Anomalies detected</p>
      </div>
    </div>
  `,
})
export class DetectorNodeContent {
  protected readonly mqtt = inject(MqttService);
  private readonly status = inject(NODE_STATUS);
  protected readonly iconBg = computed(() => iconBgClass(this.status()));
}
