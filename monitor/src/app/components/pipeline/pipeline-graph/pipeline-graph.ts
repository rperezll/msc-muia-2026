import {
  Component,
  ChangeDetectionStrategy,
  ElementRef,
  DestroyRef,
  inject,
  afterNextRender,
} from '@angular/core';

import { PipelineLayoutService } from '../../../services/pipeline/pipeline-layout.service';

import {
  NgDiagramComponent,
  NgDiagramMarkerComponent,
  provideNgDiagram,
  initializeModel,
  NgDiagramNodeTemplateMap,
  NgDiagramEdgeTemplateMap,
  NgDiagramModelService,
  NgDiagramViewportService,
  type NgDiagramConfig,
} from 'ng-diagram';

import { PipelineNodeComponent } from '../nodes/pipeline-node/pipeline-node';
import { AnimatedEdgeComponent } from '../animated-edge/animated-edge';

import { Definition, Dimensions, Nodes } from './pipeline-definition';

@Component({
  selector: 'app-pipeline-graph',
  imports: [NgDiagramComponent, NgDiagramMarkerComponent],
  providers: [provideNgDiagram()],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ng-diagram
      [model]="model"
      [config]="config"
      [nodeTemplateMap]="nodeTemplateMap"
      [edgeTemplateMap]="edgeTemplateMap"
      (diagramInit)="onDiagramInit()"
    >
    </ng-diagram>

    <ng-diagram-marker>
      <svg style="width:0;height:0;overflow:hidden">
        <defs>
          <marker
            id="arrow-large"
            viewBox="0 9 8 14"
            refX="6"
            refY="16"
            markerWidth="8"
            markerHeight="14"
            orient="auto-start-reverse"
          >
            <path
              d="M1 21L6 16L1 11"
              stroke="context-stroke"
              fill="none"
              stroke-width="1"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </marker>
        </defs>
      </svg>
    </ng-diagram-marker>
  `,
  styles: `
    :host {
      display: flex;
      height: 100%;
      width: 100%;
    }
    ng-diagram {
      --ngd-diagram-background-color: transparent;
      --ngd-background-dot-color: var(--color-border-subtle, #333);
    }
  `,
})
export class PipelineGraphComponent {
  private readonly el = inject(ElementRef);
  private readonly destroyRef = inject(DestroyRef);
  private readonly modelService = inject(NgDiagramModelService);
  private readonly viewportService = inject(NgDiagramViewportService);
  private readonly layoutService = inject(PipelineLayoutService);

  private readonly edgeNodeMap = new Map(
    Definition.edges.map((e) => [e.id, { source: e.source, target: e.target }]),
  );

  private resizeObserver?: ResizeObserver;
  private currentCols = 0;
  private initialized = false;

  nodeTemplateMap = new NgDiagramNodeTemplateMap([['pipeline-node', PipelineNodeComponent]]);

  edgeTemplateMap = new NgDiagramEdgeTemplateMap([['animated-edge', AnimatedEdgeComponent]]);

  config: NgDiagramConfig = {
    nodeDraggingEnabled: false,
    hideWatermark: true,
    resize: { defaultResizable: false },
    nodeRotation: { defaultRotatable: false },
  };

  model = initializeModel(Definition);

  constructor() {
    afterNextRender(() => {
      this.resizeObserver = new ResizeObserver((entries) => {
        if (!this.initialized) return;
        const { width, height } = entries[0].contentRect;
        this.applyLayout(width, height);
      });
      this.resizeObserver.observe(this.el.nativeElement);
      this.destroyRef.onDestroy(() => this.resizeObserver?.disconnect());
    });
  }

  onDiagramInit(): void {
    this.initialized = true;
    const { width, height } = this.el.nativeElement.getBoundingClientRect();
    this.applyLayout(width, height, true);
  }

  private applyLayout(containerWidth: number, containerHeight: number, force = false): void {
    const cols = this.computeColumns(containerWidth, containerHeight);
    if (!force && cols === this.currentCols) {
      this.scheduleZoomToFit();
      return;
    }
    this.currentCols = cols;

    const mainPositions = Nodes.MAIN_NODE_IDS.map((id, i) => ({
      id,
      position: {
        x: (i % cols) * (Dimensions.NODE_W + Dimensions.GAP_X),
        y: Math.floor(i / cols) * (Dimensions.NODE_H + Dimensions.GAP_Y),
      },
    }));

    this.modelService.updateNodes(mainPositions);

    const edgeUpdates = Nodes.MAIN_EDGE_DEFS.map(({ id, sourceIdx, targetIdx }) => {
      const sameRow = Math.floor(sourceIdx / cols) === Math.floor(targetIdx / cols);
      return {
        id,
        sourcePort: sameRow ? 'port-right' : 'port-bottom',
        targetPort: sameRow ? 'port-left' : 'port-top',
      };
    });

    this.modelService.updateEdges(edgeUpdates);

    const portsMap = new Map<string, Set<string>>();
    const addPort = (nodeId: string, portId: string) => {
      if (!portsMap.has(nodeId)) portsMap.set(nodeId, new Set());
      portsMap.get(nodeId)!.add(portId);
    };
    for (const eu of edgeUpdates) {
      const nodes = this.edgeNodeMap.get(eu.id);
      if (nodes) {
        addPort(nodes.source, eu.sourcePort);
        addPort(nodes.target, eu.targetPort);
      }
    }
    this.layoutService.update(portsMap);

    this.scheduleZoomToFit();
  }

  private zoomTimer?: ReturnType<typeof setTimeout>;

  private scheduleZoomToFit(): void {
    clearTimeout(this.zoomTimer);
    this.zoomTimer = setTimeout(() => this.viewportService.zoomToFit({ padding: 20 }), 50);
  }

  private computeColumns(width: number, height: number): number {
    const nodeCount = Nodes.MAIN_NODE_IDS.length;
    const padding = 40;
    const availW = Math.max(1, width - padding);
    const availH = Math.max(1, height - padding);

    let bestCols = 1;
    let bestZoom = 0;

    for (let cols = 1; cols <= nodeCount; cols++) {
      const rows = Math.ceil(nodeCount / cols);
      const bboxW = cols * Dimensions.NODE_W + (cols - 1) * Dimensions.GAP_X;
      const bboxH = rows * Dimensions.NODE_H + (rows - 1) * Dimensions.GAP_Y;
      const zoom = Math.min(availW / bboxW, availH / bboxH);
      if (zoom > bestZoom) {
        bestZoom = zoom;
        bestCols = cols;
      }
    }

    return bestCols;
  }
}
