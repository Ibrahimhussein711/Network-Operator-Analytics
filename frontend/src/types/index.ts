export type EventSource = 'p4_c2' | 'p5_shell' | 'p6_exfil' | 'p7_analytics';
export type EventStatus = 'running' | 'completed' | 'failed' | 'timeout' | 'stalled' | 'pending';
export type EntityType = 'agent' | 'task' | 'session' | 'transfer';
export type Severity = 'warning' | 'critical' | 'info';

export interface HostInfo {
  host_id: string;
  ip: string;
  hostname?: string;
  role: string;
}

export interface DestinationInfo {
  ip: string;
  hostname?: string;
  port?: number;
  protocol?: string;
  role?: string;
}

export interface TechniqueInfo {
  id: string;
  internal_name: string;
  attack_id: string;
  attack_name: string;
  tactic: string;
}

export interface CorrelationInfo {
  entity_id: string;
  entity_type: EntityType;
  parent_id?: string | null;
}

export interface CommonEventEnvelope {
  event_id: string;
  schema_version: string;
  campaign_id: string;
  run_id: string;
  ts: string;
  received_at?: string | null;
  source: EventSource;
  type: string;
  status: EventStatus;
  host: HostInfo;
  destination?: DestinationInfo | null;
  technique: TechniqueInfo;
  correlation: CorrelationInfo;
  timeout_sec?: number | null;
  bytes_transferred_delta?: number | null;
  details: Record<string, any>;
  metadata: {
    is_simulated: boolean;
    generator: string;
    inferred: boolean;
  };
}

export interface EntitySummary {
  entity_id: string;
  entity_type: EntityType;
  parent_id: string | null;
  campaign_id: string;
  run_id: string;
  current_status: EventStatus;
  is_terminal: boolean;
  is_stalled: boolean;
  is_established: boolean;
  timeout_sec: number | null;
  first_seen_ts: string;
  last_seen_ts: string;
  last_received_at: string;
  bytes_transferred_total: number;
  event_count: number;
}

export interface AnalyticsOverviewResponse {
  timestamp: string;
  campaign_id?: string | null;
  run_id?: string | null;
  total_events: number;
  events_by_source: Record<string, number>;
  events_by_type: Record<string, number>;
  entities: {
    total: number;
    active_agents: number;
    active_tasks: number;
    active_sessions: number;
    active_transfers: number;
  };
  stalled_count: number;
  timeout_count: number;
}

export interface AlertItem {
  alert_id: string;
  alert_type: string;
  severity: Severity;
  campaign_id: string;
  run_id: string;
  entity_id: string;
  entity_type: string;
  event_id: string;
  first_detected_at: string;
  last_updated_at: string;
  current_status: 'active' | 'resolved' | 'timed_out';
  is_recovered: boolean;
  recovered_at?: string | null;
  is_timeout: boolean;
  timeout_at?: string | null;
  message: string;
}

export interface AlertsResponse {
  active: AlertItem[];
  resolved: AlertItem[];
  historical: AlertItem[];
  total_active: number;
  total_resolved: number;
  total_historical: number;
}

export interface CampaignReportResponse {
  campaign_id: string;
  generated_at: string;
  runs: string[];
  total_events: number;
  events_by_source: Record<string, number>;
  events_by_type: Record<string, number>;
  total_agents: number;
  total_tasks: number;
  total_sessions: number;
  total_transfers: number;
  bytes_transferred_total: number;
  stalled_incidents: number;
  timeout_failures: number;
  entities: EntitySummary[];
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  storage?: {
    type: string;
    connected: boolean;
    event_count: number;
  };
}

export interface RunMetrics {
  run_id: string;
  total_events: number;
  events_by_source: Record<string, number>;
  events_by_type: Record<string, number>;
  unique_entities: number;
  entities_by_type: Record<string, number>;
  technique_ids: string[];
  completed_entities: number;
  failed_entities: number;
  stalled_entities: number;
  recovered_count: number;
  total_alerts: number;
  bytes_transferred: number;
  duration_sec?: number | null;
}

export interface RunComparisonResponse {
  campaign_id: string;
  run_a: RunMetrics;
  run_b: RunMetrics;
  differences: {
    event_count_delta: number;
    unique_entities_delta: number;
    completed_entities_delta: number;
    failed_entities_delta: number;
    stalled_entities_delta: number;
    alerts_delta: number;
    bytes_transferred_delta: number;
    new_techniques_in_run_b: string[];
  };
  generated_at: string;
}

