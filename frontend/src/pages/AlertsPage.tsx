import React, { useState } from 'react';
import {
  Bell,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ShieldAlert,
  Flame,
} from 'lucide-react';
import { AlertsResponse, AlertItem } from '../types';

interface AlertsPageProps {
  alertsData: AlertsResponse | null;
  onRefresh: () => void;
}

export const AlertsPage: React.FC<AlertsPageProps> = ({ alertsData, onRefresh }) => {
  const [activeTab, setActiveTab] = useState<'active' | 'resolved' | 'historical'>('active');
  const [severityFilter, setSeverityFilter] = useState('ALL');

  const activeAlerts = alertsData?.active || [];
  const resolvedAlerts = alertsData?.resolved || [];
  const historicalAlerts = alertsData?.historical || [];

  const currentList =
    activeTab === 'active'
      ? activeAlerts
      : activeTab === 'resolved'
      ? resolvedAlerts
      : historicalAlerts;

  const filteredList = currentList.filter((a) => {
    if (severityFilter !== 'ALL' && a.severity !== severityFilter) return false;
    return true;
  });

  return (
    <div className="page-container">
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 800 }}>Watchdog Alert Center & Incident Tracking</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>
          Categorized operational alerts distinguishing active stalls, verified recoveries, and terminal timeouts.
        </p>
      </div>

      {/* Tabs & Filter Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '20px',
          borderBottom: '1px solid var(--border)',
          paddingBottom: '12px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setActiveTab('active')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              borderRadius: '6px',
              background: activeTab === 'active' ? 'rgba(239, 68, 68, 0.15)' : 'transparent',
              color: activeTab === 'active' ? '#f87171' : 'var(--text-muted)',
              border: `1px solid ${activeTab === 'active' ? 'rgba(239, 68, 68, 0.4)' : 'transparent'}`,
              fontWeight: 700,
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            <AlertTriangle size={15} />
            <span>Active Stalls ({activeAlerts.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('resolved')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              borderRadius: '6px',
              background: activeTab === 'resolved' ? 'rgba(16, 185, 129, 0.15)' : 'transparent',
              color: activeTab === 'resolved' ? '#34d399' : 'var(--text-muted)',
              border: `1px solid ${activeTab === 'resolved' ? 'rgba(16, 185, 129, 0.4)' : 'transparent'}`,
              fontWeight: 700,
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            <CheckCircle2 size={15} />
            <span>Resolved Recoveries ({resolvedAlerts.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('historical')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              borderRadius: '6px',
              background: activeTab === 'historical' ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
              color: activeTab === 'historical' ? '#60a5fa' : 'var(--text-muted)',
              border: `1px solid ${activeTab === 'historical' ? 'rgba(59, 130, 246, 0.4)' : 'transparent'}`,
              fontWeight: 700,
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            <Flame size={15} />
            <span>Terminal Timeouts ({historicalAlerts.length})</span>
          </button>
        </div>

        {/* Severity Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-dim)', fontWeight: 600 }}>SEVERITY:</span>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            style={{
              background: 'var(--bg-card)',
              color: 'var(--text-main)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '6px 12px',
              fontSize: '13px',
              outline: 'none',
            }}
          >
            <option value="ALL">ALL SEVERITIES</option>
            <option value="warning">warning</option>
            <option value="critical">critical</option>
          </select>
        </div>
      </div>

      {/* Alerts List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {filteredList.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '50px' }}>
            No alerts present in this category. System operations normal.
          </div>
        ) : (
          filteredList.map((a) => {
            const isCrit = a.severity === 'critical';
            return (
              <div
                key={a.alert_id}
                style={{
                  background: 'var(--bg-card)',
                  border: `1px solid ${isCrit ? 'rgba(239, 68, 68, 0.5)' : 'var(--border)'}`,
                  borderRadius: '8px',
                  padding: '16px 20px',
                  display: 'flex',
                  alignItems: 'flex-start',
                  justifyContent: 'space-between',
                  gap: '16px',
                }}
              >
                <div style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
                  <div
                    style={{
                      background: isCrit ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                      color: isCrit ? '#f87171' : '#fbbf24',
                      padding: '8px',
                      borderRadius: '6px',
                      marginTop: '2px',
                    }}
                  >
                    {isCrit ? <Flame size={18} /> : <AlertTriangle size={18} />}
                  </div>

                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                      <span
                        className="badge"
                        style={{
                          background: isCrit ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                          color: isCrit ? '#f87171' : '#fbbf24',
                          border: `1px solid ${isCrit ? 'rgba(239, 68, 68, 0.5)' : 'rgba(245, 158, 11, 0.5)'}`,
                        }}
                      >
                        {a.severity}
                      </span>
                      <span style={{ fontWeight: 700, fontSize: '14px' }}>{a.alert_type}</span>
                      <span className="font-mono" style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                        ID: {a.entity_id} ({a.entity_type})
                      </span>
                    </div>

                    <div style={{ fontSize: '13px', color: 'var(--text-main)', marginBottom: '8px' }}>
                      {a.message}
                    </div>

                    <div
                      style={{
                        display: 'flex',
                        gap: '16px',
                        fontSize: '12px',
                        color: 'var(--text-muted)',
                        fontFamily: 'JetBrains Mono, monospace',
                      }}
                    >
                      <span>Campaign: {a.campaign_id} / {a.run_id}</span>
                      <span>Detected: {new Date(a.first_detected_at).toLocaleTimeString()}</span>
                      {a.is_recovered && a.recovered_at && (
                        <span style={{ color: '#34d399' }}>
                          Recovered At: {new Date(a.recovered_at).toLocaleTimeString()}
                        </span>
                      )}
                      {a.is_timeout && a.timeout_at && (
                        <span style={{ color: '#f87171' }}>
                          Timed Out At: {new Date(a.timeout_at).toLocaleTimeString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div>
                  <span className={`badge badge-status-${a.current_status}`}>{a.current_status}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
