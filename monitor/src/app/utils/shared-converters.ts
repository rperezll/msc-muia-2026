import { InjectionToken, Signal } from '@angular/core';
import type { NodeStatus } from '../models/pipeline.model';

export const NODE_STATUS = new InjectionToken<Signal<NodeStatus>>('NODE_STATUS');

export function iconBgClass(status: NodeStatus): string {
  switch (status) {
    case 'online':
      return 'bg-surface-overlay';
    case 'offline':
      return 'bg-status-error/10';
    case 'disabled':
      return 'bg-surface-overlay';
  }
}
