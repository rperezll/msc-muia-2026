import { Component, computed, inject, signal } from '@angular/core';
import { MqttService } from '../../../services/mqtt/mqtt.service';

import {
  LucideActivity,
  LucideMoon,
  LucidePause,
  LucidePlay,
  LucideRefreshCw,
  LucideSun,
} from '@lucide/angular';
import { DialogService } from '../../../ui/dialog/dialog.service';

const THEME_KEY = 'msc-muia-2026-theme';

@Component({
  selector: 'app-top-bar',
  imports: [LucideActivity, LucideMoon, LucidePause, LucidePlay, LucideRefreshCw, LucideSun],
  templateUrl: './top-bar.html',
})
export class TopBarComponent {
  protected readonly mqtt = inject(MqttService);
  private readonly dialog = inject(DialogService);

  protected readonly simulatorState = this.mqtt.simulatorState;
  protected readonly isDark = signal(document.documentElement.classList.contains('dark'));

  protected readonly statusLabel = computed(() => {
    if (!this.mqtt.connected()) return 'Disconnected';
    switch (this.simulatorState()) {
      case 'playing':
        return 'Running';
      case 'paused':
        return 'Paused';
      default:
        return 'Stopped';
    }
  });

  protected readonly badgeWrapperClass = computed(() => {
    switch (this.simulatorState()) {
      case 'playing':
        return 'border border-status-ok/20';
      case 'paused':
        return 'border border-status-warning/20';
      default:
        return 'border border-border-default';
    }
  });

  protected readonly badgeClass = computed(() => {
    switch (this.simulatorState()) {
      case 'playing':
        return 'bg-status-ok/10 text-status-ok';
      case 'paused':
        return 'bg-status-warning/10 text-status-warning';
      default:
        return 'bg-surface-overlay text-neutral-300';
    }
  });

  protected readonly dotColorClass = computed(() => {
    switch (this.simulatorState()) {
      case 'playing':
        return 'bg-status-ok';
      case 'paused':
        return 'bg-status-warning';
      default:
        return 'bg-status-disabled';
    }
  });

  protected readonly resetClass = computed(() => {
    if (this.simulatorState() === 'playing') {
      return 'text-neutral-400 opacity-40 cursor-not-allowed';
    }
    return 'text-neutral-200 cursor-pointer hover:bg-status-error/10 hover:text-status-error';
  });

  protected toggleTheme(): void {
    const html = document.documentElement;
    const next = html.classList.contains('dark') ? 'light' : 'dark';
    html.classList.remove('dark', 'light');
    html.classList.add(next);
    localStorage.setItem(THEME_KEY, next);
    this.isDark.set(next === 'dark');
  }

  protected resetAction(): void {
    const resetDialog = this.dialog.confirm({
      title: 'Reset Simulator',
      description:
        'Are you sure you want to reset the MQTT simulator? This action will restore all settings to their default values and cannot be undone.',
      confirmLabel: 'Yes, reset it',
    });

    resetDialog.closed.subscribe((result) => {
      if (result) {
        this.mqtt.sendControl('stop');
      }
    });
  }
}
