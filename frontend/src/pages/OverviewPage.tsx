import React from 'react';
import {
  BarChart3,
  Monitor,
  ClipboardCheck,
  Share2,
  ArrowLeftRight,
  AlertTriangle,
  XCircle,
  ArrowRight,
  TrendingUp,
  CheckCircle2,
  Activity,
  Play,
} from 'lucide-react';
import { AnalyticsOverviewResponse, CommonEventEnvelope, AlertItem } from '../types';

interface OverviewPageProps {
  overview: AnalyticsOverviewResponse | null;
  recentEvents: CommonEventEnvelope[];
  activeAlerts: AlertItem[];
  onSelectEvent: (event: CommonEventEnvelope) => void;
  onNavigate: (page: any) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  overview,
  recentEvents,
  activeAlerts,
  onSelectEvent,
  onNavigate,
}) => {
  // Real live telemetry values from backend (defaults to 0 when starting fresh)
  const totalEvents = overview?.total_events ?? 0;
  const activeAgents = overview?.entities.active_agents ?? 0;
  const activeTasks = overview?.entities.active_tasks ?? 0;
  const activeSessions = overview?.entities.active_sessions ?? 0;
  const activeTransfers = overview?.entities.active_transfers ?? 0;
  const stalledCount = overview?.stalled_count ?? 0;
  const timeoutCount = overview?.timeout_count ?? 0;

  const kpis = [
    {
      title: 'Total Events',
      value: totalEvents,
      icon: BarChart3,
      trend: totalEvents > 0 ? '+100%' : '0%',
      trendUp: totalEvents > 0,
      iconBg: 'rgba(58, 134, 255, 0.15)',
      iconColor: '#3a86ff',
      glow: 'rgba(58, 134, 255, 0.3)',
    },
    {
      title: 'Active Agents',
      value: activeAgents,
      icon: Monitor,
      trend: activeAgents > 0 ? '+Active' : 'Idle',
      trendUp: activeAgents > 0,
      iconBg: 'rgba(16, 185, 129, 0.15)',
      iconColor: '#10b981',
      glow: 'rgba(16, 185, 129, 0.3)',
    },
    {
      title: 'Active Tasks',
      value: activeTasks,
      icon: ClipboardCheck,
      trend: activeTasks > 0 ? '+Active' : 'Idle',
      trendUp: activeTasks > 0,
      iconBg: 'rgba(255, 183, 3, 0.15)',
      iconColor: '#ffb703',
      glow: 'rgba(255, 183, 3, 0.3)',
    },
    {
      title: 'Active Sessions',
      value: activeSessions,
      icon: Share2,
      trend: activeSessions > 0 ? '+Active' : 'Idle',
      trendUp: activeSessions > 0,
      iconBg: 'rgba(168, 85, 247, 0.15)',
      iconColor: '#a855f7',
      glow: 'rgba(168, 85, 247, 0.3)',
    },
    {
      title: 'Active Transfers',
      value: activeTransfers,
      icon: ArrowLeftRight,
      trend: activeTransfers > 0 ? '+Active' : 'Idle',
      trendUp: activeTransfers > 0,
      iconBg: 'rgba(0, 245, 212, 0.15)',
      iconColor: '#00f5d4',
      glow: 'rgba(0, 245, 212, 0.3)',
    },
    {
      title: 'Stalled Entities',
      value: stalledCount,
      icon: AlertTriangle,
      trend: stalledCount > 0 ? `Alert` : 'Normal',
      trendUp: false,
      iconBg: 'rgba(255, 183, 3, 0.18)',
      iconColor: '#fbbf24',
      glow: 'rgba(255, 183, 3, 0.4)',
    },
    {
      title: 'Timeout Failures',
      value: timeoutCount,
      icon: XCircle,
      trend: timeoutCount > 0 ? `Failed` : 'Normal',
      trendUp: false,
      iconBg: 'rgba(239, 35, 60, 0.2)',
      iconColor: '#ef233c',
      glow: 'rgba(239, 35, 60, 0.4)',
    },
  ];

  // Real source distribution
  const sources = overview?.events_by_source || {};
  const p4Count = sources['p4_c2'] || 0;
  const p5Count = sources['p5_shell'] || 0;
  const p6Count = sources['p6_exfil'] || 0;
  const sumSources = p4Count + p5Count + p6Count;

  const p4Pct = sumSources > 0 ? Math.round((p4Count / sumSources) * 100) : 0;
  const p5Pct = sumSources > 0 ? Math.round((p5Count / sumSources) * 100) : 0;
  const p6Pct = sumSources > 0 ? Math.max(0, 100 - p4Pct - p5Pct) : 0;

  // Format Total display for Donut
  const formattedDonutTotal =
    totalEvents >= 1000 ? `${(totalEvents / 1000).toFixed(1)}K` : totalEvents.toString();

  // Compute dynamic timeline buckets from recentEvents (or default smooth guide when active)
  const hasEvents = recentEvents.length > 0;

  return (
    <div className="page-container">
      {/* 1. TOP ROW OF 7 FROSTED GLASS KPI CARDS (OPTION 2 EXACT) */}
      <div className="kpi-row-7">
        {kpis.map((k, i) => {
          const Icon = k.icon;
          return (
            <div key={i} className="kpi-glass-card">
              <div className="kpi-card-header">
                <div
                  className="kpi-icon-container"
                  style={{
                    backgroundColor: k.iconBg,
                    boxShadow: `0 0 12px ${k.glow}`,
                  }}
                >
                  <Icon size={17} color={k.iconColor} />
                </div>
                <div className="kpi-meta">
                  <span className="kpi-title-text">{k.title}</span>
                  <span className="kpi-value-text">{k.value.toLocaleString()}</span>
                </div>
              </div>
              <div className={`kpi-trend ${k.trendUp ? '' : 'kpi-trend-neutral'}`}>
                {k.trendUp && <TrendingUp size={12} />}
                <span>{k.trend}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* 2. OPTION 2 MIDDLE SECTION: 3 FROSTED PANELS */}
      <div className="overview-panels-grid">
        {/* PANEL 1: ANALYTICS OVERVIEW (MULTI-LINE SPLINE CHART) */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
          {/* Header & Legend */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '16px',
            }}
          >
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#ffffff' }}>
              Analytics Overview
            </h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '11px', fontWeight: 600 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#3a86ff' }} />
                <span style={{ color: 'var(--text-muted)' }}>P4 C2</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#b5179e' }} />
                <span style={{ color: 'var(--text-muted)' }}>P5 Shell</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#00f5d4' }} />
                <span style={{ color: 'var(--text-muted)' }}>P6 Exfil</span>
              </div>
            </div>
          </div>

          {/* SVG Smooth Spline Chart */}
          <div style={{ position: 'relative', width: '100%', height: '220px', marginTop: '10px' }}>
            {!hasEvents ? (
              <div
                style={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--text-dim)',
                  gap: '8px',
                }}
              >
                <Activity size={28} style={{ opacity: 0.4 }} />
                <div style={{ fontSize: '13px', fontWeight: 500 }}>No telemetry stream recorded yet.</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Use the header scenario injector above to start an operational stream.
                </div>
              </div>
            ) : (
              <svg
                viewBox="0 0 540 180"
                style={{ width: '100%', height: '100%', overflow: 'visible' }}
              >
                <defs>
                  <filter id="glow-line" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="2.5" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                  </filter>
                </defs>

                {/* Grid Lines & Y-Labels */}
                {[
                  { y: 20, label: '150' },
                  { y: 65, label: '100' },
                  { y: 110, label: '50' },
                  { y: 155, label: '0' },
                ].map((grid, idx) => (
                  <g key={idx}>
                    <text
                      x="24"
                      y={grid.y + 4}
                      fill="#64748b"
                      fontSize="10"
                      fontFamily="JetBrains Mono, monospace"
                      textAnchor="end"
                    >
                      {grid.label}
                    </text>
                    <line
                      x1="35"
                      y1={grid.y}
                      x2="530"
                      y2={grid.y}
                      stroke="rgba(255, 255, 255, 0.06)"
                      strokeDasharray="4 4"
                    />
                  </g>
                ))}

                {/* X-Axis Labels */}
                {[
                  { x: 50, label: 'T-4' },
                  { x: 165, label: 'T-3' },
                  { x: 280, label: 'T-2' },
                  { x: 395, label: 'T-1' },
                  { x: 510, label: 'Now' },
                ].map((tick, idx) => (
                  <text
                    key={idx}
                    x={tick.x}
                    y="175"
                    fill="#64748b"
                    fontSize="10"
                    fontFamily="JetBrains Mono, monospace"
                    textAnchor="middle"
                  >
                    {tick.label}
                  </text>
                ))}

                {/* Dynamic Curves proportional to ingested event counts */}
                {/* P4 Electric Blue Curve */}
                <path
                  d={`M 50 ${155 - Math.min(130, p4Count * 12)} C 110 130, 180 ${155 - Math.min(130, p4Count * 18)}, 280 ${155 - Math.min(130, p4Count * 22)} C 380 90, 450 ${155 - Math.min(130, p4Count * 25)}, 520 ${155 - Math.min(130, p4Count * 20)}`}
                  fill="none"
                  stroke="#3a86ff"
                  strokeWidth="2.5"
                  filter="url(#glow-line)"
                />

                {/* P5 Magenta Curve */}
                <path
                  d={`M 50 ${155 - Math.min(130, p5Count * 10)} C 130 140, 220 ${155 - Math.min(130, p5Count * 20)}, 310 ${155 - Math.min(130, p5Count * 15)} C 400 110, 470 ${155 - Math.min(130, p5Count * 24)}, 520 ${155 - Math.min(130, p5Count * 18)}`}
                  fill="none"
                  stroke="#b5179e"
                  strokeWidth="2.5"
                  filter="url(#glow-line)"
                />

                {/* P6 Cyan Curve */}
                <path
                  d={`M 50 ${155 - Math.min(130, p6Count * 8)} C 140 135, 230 ${155 - Math.min(130, p6Count * 16)}, 330 ${155 - Math.min(130, p6Count * 24)} C 420 85, 480 ${155 - Math.min(130, p6Count * 22)}, 520 ${155 - Math.min(130, p6Count * 25)}`}
                  fill="none"
                  stroke="#00f5d4"
                  strokeWidth="2.5"
                  filter="url(#glow-line)"
                />
              </svg>
            )}
          </div>
        </div>

        {/* PANEL 2: EVENT SOURCES (CONCENTRIC GLOWING DONUT CHART) */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#ffffff', marginBottom: '16px' }}>
            Event Sources
          </h3>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-around',
              flex: 1,
            }}
          >
            {/* SVG Donut */}
            <div style={{ position: 'relative', width: '130px', height: '130px' }}>
              <svg viewBox="0 0 100 100" style={{ transform: 'rotate(-90deg)', width: '100%', height: '100%' }}>
                {/* Background Ring */}
                <circle
                  cx="50"
                  cy="50"
                  r="38"
                  fill="transparent"
                  stroke="rgba(255, 255, 255, 0.05)"
                  strokeWidth="12"
                />
                {sumSources > 0 && (
                  <>
                    {/* P4 Segment */}
                    <circle
                      cx="50"
                      cy="50"
                      r="38"
                      fill="transparent"
                      stroke="#ffb703"
                      strokeWidth="12"
                      strokeDasharray={`${p4Pct * 2.38} 238`}
                      strokeDashoffset="0"
                    />
                    {/* P5 Segment */}
                    <circle
                      cx="50"
                      cy="50"
                      r="38"
                      fill="transparent"
                      stroke="#b5179e"
                      strokeWidth="12"
                      strokeDasharray={`${p5Pct * 2.38} 238`}
                      strokeDashoffset={`-${p4Pct * 2.38}`}
                    />
                    {/* P6 Segment */}
                    <circle
                      cx="50"
                      cy="50"
                      r="38"
                      fill="transparent"
                      stroke="#00f5d4"
                      strokeWidth="12"
                      strokeDasharray={`${p6Pct * 2.38} 238`}
                      strokeDashoffset={`-${(p4Pct + p5Pct) * 2.38}`}
                    />
                  </>
                )}
              </svg>
              {/* Donut Center Text */}
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <div style={{ fontSize: '18px', fontWeight: 800, color: '#ffffff', fontFamily: 'JetBrains Mono, monospace' }}>
                  {formattedDonutTotal}
                </div>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600 }}>
                  Total
                </div>
              </div>
            </div>

            {/* Legend on Right Side */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ffb703' }} />
                <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', width: '22px' }}>P4</span>
                <span style={{ fontSize: '12px', fontFamily: 'JetBrains Mono', color: 'var(--text-muted)' }}>
                  {p4Pct}%
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#b5179e' }} />
                <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', width: '22px' }}>P5</span>
                <span style={{ fontSize: '12px', fontFamily: 'JetBrains Mono', color: 'var(--text-muted)' }}>
                  {p5Pct}%
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#00f5d4' }} />
                <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', width: '22px' }}>P6</span>
                <span style={{ fontSize: '12px', fontFamily: 'JetBrains Mono', color: 'var(--text-muted)' }}>
                  {p6Pct}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* PANEL 3: RECENT ALERTS (100% REAL LIVE DATA) */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '16px',
            }}
          >
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#ffffff' }}>
              Recent Alerts
            </h3>
            <button
              onClick={() => onNavigate('alerts')}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#60a5fa',
                fontSize: '11px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <span>View All</span>
              <ArrowRight size={12} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flex: 1, justifyContent: 'center' }}>
            {activeAlerts.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '24px 12px', color: 'var(--text-muted)' }}>
                <CheckCircle2 size={30} color="#10b981" style={{ margin: '0 auto 8px' }} />
                <div style={{ fontWeight: 600, color: '#f8fafc', fontSize: '13px' }}>No Active Alerts</div>
                <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>
                  All entity heartbeats and sessions operating normally.
                </div>
              </div>
            ) : (
              activeAlerts.slice(0, 3).map((a, idx) => {
                const isCrit = a.severity === 'critical';
                const isMed = a.severity === 'warning';
                const badgeClass = isCrit
                  ? 'glass-badge-critical'
                  : isMed
                  ? 'glass-badge-medium'
                  : 'glass-badge-info';
                const badgeLabel = isCrit ? 'Critical' : isMed ? 'Medium' : 'Info';
                const dotColor = isCrit ? '#ef233c' : isMed ? '#ffb703' : '#3a86ff';

                return (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px 12px',
                      borderRadius: '10px',
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.05)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span
                        style={{
                          width: '7px',
                          height: '7px',
                          borderRadius: '50%',
                          backgroundColor: dotColor,
                          boxShadow: `0 0 6px ${dotColor}`,
                        }}
                      />
                      <div>
                        <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-main)' }}>
                          {a.message || `${a.alert_type} - ${a.entity_id}`}
                        </div>
                        <div style={{ fontSize: '10px', color: 'var(--text-dim)', marginTop: '2px' }}>
                          {new Date(a.last_updated_at).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>

                    <span className={`glass-badge ${badgeClass}`}>{badgeLabel}</span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* 3. RECENT EVENTS STREAM (FILTERABLE LIVE TABLE) */}
      <div className="glass-card" style={{ marginTop: '20px' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '16px',
          }}
        >
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#ffffff' }}>
              Operational Event Stream
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
              Canonical normalized events correlated across C2, Shell, and Covert Channels. Click any event to inspect.
            </p>
          </div>
          <button
            className="btn btn-outline"
            style={{ fontSize: '11px', padding: '6px 12px' }}
            onClick={() => onNavigate('events')}
          >
            <span>Open Live Event Explorer</span>
            <ArrowRight size={13} />
          </button>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Source</th>
                <th>Event Type</th>
                <th>Status</th>
                <th>Entity ID</th>
                <th>Technique</th>
                <th>Campaign</th>
                <th>Run</th>
              </tr>
            </thead>
            <tbody>
              {recentEvents.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '36px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                      <Activity size={24} style={{ opacity: 0.5 }} />
                      <div>No events captured in this scope.</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        Select a scenario from the top bar to inject and visualize operational telemetry.
                      </div>
                    </div>
                  </td>
                </tr>
              ) : (
                recentEvents.slice(0, 10).map((ev) => (
                  <tr
                    key={ev.event_id}
                    onClick={() => onSelectEvent(ev)}
                    style={{ cursor: 'pointer' }}
                    title="Click to view canonical payload"
                  >
                    <td className="font-mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {new Date(ev.ts).toLocaleTimeString()}
                    </td>
                    <td>
                      <span className={`badge badge-${ev.source.split('_')[0]}`}>
                        {ev.source.split('_')[0].toUpperCase()}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600 }}>{ev.type}</td>
                    <td>
                      <span className={`badge badge-status-${ev.status}`}>{ev.status}</span>
                    </td>
                    <td className="font-mono" style={{ fontSize: '11px' }}>
                      {ev.correlation.entity_id}
                    </td>
                    <td style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {ev.technique.attack_id}
                    </td>
                    <td className="font-mono" style={{ fontSize: '11px' }}>
                      {ev.campaign_id}
                    </td>
                    <td className="font-mono" style={{ fontSize: '11px' }}>
                      {ev.run_id}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
