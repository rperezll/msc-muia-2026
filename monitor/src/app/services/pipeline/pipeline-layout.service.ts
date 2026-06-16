import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class PipelineLayoutService {
  readonly activePorts = signal<Map<string, Set<string>>>(new Map());

  update(map: Map<string, Set<string>>): void {
    this.activePorts.set(map);
  }
}
