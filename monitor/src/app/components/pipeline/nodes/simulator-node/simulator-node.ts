import { Component, computed, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MqttService } from '../../../../services/mqtt/mqtt.service';

import { LucideSolarPanel } from '@lucide/angular';
import { iconBgClass, NODE_STATUS } from '../../../../utils/shared-converters';
import { LiveSignalWave } from '../../../../ui/live-signal-wave/live-signal-wave';

@Component({
  selector: 'app-simulator-content',
  imports: [DatePipe, LucideSolarPanel, LiveSignalWave],
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
        <svg lucideSolarPanel></svg>
      </div>
    </div>

    <div class="flex justify-center">
      @if (mqtt.simulatedTime(); as st) {
        <p class="font-mono text-sm text-neutral-200">{{ st | date: 'dd MMM HH:mm' }}</p>
      } @else {
        <p class="text-xs text-neutral-400">No data</p>
      }
    </div>

    <div class="-mx-3 -mb-3 md:-mx-5 md:-mb-5 h-20">
      <app-live-signal-wave [state]="mqtt.simulatorState()" [value]="normalizedPower()" />
    </div>
  `,
})
export class SimulatorNodeContent {
  protected readonly mqtt = inject(MqttService);
  private readonly status = inject(NODE_STATUS);
  protected readonly iconBg = computed(() => iconBgClass(this.status()));

  protected readonly normalizedPower = computed((): number | null => {
    const map = this.mqtt.telemetryMap();
    if (!map.size) return null;

    let total = 0;
    for (const p of map.values()) total += p.IRRADIATION;
    return total / map.size;
  });
}
