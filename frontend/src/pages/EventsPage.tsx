import React, { useState } from 'react';
import { Search, Filter, RefreshCw, Eye } from 'lucide-react';
import { CommonEventEnvelope } from '../types';

interface EventsPageProps {
  events: CommonEventEnvelope[];
  onSelectEvent: (event: CommonEventEnvelope) => void;
  onRefresh: () => void;
  autoRefresh: boolean;
  onToggleAutoRefresh: (val: boolean) => void;
}

export const EventsPage: React.FC<EventsPageProps> = ({
  events,
  onSelectEvent,
  onRefresh,
  autoRefresh,
  onToggleAutoRefresh,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sourceFilter, setSourceFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const filteredEvents = events.filter((ev) => {
    if (sourceFilter !== 'ALL' && ev.source !== sourceFilter) return false;
    if (statusFilter !== 'ALL' && ev.status !== statusFilter) return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      const matchType = ev.type.toLowerCase().includes(q);
      const matchEntity = ev.correlation.entity_id.toLowerCase().includes(q);
      const matchId = ev.event_id.toLowerCase().includes(q);
      const matchCampaign = ev.campaign_id.toLowerCase().includes(q);
      if (!matchType && !matchEntity && !matchId && !matchCampaign) return false;
    }
    return true;
  });

  return (
    <div className="page-container">
      {/* Header & Controls */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '20px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 800 }}>Live Event Stream & Ingestion Ledger</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>
            Canonical SHA-256 deduplicated telemetry from P4 (C2), P5 (Shells), P6 (Exfil), and P7 (Analytics).
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => onToggleAutoRefresh(e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            <span style={{ color: 'var(--text-muted)' }}>Auto-poll (3s)</span>
          </label>

          <button className="btn btn-outline" onClick={onRefresh} style={{ padding: '6px 12px' }}>
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          padding: '14px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          marginBottom: '20px',
          flexWrap: 'wrap',
        }}
      >
        {/* Search */}
        <div style={{ position: 'relative', flex: 1, minWidth: '220px' }}>
          <Search size={15} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--text-dim)' }} />
          <input
            type="text"
            placeholder="Search by event type, entity ID, or UUID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              background: 'var(--bg-darker)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '8px 12px 8px 34px',
              color: 'var(--text-main)',
              fontSize: '13px',
              outline: 'none',
            }}
          />
        </div>

        {/* Source Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-dim)', fontWeight: 600 }}>SOURCE:</span>
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            style={{
              background: 'var(--bg-darker)',
              color: 'var(--text-main)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '6px 10px',
              fontSize: '13px',
              outline: 'none',
            }}
          >
            <option value="ALL">ALL SOURCES</option>
            <option value="p4_c2">P4 C2</option>
            <option value="p5_shell">P5 Shell</option>
            <option value="p6_exfil">P6 Exfil</option>
            <option value="p7_analytics">P7 Analytics</option>
          </select>
        </div>

        {/* Status Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-dim)', fontWeight: 600 }}>STATUS:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              background: 'var(--bg-darker)',
              color: 'var(--text-main)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '6px 10px',
              fontSize: '13px',
              outline: 'none',
            }}
          >
            <option value="ALL">ALL STATUSES</option>
            <option value="running">running</option>
            <option value="completed">completed</option>
            <option value="stalled">stalled</option>
            <option value="timeout">timeout</option>
            <option value="failed">failed</option>
          </select>
        </div>

        <div style={{ fontSize: '13px', color: 'var(--text-dim)', marginLeft: 'auto' }}>
          Showing {filteredEvents.length} of {events.length}
        </div>
      </div>

      {/* Events Table */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Source</th>
              <th>Event Type</th>
              <th>Status</th>
              <th>Entity</th>
              <th>Campaign / Run</th>
              <th>Host / Dest</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredEvents.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '40px' }}>
                  No matching events found.
                </td>
              </tr>
            ) : (
              filteredEvents.slice().reverse().map((ev) => (
                <tr key={ev.event_id}>
                  <td className="font-mono" style={{ fontSize: '12px', whiteSpace: 'nowrap' }}>
                    {new Date(ev.ts).toLocaleTimeString()}
                  </td>
                  <td>
                    <span className={`badge badge-${ev.source}`}>{ev.source}</span>
                  </td>
                  <td style={{ fontWeight: 600 }}>{ev.type}</td>
                  <td>
                    <span className={`badge badge-status-${ev.status}`}>{ev.status}</span>
                  </td>
                  <td className="font-mono" style={{ fontSize: '12px' }}>
                    {ev.correlation.entity_id}
                  </td>
                  <td className="font-mono" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    {ev.campaign_id} / {ev.run_id}
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                    {ev.host.ip}
                  </td>
                  <td>
                    <button
                      className="btn btn-outline"
                      style={{ padding: '3px 8px', fontSize: '11px' }}
                      onClick={() => onSelectEvent(ev)}
                    >
                      <Eye size={12} />
                      <span>Inspect</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
