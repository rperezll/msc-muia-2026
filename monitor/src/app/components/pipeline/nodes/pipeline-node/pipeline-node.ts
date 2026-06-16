import { Component, computed, inject, input, Injector } from '@angular/core';
import { NgComponentOutlet } from '@angular/common';
import { NgDiagramPortComponent, type NgDiagramNodeTemplate, type Node } from 'ng-diagram';
import { MqttService } from '../../../../services/mqtt/mqtt.service';
import { RabbitmqApiService } from '../../../../services/rabbitmq/rabbitmq-api.service';
import { NodeStatus, PipelineNodeData } from '../../../../models/pipeline.model';
import { NODE_STATUS } from '../../../../utils/shared-converters';
import { PipelineLayoutService } from '../../../../services/pipeline/pipeline-layout.service';

@Component({
  selector: 'app-pipeline-node',
  imports: [NgComponentOutlet, NgDiagramPortComponent],
  templateUrl: './pipeline-node.html',
  styles: [
    `
      :host {
        display: block;
        width: max-content;
      }
      .animate-pulse-ring {
        animation: pulse-ring 1s ease-out infinite;
      }
      .beam-border {
        padding: 2px;
      }
    `,
  ],
})
export class PipelineNodeComponent implements NgDiagramNodeTemplate<PipelineNodeData> {
  readonly node = input.required<Node<PipelineNodeData>>();

  private readonly parentInjector = inject(Injector);
  private readonly mqtt = inject(MqttService);
  private readonly rabbitmq = inject(RabbitmqApiService);
  private readonly layoutService = inject(PipelineLayoutService);

  protected readonly data = computed(() => this.node().data);
  protected readonly activePorts = computed(
    () => this.layoutService.activePorts().get(this.node().id) ?? new Set<string>(),
  );

  protected readonly status = computed<NodeStatus>(() => {
    const t = this.data().type;
    if (t === 'simulator' || t === 'detector') {
      if (!this.mqtt.connected()) return 'offline';
      return this.mqtt.simulatorState() === 'playing' ? 'online' : 'offline';
    }
    if (t === 'queue') return this.rabbitmq.connected() ? 'online' : 'offline';
    if (t === 'explainer') {
      if (!this.rabbitmq.connected()) return 'offline';
      const stats = this.rabbitmq.queueStats();
      if (!stats) return 'offline';
      return stats.consumers > 0 ? 'online' : 'offline';
    }
    return 'disabled';
  });

  protected readonly pulse = computed(() => {
    if (this.data().type === 'detector') return this.mqtt.anomalyPulse();
    if (this.data().type === 'queue') return this.rabbitmq.queuePulse();
    return false;
  });

  protected readonly beaming = computed(
    () =>
      this.data().type === 'explainer' &&
      (this.rabbitmq.queueStats()?.messages_unacknowledged ?? 0) > 0,
  );

  protected readonly contentInjector = Injector.create({
    providers: [{ provide: NODE_STATUS, useValue: this.status }],
    parent: this.parentInjector,
  });

  protected readonly statusLabel = computed(() => {
    switch (this.status()) {
      case 'online':
        return 'OK';
      case 'offline':
        return 'DOWN';
      case 'disabled':
        return 'N/A';
    }
  });

  protected readonly statusBadgeClass = computed(() => {
    switch (this.status()) {
      case 'online':
        return 'bg-status-ok/15 text-status-ok';
      case 'offline':
        return 'bg-status-error/15 text-status-error';
      case 'disabled':
        return 'bg-surface-overlay text-neutral-400';
    }
  });

  protected readonly borderClass = computed(() => {
    switch (this.status()) {
      case 'online':
        return 'border-border-default';
      case 'offline':
        return 'border-status-error/30';
      case 'disabled':
        return 'border-border-subtle';
    }
  });
}
