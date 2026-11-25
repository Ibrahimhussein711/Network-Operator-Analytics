import React, { useState, useEffect } from 'react';
import { FileText, Download, Layers, ShieldCheck, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';
import { CampaignReportResponse } from '../types';

interface ReportsPageProps {
  campaigns: string[];
  selectedCampaign: string;
  onSelectCampaign: (campaign: string) => void;
}

export const ReportsPage: React.FC<ReportsPageProps> = ({
  campaigns,
  selectedCampaign,
  onSelectCampaign,
}) => {
  const [report, setReport] = useState<CampaignReportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchReport = async (camp: string) => {
    if (!camp) return;
    try {
      setLoading(true);
      setError(null);
      const data = await api.getCampaignReport(camp);
      setReport(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedCampaign) {
      fetchReport(selectedCampaign);
    }
  }, [selectedCampaign]);

  const exportJSON = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `campaign_report_${report.campaign_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportCSV = () => {
    if (!report) return;
    const headers = [
      'entity_id',
      'entity_type',
      'parent_id',
      'campaign_id',
      'run_id',
      'current_status',
      'timeout_sec',
      'bytes_transferred_total',
      'event_count',
    ];
    const rows = report.entities.map((e) => [
      e.entity_id,
      e.entity_type,
      e.parent_id || '',
      e.campaign_id,
      e.run_id,
      e.current_status,
      e.timeout_sec ?? '',
      e.bytes_transferred_total,
      e.event_count,
    ]);
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `entities_${report.campaign_id}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '24px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 800 }}>Executive Campaign Report</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>
            Consolidated operational review, timeline summaries, and outcome metrics for command briefing.
          </p>
        </div>

        {report && (
          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn btn-outline" onClick={exportJSON}>
              <Download size={14} />
              <span>Export JSON</span>
            </button>
            <button className="btn btn-outline" onClick={exportCSV}>
              <Download size={14} />
              <span>Export Entities CSV</span>
            </button>
          </div>
        )}
      </div>

      {/* Campaign Selector Banner */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: '14px',
          marginBottom: '24px',
        }}
      >
        <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-muted)' }}>SELECT CAMPAIGN:</span>
        <select
          value={selectedCampaign}
          onChange={(e) => onSelectCampaign(e.target.value)}
          style={{
            background: 'var(--bg-darker)',
            color: 'var(--text-main)',
            border: '1px solid var(--border)',
            borderRadius: '6px',
            padding: '8px 14px',
            fontSize: '13px',
            fontFamily: 'JetBrains Mono, monospace',
            minWidth: '240px',
            outline: 'none',
          }}
        >
          <option value="">-- Choose Campaign --</option>
          {campaigns.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>

        {selectedCampaign && (
          <button
            className="btn btn-primary"
            onClick={() => fetchReport(selectedCampaign)}
            disabled={loading}
            style={{ fontSize: '12px' }}
          >
            <span>{loading ? 'Generating...' : 'Refresh Report'}</span>
          </button>
        )}
      </div>

      {error && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid #ef4444',
            color: '#f87171',
            padding: '14px',
            borderRadius: '6px',
            marginBottom: '20px',
            fontSize: '13px',
          }}
        >
          Error generating report: {error}
        </div>
      )}

      {!report && !loading && (
        <div className="card" style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '60px' }}>
          <FileText size={40} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
          <div>Select an active campaign above to generate its formal executive report.</div>
        </div>
      )}

      {report && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Executive KPI Grid */}
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-title">Total Ingested Events</div>
              <div className="kpi-value font-mono">{report.total_events}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title">Operational Runs</div>
              <div className="kpi-value font-mono">{report.runs.length}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title">Agents Active</div>
              <div className="kpi-value font-mono" style={{ color: '#60a5fa' }}>{report.total_agents}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title">Tasks Executed</div>
              <div className="kpi-value font-mono" style={{ color: '#c084fc' }}>{report.total_tasks}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title">Shell Sessions</div>
              <div className="kpi-value font-mono" style={{ color: '#22d3ee' }}>{report.total_sessions}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title">Exfiltrated Data</div>
              <div className="kpi-value font-mono" style={{ color: '#34d399' }}>
                {report.bytes_transferred_total.toLocaleString()} B
              </div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title">Watchdog Stalls</div>
              <div className="kpi-value font-mono" style={{ color: '#fbbf24' }}>{report.stalled_incidents}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title">Terminal Timeouts</div>
              <div className="kpi-value font-mono" style={{ color: '#f87171' }}>{report.timeout_failures}</div>
            </div>
          </div>

          {/* Report Meta Card */}
          <div className="card">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', fontSize: '13px' }}>
              <div>
                <span style={{ color: 'var(--text-dim)', fontWeight: 600 }}>CAMPAIGN ID: </span>
                <span className="font-mono" style={{ fontWeight: 700 }}>{report.campaign_id}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-dim)', fontWeight: 600 }}>REPORT GENERATED: </span>
                <span className="font-mono">{new Date(report.generated_at).toLocaleString()}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-dim)', fontWeight: 600 }}>RUNS INCLUDED: </span>
                <span className="font-mono">{report.runs.join(', ') || 'None'}</span>
              </div>
            </div>
          </div>

          {/* Entities Outcome Table */}
          <div className="card">
            <div style={{ fontWeight: 700, fontSize: '15px', marginBottom: '16px' }}>
              Entity Final Lifecycles & Telemetry Outcomes
            </div>

            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Entity ID</th>
                    <th>Type</th>
                    <th>Parent ID</th>
                    <th>Run</th>
                    <th>Status</th>
                    <th>Timeout Setting</th>
                    <th>Bytes Transferred</th>
                    <th>Recorded Events</th>
                  </tr>
                </thead>
                <tbody>
                  {report.entities.map((e) => (
                    <tr key={e.entity_id}>
                      <td className="font-mono" style={{ fontWeight: 700 }}>{e.entity_id}</td>
                      <td>
                        <span className="badge" style={{ background: 'var(--bg-darker)' }}>
                          {e.entity_type}
                        </span>
                      </td>
                      <td className="font-mono" style={{ color: 'var(--text-dim)' }}>{e.parent_id || '—'}</td>
                      <td className="font-mono">{e.run_id}</td>
                      <td>
                        <span className={`badge badge-status-${e.current_status}`}>{e.current_status}</span>
                      </td>
                      <td>{e.timeout_sec !== null ? `${e.timeout_sec}s` : '—'}</td>
                      <td className="font-mono">{e.bytes_transferred_total.toLocaleString()} B</td>
                      <td>{e.event_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
