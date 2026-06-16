import { Type } from '@angular/core';

export type NodeStatus = 'online' | 'offline' | 'disabled';
export type NodeType = 'simulator' | 'detector' | 'queue' | 'explainer';

export interface PipelineNodeData {
  label: string;
  type: NodeType;
  content: Type<unknown>;
}

export interface McpNodeData {
  label: string;
}

export interface AnimatedEdgeData {
  animated?: boolean;
  dashed?: boolean;
  mcpAnimated?: boolean;
  label?: string;
  positionOnEdge?: number;
}
