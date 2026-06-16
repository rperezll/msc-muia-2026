export interface SolarTelemetryPayload {
  DATE_TIME: string;
  PLANT_ID: number;
  SOURCE_KEY: string;
  DC_POWER: number;
  AC_POWER: number;
  DAILY_YIELD: number;
  TOTAL_YIELD: number;
  AMBIENT_TEMPERATURE: number;
  MODULE_TEMPERATURE: number;
  IRRADIATION: number;
  PLANT: number;
}

export interface AnomalyDetection {
  detection_id: string;
  source_key: string;
  timestamp: string;
  mae: number | null;
  threshold: number | null;
  payload: SolarTelemetryPayload;
}

export interface AnomalyReport {
  report_id: string;
  source_key: string;
  detections: AnomalyDetection[];
  created_at: string;
}

export type AnomalyClassification =
  | 'power_degradation'
  | 'thermal_stress'
  | 'irradiation_mismatch'
  | 'dc_side_fault'
  | 'inverter_fault'
  | 'grid_instability'
  | 'night_residual_power'
  | 'sensor_fault'
  | 'unknown';

export const ANOMALY_CLASSIFICATION_LABELS: Record<AnomalyClassification, string> = {
  power_degradation: 'Power Degradation',
  thermal_stress: 'Thermal Stress',
  irradiation_mismatch: 'Irradiation Mismatch',
  dc_side_fault: 'DC Side Fault',
  inverter_fault: 'Inverter Fault',
  grid_instability: 'Grid Instability',
  night_residual_power: 'Night Residual Power',
  sensor_fault: 'Sensor Fault',
  unknown: 'Unknown',
};

export interface ExplainerOriginalMetrics {
  mae: number | null;
  threshold: number | null;
  dc_ac_efficiency_pct: number;
  avg_temp_delta: number;
  irradiation_category: 'night' | 'low' | 'medium' | 'high';
  detection_count: number;
}

export interface ExplainerTechnicalDescription {
  original_metrics: ExplainerOriginalMetrics;
  summary: string;
}

export interface ExplainerRagSearchParameters {
  generic_component_class: string;
  anomaly_type: AnomalyClassification;
  affected_subsystem: string;
}

export type ExplainerSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface ExplainerIncident {
  event_metadata: {
    timestamp: string;
    severity: ExplainerSeverity;
    instance_id: string;
  };
  rag_search_parameters: ExplainerRagSearchParameters;
  technical_description: ExplainerTechnicalDescription;
  suggested_rag_search_queries: string[];
}

export type JobEventType = 'started' | 'progress' | 'completed' | 'failed';

export interface JobEvent {
  type: JobEventType;
  report_id: string;
  source_key: string;
  started_at?: string;
  iteration?: number;
  max_iterations?: number;
  result?: unknown;
  duration_ms?: number;
  error?: string;
  report?: AnomalyReport;
}

export type SimulatorState = 'stopped' | 'playing' | 'paused';

export const MQTT_TOPICS = {
  TELEMETRY: 'telemetry/solar',
  SIMULATOR_CONTROL: 'simulator/control',
  SIMULATOR_STATUS: 'simulator/status',
  DETECTOR_ANOMALY: 'detector/anomaly',
  JOB_EVENT: 'explainer/job_event',
} as const;

export interface RabbitMqQueueStats {
  messages: number;
  messages_ready: number;
  messages_unacknowledged: number;
  consumers: number;
  name: string;
}

export type ExplanationFeedback = 'up' | 'down' | null;

export interface ExplanationRecord {
  id: string;
  source_key: string;
  result: ExplainerIncident[];
  report: AnomalyReport | null;
  duration_ms: number | null;
  feedback: ExplanationFeedback;
  feedback_at: string | null;
  created_at: string;
}

export interface ExplanationListResponse {
  items: ExplanationRecord[];
  total: number;
  limit: number;
  offset: number;
}

export interface RagDocument {
  title: string | null;
  source: string | null;
  snippet: string;
  score: number | null;
}

export interface AugmentResponse {
  augmented_summary: string;
  retrieved: RagDocument[];
  model: string;
}

export const SEVERITY_ORDER: ExplainerSeverity[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

export function worstSeverity(incidents: ExplainerIncident[]): ExplainerSeverity | null {
  for (const level of SEVERITY_ORDER) {
    if (incidents.some((i) => i.event_metadata.severity === level)) return level;
  }
  return null;
}

export function severityDotClass(s: ExplainerSeverity): string {
  switch (s) {
    case 'CRITICAL':
      return 'bg-status-error';
    case 'HIGH':
      return 'bg-status-error/70';
    case 'MEDIUM':
      return 'bg-status-warning';
    default:
      return 'bg-neutral-400';
  }
}

export function severityTextClass(s: ExplainerSeverity): string {
  switch (s) {
    case 'CRITICAL':
      return 'text-status-error';
    case 'HIGH':
      return 'text-status-error/80';
    case 'MEDIUM':
      return 'text-status-warning';
    default:
      return 'text-neutral-400';
  }
}

export function severityBadgeClass(s: ExplainerSeverity): string {
  switch (s) {
    case 'CRITICAL':
      return 'bg-status-error/15 text-status-error';
    case 'HIGH':
      return 'bg-status-error/10 text-status-error/80';
    case 'MEDIUM':
      return 'bg-status-warning/15 text-status-warning';
    default:
      return 'bg-neutral-400/10 text-neutral-400';
  }
}

export function severityBorderClass(s: ExplainerSeverity): string {
  switch (s) {
    case 'CRITICAL':
      return 'border-status-error/30';
    case 'HIGH':
      return 'border-status-error/20';
    case 'MEDIUM':
      return 'border-status-warning/30';
    default:
      return 'border-border-default';
  }
}

export function formatDuration(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`;
}

export function formatDetectedAt(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    const day = d.getDate().toString().padStart(2, '0');
    const month = d.toLocaleString('en-GB', { month: 'short' });
    const time = d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
    return `${day} ${month} ${time}`;
  } catch {
    return dateStr;
  }
}
