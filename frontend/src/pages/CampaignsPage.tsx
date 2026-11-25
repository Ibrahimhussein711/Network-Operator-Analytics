import React, { useEffect, useState } from 'react';
import {
  Layers,
  CheckCircle,
  ArrowRight,
  GitCompare,
  TrendingDown,
  TrendingUp,
  AlertCircle,
  Activity,
  Boxes,
} from 'lucide-react';
import { api } from '../services/api';
import { EntitySummary, RunComparisonResponse } from '../types';

interface CampaignsPageProps {
  campaigns: string[];
  selectedCampaign: string;
  onSelectCampaign: (campaign: string) => void;
  onNavigate: (page: any) => void;
}

export const CampaignsPage: React.FC<CampaignsPageProps> = ({
  campaigns,
  selectedCampaign,
  onSelectCampaign,
  onNavigate,
}) => {
  const [runs, setRuns] = useState<string[]>([]);
  const [entities, setEntities] = useState<EntitySummary[]>([]);
  const [loading, setLoading] = useState(false);

  // Comparison State
  const [runA, setRunA] = useState<string>('');
  const [runB, setRunB] = useState<string>('');
  const [comparison, setComparison] = useState<RunComparisonResponse | null>(null);
  const [comparing, setComparing] = useState(false);
  const [compareError, setCompareError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedCampaign) return;
    setLoading(true);
    setComparison(null);
    setCompareError(null);
    Promise.all([
      api.getRuns(selectedCampaign),
      api.getEntities(selectedCampaign),
    ])
      .then(([rList, entList]) => {
        setRuns(rList);
        setEntities(entList);
        if (rList.length >= 2) {
          setRunA(rList[0]);
          setRunB(rList[1]);
        } else if (rList.length === 1) {
          setRunA(rList[0]);
          setRunB(rList[0]);
        }
      })
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, [selectedCampaign]);

  const handleCompare = async () => {
    if (!selectedCampaign || !runA || !runB) return;
    try {
      setComparing(true);
      setCompareError(null);
      const res = await api.compareRuns(selectedCampaign, runA, runB);
      setComparison(res);
    } catch (e: any) {
      setCompareError(e.message || 'Comparison failed');
    } finally {
      setComparing(false);
    }
  };

  return (
    <div className="page-container">
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#ffffff' }}>
          Campaigns & Isolated Operational Runs
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>
          Strict multi-campaign and multi-run isolation with comparative analytics.
        </p>
      </div>

      <div className="campaigns-layout-grid">
        {/* Campaign List */}
        <div className="glass-card" style={{ padding: '16px' }}>
          <div style={{ fontWeight: 700, fontSize: '13px', marginBottom: '12px', color: 'var(--text-muted)' }}>
            REGISTERED CAMPAIGNS ({campaigns.length})
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {campaigns.length === 0 ? (
              <div style={{ color: 'var(--text-dim)', fontSize: '13px', padding: '16px 0' }}>
                No campaigns registered yet.
              </div>
            ) : (
              campaigns.map((c) => {
                const isSelected = selectedCampaign === c;
                return (
                  <button
                    key={c}
                    onClick={() => onSelectCampaign(c)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: isSelected ? 'rgba(114, 9, 183, 0.25)' : 'rgba(255, 255, 255, 0.02)',
                      color: isSelected ? '#ffffff' : 'var(--text-main)',
                      border: `1px solid ${isSelected ? 'rgba(168, 85, 247, 0.5)' : 'var(--border-glass)'}`,
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: 600,
                      fontFamily: 'JetBrains Mono, monospace',
                      textAlign: 'left',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <span>{c}</span>
                    {isSelected && <CheckCircle size={14} color="#a855f7" />}
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Selected Campaign Details */}
        <div className="glass-card">
          {!selectedCampaign ? (
            <div style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '60px 20px' }}>
              <Layers size={36} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
              <div>Select a campaign from the left list to view isolated runs and comparison metrics.</div>
            </div>
          ) : (
            <div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  paddingBottom: '16px',
                  borderBottom: '1px solid var(--border-glass)',
                  marginBottom: '20px',
                }}
              >
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>CAMPAIGN SCOPE</div>
                  <h3 style={{ fontSize: '18px', fontWeight: 800, fontFamily: 'JetBrains Mono, monospace', color: '#ffffff' }}>
                    {selectedCampaign}
                  </h3>
                </div>
                <button
                  className="btn btn-outline"
                  onClick={() => onNavigate('reports')}
                  style={{ fontSize: '12px' }}
                >
                  <span>Generate Report</span>
                  <ArrowRight size={14} />
                </button>
              </div>

              {/* Multi-Run Selector and Comparison Controls */}
              <div
                style={{
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border-glass)',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  marginBottom: '24px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <GitCompare size={16} color="#3a86ff" />
                    <span style={{ fontSize: '13px', fontWeight: 700, color: '#ffffff' }}>
                      Multi-Run Isolation & Comparison
                    </span>
                  </div>
                  <button
                    className="btn btn-primary"
                    onClick={handleCompare}
                    disabled={comparing || runs.length < 1}
                    style={{ fontSize: '12px', padding: '6px 14px' }}
                  >
                    <span>{comparing ? 'Comparing...' : 'Compare Runs'}</span>
                  </button>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Run Baseline (A):</span>
                    <select
                      value={runA}
                      onChange={(e) => setRunA(e.target.value)}
                      style={{
                        background: 'rgba(20, 24, 48, 0.8)',
                        border: '1px solid var(--border-glass-bright)',
                        color: 'white',
                        padding: '6px 12px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontFamily: 'JetBrains Mono',
                      }}
                    >
                      {runs.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                  </div>

                  <span style={{ color: 'var(--text-dim)', fontSize: '12px' }}>vs</span>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Run Target (B):</span>
                    <select
                      value={runB}
                      onChange={(e) => setRunB(e.target.value)}
                      style={{
                        background: 'rgba(20, 24, 48, 0.8)',
                        border: '1px solid var(--border-glass-bright)',
                        color: 'white',
                        padding: '6px 12px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontFamily: 'JetBrains Mono',
                      }}
                    >
                      {runs.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {compareError && (
                  <div style={{ color: '#ff4d6d', fontSize: '12px', marginTop: '10px' }}>
                    {compareError}
                  </div>
                )}
              </div>

              {/* Comparison Output Cards */}
              {comparison && (
                <div
                  style={{
                    marginBottom: '24px',
                    background: 'rgba(20, 24, 52, 0.6)',
                    border: '1px solid var(--border-glass-bright)',
                    borderRadius: '12px',
                    padding: '20px',
                  }}
                >
                  <h4 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '14px', color: '#ffffff' }}>
                    Comparison Results: {comparison.run_a.run_id} &rarr; {comparison.run_b.run_id}
                  </h4>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '12px', marginBottom: '16px' }}>
                    <div className="glass-card" style={{ padding: '12px' }}>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Event Count &Delta;</div>
                      <div style={{ fontSize: '18px', fontWeight: 700, fontFamily: 'JetBrains Mono', color: '#3a86ff' }}>
                        {comparison.differences.event_count_delta > 0 ? `+${comparison.differences.event_count_delta}` : comparison.differences.event_count_delta}
                      </div>
                    </div>
                    <div className="glass-card" style={{ padding: '12px' }}>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Unique Entities &Delta;</div>
                      <div style={{ fontSize: '18px', fontWeight: 700, fontFamily: 'JetBrains Mono', color: '#a855f7' }}>
                        {comparison.differences.unique_entities_delta > 0 ? `+${comparison.differences.unique_entities_delta}` : comparison.differences.unique_entities_delta}
                      </div>
                    </div>
                    <div className="glass-card" style={{ padding: '12px' }}>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Stalled Entities &Delta;</div>
                      <div style={{ fontSize: '18px', fontWeight: 700, fontFamily: 'JetBrains Mono', color: '#ffb703' }}>
                        {comparison.differences.stalled_entities_delta > 0 ? `+${comparison.differences.stalled_entities_delta}` : comparison.differences.stalled_entities_delta}
                      </div>
                    </div>
                    <div className="glass-card" style={{ padding: '12px' }}>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Alerts &Delta;</div>
                      <div style={{ fontSize: '18px', fontWeight: 700, fontFamily: 'JetBrains Mono', color: '#ef233c' }}>
                        {comparison.differences.alerts_delta > 0 ? `+${comparison.differences.alerts_delta}` : comparison.differences.alerts_delta}
                      </div>
                    </div>
                  </div>

                  {comparison.differences.new_techniques_in_run_b.length > 0 && (
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span>New Techniques in {comparison.run_b.run_id}:</span>
                      {comparison.differences.new_techniques_in_run_b.map((t) => (
                        <span key={t} className="badge badge-p6">
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Entities Summary for Campaign */}
              <div>
                <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '12px' }}>
                  ENTITIES UNDER CAMPAIGN ({entities.length})
                </div>
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>Entity ID</th>
                        <th>Type</th>
                        <th>Run</th>
                        <th>Status</th>
                        <th>Timeout</th>
                        <th>Events</th>
                      </tr>
                    </thead>
                    <tbody>
                      {entities.length === 0 ? (
                        <tr>
                          <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '24px' }}>
                            {loading ? 'Loading...' : 'No entities registered under this campaign.'}
                          </td>
                        </tr>
                      ) : (
                        entities.map((e) => (
                          <tr key={e.entity_id}>
                            <td className="font-mono" style={{ fontWeight: 700 }}>
                              {e.entity_id}
                            </td>
                            <td>
                              <span className="badge" style={{ background: 'rgba(255, 255, 255, 0.05)' }}>
                                {e.entity_type}
                              </span>
                            </td>
                            <td className="font-mono">{e.run_id}</td>
                            <td>
                              <span className={`badge badge-status-${e.current_status}`}>{e.current_status}</span>
                            </td>
                            <td>{e.timeout_sec !== null ? `${e.timeout_sec}s` : '-'}</td>
                            <td>{e.event_count}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
