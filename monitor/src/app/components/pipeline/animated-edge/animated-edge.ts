import { Component, computed, inject, input } from '@angular/core';
import {
  NgDiagramBaseEdgeComponent,
  NgDiagramBaseEdgeLabelComponent,
  type Edge,
  type NgDiagramEdgeTemplate,
} from 'ng-diagram';
import { MqttService } from '../../../services/mqtt/mqtt.service';
import { RabbitmqApiService } from '../../../services/rabbitmq/rabbitmq-api.service';
import { AnimatedEdgeData } from '../../../models/pipeline.model';

@Component({
  selector: 'app-animated-edge',
  imports: [NgDiagramBaseEdgeComponent, NgDiagramBaseEdgeLabelComponent],
  template: `
    <ng-diagram-base-edge
      [edge]="edge()"
      stroke="var(--color-border-default)"
      [strokeWidth]="2"
      targetArrowhead="arrow-large"
      [class.is-flowing]="isFlowing()"
      [class.is-dashed]="isDashed()"
      [class.is-mcp-active]="isMcpActive()"
    >
      @if (edgeLabel(); as label) {
        <ng-diagram-base-edge-label [id]="edge().id + '-label'" [positionOnEdge]="labelPosition()">
          <span class="edge-label">{{ label }}</span>
        </ng-diagram-base-edge-label>
      }
    </ng-diagram-base-edge>
  `,
  styles: [
    `
      :host ::ng-deep ng-diagram-base-edge.is-flowing path {
        stroke: var(--color-accent) !important;
        stroke-dasharray: 6 14;
        animation: flow-dash 1s linear infinite;
      }
      :host ::ng-deep ng-diagram-base-edge.is-dashed path {
        stroke-dasharray: 4 4;
        opacity: 0.5;
      }
      :host ::ng-deep ng-diagram-base-edge.is-mcp-active path {
        stroke: var(--color-accent) !important;
        stroke-dasharray: 3 22;
        opacity: 1;
        animation: mcp-particle 0.9s linear infinite;
      }
      @keyframes flow-dash {
        to {
          stroke-dashoffset: -20;
        }
      }
      @keyframes mcp-particle {
        to {
          stroke-dashoffset: -25;
        }
      }
      .edge-label {
        font-size: 0.7rem;
        color: var(--color-neutral-300);
        background: var(--color-surface-raised);
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid var(--color-border-default);
        white-space: nowrap;
      }
    `,
  ],
})
export class AnimatedEdgeComponent implements NgDiagramEdgeTemplate {
  readonly edge = input.required<Edge>();
  private readonly mqtt = inject(MqttService);
  private readonly rabbitmq = inject(RabbitmqApiService);

  protected readonly isFlowing = computed(() => {
    const data = this.edge().data as AnimatedEdgeData | undefined;

    if (data?.animated === false) return false;

    return this.mqtt.connected() && this.mqtt.simulatorState() === 'playing';
  });

  protected readonly isMcpActive = computed(() => {
    const data = this.edge().data as AnimatedEdgeData | undefined;
    if (!data?.mcpAnimated) return false;
    return (this.rabbitmq.queueStats()?.messages_unacknowledged ?? 0) > 0;
  });

  protected readonly isDashed = computed(() => {
    const data = this.edge().data as AnimatedEdgeData | undefined;
    if (data?.mcpAnimated && this.isMcpActive()) return false;
    return data?.dashed === true;
  });

  protected readonly edgeLabel = computed(() => {
    const data = this.edge().data as AnimatedEdgeData | undefined;
    return data?.label;
  });

  protected readonly labelPosition = computed(() => {
    const data = this.edge().data as AnimatedEdgeData | undefined;
    return data?.positionOnEdge ?? 0.5;
  });
}
