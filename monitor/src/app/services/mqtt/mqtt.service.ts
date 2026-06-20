import { Injectable, DestroyRef, inject, signal, computed } from '@angular/core';
import mqtt, { MqttClient } from 'mqtt';

import {
  MQTT_TOPICS,
  type AnomalyReport,
  type JobEvent,
  type SimulatorState,
  type SolarTelemetryPayload,
} from '../../core/contracts';
import { RabbitmqApiService } from '../rabbitmq/rabbitmq-api.service';

const MQTT_WS_URL = 'ws://localhost:9001';
const MAX_ANOMALIES = 200;
const MAX_JOB_EVENTS = 50;
const MSG_RATE_WINDOW_MS = 60_000;

@Injectable({ providedIn: 'root' })
export class MqttService {
  private client: MqttClient | null = null;
  private readonly destroyRef = inject(DestroyRef);
  private readonly rabbitmq = inject(RabbitmqApiService);

  readonly connected = signal(false);
  readonly telemetryMap = signal<Map<string, SolarTelemetryPayload>>(new Map());
  readonly simulatorState = signal<SimulatorState>('stopped');
  readonly anomalies = signal<AnomalyReport[]>([]);
  readonly anomalyPulse = signal(false);

  readonly jobEvents = signal<JobEvent[]>([]);

  private _msgTimestamps: number[] = [];
  readonly msgRate = signal(0);

  readonly totalInverters = computed(() => this.telemetryMap().size);
  readonly simulatedTime = computed(() => {
    let latest = '';
    for (const p of this.telemetryMap().values()) {
      if (p.DATE_TIME > latest) latest = p.DATE_TIME;
    }
    return latest || null;
  });
  readonly anomalyCount = computed(() => this.anomalies().length);
  readonly telemetryReceived = signal(false);

  readonly completedJobs = computed(
    () => this.jobEvents().filter((e) => e.type === 'completed').length,
  );
  readonly failedJobs = computed(() => this.jobEvents().filter((e) => e.type === 'failed').length);

  constructor() {
    this.connect();
    this.destroyRef.onDestroy(() => this.client?.end());
  }

  private connect(): void {
    this.client = mqtt.connect(MQTT_WS_URL, {
      reconnectPeriod: 3000,
      connectTimeout: 5000,
    });

    this.client.on('connect', () => {
      this.connected.set(true);
      this.client!.subscribe([
        MQTT_TOPICS.TELEMETRY,
        MQTT_TOPICS.SIMULATOR_STATUS,
        MQTT_TOPICS.DETECTOR_ANOMALY,
        MQTT_TOPICS.JOB_EVENT,
      ]);
    });

    this.client.on('close', () => this.connected.set(false));
    this.client.on('error', () => this.connected.set(false));
    this.client.on('message', (topic: string, payload: Buffer) =>
      this.handleMessage(topic, payload),
    );
  }

  private handleMessage(topic: string, payload: Buffer): void {
    const raw = payload.toString();

    switch (topic) {
      case MQTT_TOPICS.TELEMETRY: {
        const data: SolarTelemetryPayload = JSON.parse(raw);
        this.telemetryMap.update((m) => {
          const next = new Map(m);
          next.set(data.SOURCE_KEY, data);
          return next;
        });
        this.telemetryReceived.set(true);
        this.updateMsgRate();
        break;
      }

      case MQTT_TOPICS.SIMULATOR_STATUS: {
        this.simulatorState.set(raw.replace(/"/g, '') as SimulatorState);
        break;
      }

      case MQTT_TOPICS.DETECTOR_ANOMALY: {
        const report: AnomalyReport = JSON.parse(raw);
        this.anomalies.update((list) => [report, ...list].slice(0, MAX_ANOMALIES));
        this.triggerPulse();
        break;
      }

      case MQTT_TOPICS.JOB_EVENT: {
        const event: JobEvent = JSON.parse(raw);
        this.jobEvents.update((list) => [event, ...list].slice(0, MAX_JOB_EVENTS));
        this.rabbitmq.refresh();
        break;
      }
    }
  }

  private updateMsgRate(): void {
    const now = Date.now();
    this._msgTimestamps.push(now);
    const cutoff = now - MSG_RATE_WINDOW_MS;
    this._msgTimestamps = this._msgTimestamps.filter((t) => t >= cutoff);
    this.msgRate.set(this._msgTimestamps.length);
  }

  private triggerPulse(): void {
    this.anomalyPulse.set(true);
    setTimeout(() => this.anomalyPulse.set(false), 2000);
  }

  sendControl(command: string): void {
    this.client?.publish(MQTT_TOPICS.SIMULATOR_CONTROL, command);
    if (command === 'stop') this.resetState();
  }

  private resetState(): void {
    this.telemetryMap.set(new Map());
    this._msgTimestamps = [];
    this.msgRate.set(0);
    this.anomalies.set([]);
    this.anomalyPulse.set(false);
    this.telemetryReceived.set(false);
    this.jobEvents.set([]);
  }
}
