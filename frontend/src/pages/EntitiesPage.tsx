import React, { useState } from 'react';
import { Boxes, Filter, Search, ArrowUpRight } from 'lucide-react';
import { EntitySummary } from '../types';

interface EntitiesPageProps {
  entities: EntitySummary[];
}

export const EntitiesPage: React.FC<EntitiesPageProps> = ({ entities }) => {
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  const filteredEntities = entities.filter((e) => {
    if (typeFilter !== 'ALL' && e.entity_type !== typeFilter) return false;
    if (statusFilter !== 'ALL' && e.current_status !== statusFilter) return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      if (!e.entity_id.toLowerCase().includes(q) && !(e.parent_id || '').toLowerCase().includes(q)) {
        return false;
      }
    }
    return true;
  });

  return (
    <div className="page-container">
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 800 }}>Correlated Tracked Entities</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>
          Lifecycle state tracking across Agents, Tasks, Interactive Shells, and Exfiltration Transfers.
        </p>
      </div>

      {/* Toolbar */}
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
        <div style={{ position: 'relative', flex: 1, minWidth: '220px' }}>
          <Search size={15} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--text-dim)' }} />
          <input
            type="text"
            placeholder="Search entity ID or parent ID..."
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

        {/* Type Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-dim)', fontWeight: 600 }}>TYPE:</span>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
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
            <option value="ALL">ALL TYPES</option>
            <option value="agent">Agents</option>
            <option value="task">Tasks</option>
            <option value="session">Sessions</option>
            <option value="transfer">Transfers</option>
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
            <option value="stalled">stalled</option>
            <option value="timeout">timeout</option>
            <option value="completed">completed</option>
            <option value="failed">failed</option>
          </select>
        </div>

        <div style={{ fontSize: '13px', color: 'var(--text-dim)', marginLeft: 'auto' }}>
          {filteredEntities.length} tracked entities
        </div>
      </div>

      {/* Entities Table */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Entity ID</th>
              <th>Type</th>
              <th>Parent ID</th>
              <th>Campaign / Run</th>
              <th>Status</th>
              <th>Timeout Threshold</th>
              <th>Exfil Volume</th>
              <th>Event Count</th>
              <th>Last Seen</th>
            </tr>
          </thead>
          <tbody>
            {filteredEntities.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '40px' }}>
                  No entities found matching filters.
                </td>
              </tr>
            ) : (
              filteredEntities.map((e) => (
                <tr key={e.entity_id}>
                  <td className="font-mono" style={{ fontWeight: 700 }}>
                    {e.entity_id}
                  </td>
                  <td>
                    <span className="badge" style={{ background: 'var(--bg-darker)' }}>
                      {e.entity_type}
                    </span>
                  </td>
                  <td className="font-mono" style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                    {e.parent_id || '—'}
                  </td>
                  <td className="font-mono" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    {e.campaign_id} / {e.run_id}
                  </td>
                  <td>
                    <span className={`badge badge-status-${e.current_status}`}>{e.current_status}</span>
                  </td>
                  <td style={{ fontSize: '12px' }}>
                    {e.timeout_sec !== null ? `${e.timeout_sec}s` : '—'}
                  </td>
                  <td className="font-mono" style={{ fontSize: '12px' }}>
                    {e.bytes_transferred_total > 0 ? `${e.bytes_transferred_total.toLocaleString()} B` : '0 B'}
                  </td>
                  <td>{e.event_count}</td>
                  <td className="font-mono" style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                    {new Date(e.last_seen_ts).toLocaleTimeString()}
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
