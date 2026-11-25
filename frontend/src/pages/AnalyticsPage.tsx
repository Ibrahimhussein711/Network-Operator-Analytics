import React from 'react';
import { BarChart3, PieChart, Activity, Zap } from 'lucide-react';
import { AnalyticsOverviewResponse, EntitySummary } from '../types';

interface AnalyticsPageProps {
  overview: AnalyticsOverviewResponse | null;
  entities: EntitySummary[];
}

export const AnalyticsPage: React.FC<AnalyticsPageProps> = ({ overview, entities }) => {
  const totalEvents = overview?.total_events || 0;
  const sources = overview?.events_by_source || {};
  const types = overview?.events_by_type || {};

  const totalExfilBytes = entities.reduce((acc, e) => acc + (e.bytes_transferred_total || 0), 0);

  const statusCounts = entities.reduce<Record<string, number>>((acc, e) => {
    acc[e.current_status] = (acc[e.current_status] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="page-container">
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 800 }}>Operational Analytics & Telemetry Breakdown</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>
          Aggregate analysis of ingested events, telemetry distribution, and lifecycle state metrics.
        </p>
      </div>

      {/* Grid: Events by Type & Entity Lifecycles */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        {/* Events by Source Breakdown */}
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: '14px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={16} color="#3b82f6" />
            <span>Telemetry Volume by Source</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {[
              { key: 'p4_c2', label: 'P4 C2 Framework', color: '#3b82f6' },
              { key: 'p5_shell', label: 'P5 Interactive Shell', color: '#a855f7' },
              { key: 'p6_exfil', label: 'P6 Covert Exfiltration', color: '#06b6d4' },
              { key: 'p7_analytics', label: 'P7 Analytics Watchdogs', color: '#ef4444' },
            ].map((s) => {
              const count = sources[s.key] || 0;
              const pct = totalEvents > 0 ? Math.round((count / totalEvents) * 100) : 0;
              return (
                <div key={s.key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 600 }}>{s.label}</span>
                    <span className="font-mono">{count} events ({pct}%)</span>
                  </div>
                  <div style={{ height: '8px', background: 'var(--bg-darker)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${pct}%`, height: '100%', background: s.color, borderRadius: '4px' }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Entity Lifecycle Status Distribution */}
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: '14px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <PieChart size={16} color="#10b981" />
            <span>Entity Lifecycle Status Distribution</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {[
              { key: 'running', label: 'Running / Active', color: '#10b981' },
              { key: 'completed', label: 'Completed (Clean)', color: '#3b82f6' },
              { key: 'stalled', label: 'Stalled (Grace Active)', color: '#f59e0b' },
              { key: 'timeout', label: 'Timed Out (Failed)', color: '#ef4444' },
              { key: 'failed', label: 'Failed (Explicit)', color: '#dc2626' },
            ].map((st) => {
              const count = statusCounts[st.key] || 0;
              const totalEnts = entities.length;
              const pct = totalEnts > 0 ? Math.round((count / totalEnts) * 100) : 0;
              return (
                <div key={st.key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 600 }}>{st.label}</span>
                    <span className="font-mono">{count} entities ({pct}%)</span>
                  </div>
                  <div style={{ height: '8px', background: 'var(--bg-darker)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${pct}%`, height: '100%', background: st.color, borderRadius: '4px' }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Covert Exfiltration Volume */}
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: '14px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={16} color="#06b6d4" />
            <span>Covert Channel Throughput</span>
          </div>

          <div style={{ padding: '20px 0', textAlign: 'center' }}>
            <div style={{ fontSize: '32px', fontWeight: 800, color: '#22d3ee', fontFamily: 'JetBrains Mono, monospace' }}>
              {totalExfilBytes.toLocaleString()} B
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Cumulative Exfiltrated Payload Bytes
            </div>
          </div>

          <div style={{ borderTop: '1px solid var(--border)', paddingTop: '14px', fontSize: '12px', color: 'var(--text-dim)' }}>
            Across all chunked covert channels (DNS Tunneling, ICMP Echo, HTTPS Steganography).
          </div>
        </div>
      </div>

      {/* Events by Type Table */}
      <div className="card">
        <div style={{ fontWeight: 700, fontSize: '14px', marginBottom: '16px' }}>
          Ingested Events Ranked by Canonical Event Type
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Event Type</th>
                <th>Count</th>
                <th>Proportion</th>
              </tr>
            </thead>
            <tbody>
              {Object.keys(types).length === 0 ? (
                <tr>
                  <td colSpan={3} style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '20px' }}>
                    No events recorded.
                  </td>
                </tr>
              ) : (
                Object.entries(types)
                  .sort((a, b) => b[1] - a[1])
                  .map(([t, count]) => {
                    const pct = totalEvents > 0 ? Math.round((count / totalEvents) * 100) : 0;
                    return (
                      <tr key={t}>
                        <td style={{ fontWeight: 600, fontFamily: 'JetBrains Mono, monospace' }}>{t}</td>
                        <td className="font-mono">{count}</td>
                        <td style={{ width: '40%' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <div style={{ flex: 1, height: '6px', background: 'var(--bg-darker)', borderRadius: '3px', overflow: 'hidden' }}>
                              <div style={{ width: `${pct}%`, height: '100%', background: '#3b82f6', borderRadius: '3px' }} />
                            </div>
                            <span style={{ fontSize: '12px', color: 'var(--text-muted)', width: '40px' }}>{pct}%</span>
                          </div>
                        </td>
                      </tr>
                    );
                  })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
