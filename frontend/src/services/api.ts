import {
  AlertsResponse,
  AnalyticsOverviewResponse,
  CampaignReportResponse,
  CommonEventEnvelope,
  EntitySummary,
  HealthResponse,
} from '../types';

const API_BASE = '/api/v1';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    let errorDetail = `Request failed: ${res.status} ${res.statusText}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  // Probes
  getLiveness: () => request<HealthResponse>('/health/live'),
  getReadiness: () => request<HealthResponse>('/health/ready'),

  // Campaigns & Runs
  getCampaigns: () => request<string[]>('/campaigns'),
  getRuns: (campaignId: string) => request<string[]>(`/campaigns/${encodeURIComponent(campaignId)}/runs`),

  // Analytics Overview
  getOverview: (campaignId?: string | null, runId?: string | null) => {
    const params = new URLSearchParams();
    if (campaignId) params.append('campaign_id', campaignId);
    if (runId) params.append('run_id', runId);
    const qs = params.toString();
    return request<AnalyticsOverviewResponse>(`/analytics/overview${qs ? `?${qs}` : ''}`);
  },

  // Events
  getEvents: (params?: {
    campaignId?: string | null;
    runId?: string | null;
    source?: string | null;
    type?: string | null;
    limit?: number;
    offset?: number;
  }) => {
    const sp = new URLSearchParams();
    if (params?.campaignId) sp.append('campaign_id', params.campaignId);
    if (params?.runId) sp.append('run_id', params.runId);
    if (params?.source) sp.append('source', params.source);
    if (params?.type) sp.append('type', params.type);
    if (params?.limit) sp.append('limit', params.limit.toString());
    if (params?.offset) sp.append('offset', params.offset.toString());
    const qs = sp.toString();
    return request<CommonEventEnvelope[]>(`/events${qs ? `?${qs}` : ''}`);
  },

  getEventById: (eventId: string) => request<CommonEventEnvelope>(`/events/${encodeURIComponent(eventId)}`),

  // Entities
  getEntities: (campaignId?: string | null, runId?: string | null) => {
    const sp = new URLSearchParams();
    if (campaignId) sp.append('campaign_id', campaignId);
    if (runId) sp.append('run_id', runId);
    const qs = sp.toString();
    return request<EntitySummary[]>(`/analytics/entities${qs ? `?${qs}` : ''}`);
  },

  // Alerts
  getAlerts: (campaignId?: string | null, runId?: string | null, severity?: string | null) => {
    const sp = new URLSearchParams();
    if (campaignId) sp.append('campaign_id', campaignId);
    if (runId) sp.append('run_id', runId);
    if (severity) sp.append('severity', severity);
    const qs = sp.toString();
    return request<AlertsResponse>(`/analytics/alerts${qs ? `?${qs}` : ''}`);
  },

  // Campaign Report & Comparison
  getCampaignReport: (campaignId: string) =>
    request<CampaignReportResponse>(`/analytics/campaigns/${encodeURIComponent(campaignId)}/report`),

  compareRuns: (campaignId: string, runA: string, runB: string) =>
    request<any>(
      `/analytics/campaigns/${encodeURIComponent(campaignId)}/compare?run_a=${encodeURIComponent(runA)}&run_b=${encodeURIComponent(runB)}`
    ),

  // Watchdog Trigger
  triggerWatchdogs: (campaignId?: string | null, runId?: string | null) => {
    const sp = new URLSearchParams();
    if (campaignId) sp.append('campaign_id', campaignId);
    if (runId) sp.append('run_id', runId);
    const qs = sp.toString();
    return request<CommonEventEnvelope[]>(`/watchdogs/trigger${qs ? `?${qs}` : ''}`, {
      method: 'POST',
    });
  },

  // Demo Scenarios (all 7 scenarios)
  injectDemo: (
    scenario:
      | 'normal'
      | 'agent_stalled'
      | 'task_stalled'
      | 'handshake_timeout'
      | 'session_stalled'
      | 'transfer_stalled'
      | 'mixed'
      | 'stalled',
    campaignId?: string | null,
    runId?: string | null
  ) => {
    const sp = new URLSearchParams({ scenario });
    if (campaignId) sp.append('campaign_id', campaignId);
    if (runId) sp.append('run_id', runId);
    return request<{ status: string; scenario: string; campaign_id: string; run_id: string; events_injected: number }>(
      `/demo/inject?${sp.toString()}`,
      { method: 'POST' }
    );
  },
};
