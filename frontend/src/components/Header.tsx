import React, { useState } from 'react';
import {
  Flame,
  CheckCircle2,
  ChevronDown,
  Play,
  Loader2,
} from 'lucide-react';

interface HeaderProps {
  campaigns: string[];
  runs: string[];
  selectedCampaign: string;
  selectedRun: string;
  onSelectCampaign: (campaign: string) => void;
  onSelectRun: (run: string) => void;
  isLive: boolean;
  isReady: boolean;
  onTriggerDemo: (scenario: any) => Promise<void>;
  onTriggerWatchdogs: () => Promise<void>;
  onRefresh: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  campaigns,
  runs,
  selectedCampaign,
  selectedRun,
  onSelectCampaign,
  onSelectRun,
  isLive,
  isReady,
  onTriggerDemo,
  onTriggerWatchdogs,
  onRefresh,
}) => {
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ msg: string; type: 'success' | 'error' } | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<string>('normal');

  const handleAction = async (name: string, fn: () => Promise<any>) => {
    try {
      setLoadingAction(name);
      await fn();
      setNotification({ msg: `${name} executed successfully`, type: 'success' });
      setTimeout(() => setNotification(null), 4000);
    } catch (e: any) {
      setNotification({ msg: `${name} failed: ${e.message}`, type: 'error' });
      setTimeout(() => setNotification(null), 5000);
    } finally {
      setLoadingAction(null);
    }
  };

  const scenarios = [
    { id: 'normal', label: '1. Normal Scenario' },
    { id: 'agent_stalled', label: '2. Agent Stalled' },
    { id: 'task_stalled', label: '3. Task Stalled' },
    { id: 'handshake_timeout', label: '4. Session Timeout' },
    { id: 'session_stalled', label: '5. Session Stalled' },
    { id: 'transfer_stalled', label: '6. Transfer Stalled' },
    { id: 'mixed', label: '7. Mixed Operations' },
  ];

  return (
    <header className="header">
      {/* Option 2 Left: Title & Subtitle */}
      <div className="header-title-container">
        <h1
          style={{
            fontSize: 'clamp(16px, 1.4vw, 20px)',
            fontWeight: 800,
            letterSpacing: '-0.3px',
            color: '#ffffff',
          }}
        >
          Network Operator Analytics Console
        </h1>
        <p
          style={{
            fontSize: 'clamp(11px, 0.9vw, 12px)',
            color: 'var(--text-muted)',
            fontWeight: 500,
            marginTop: '2px',
          }}
        >
          Monitor &bull; Analyze &bull; Respond
        </p>
      </div>

      {/* Option 2 Right: Scopes, Live Badge, Actions */}
      <div className="header-controls-container">
        {/* Campaign Capsule Dropdown */}
        <div className="glass-capsule">
          <span style={{ color: 'var(--text-muted)', fontWeight: 500 }}>Campaign:</span>
          <select
            value={selectedCampaign}
            onChange={(e) => onSelectCampaign(e.target.value)}
          >
            <option value="">ALL CAMPAIGNS</option>
            {campaigns.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <ChevronDown size={14} color="var(--text-muted)" />
        </div>

        {/* Run Capsule Dropdown */}
        <div className="glass-capsule">
          <span style={{ color: 'var(--text-muted)', fontWeight: 500 }}>Run:</span>
          <select
            value={selectedRun}
            onChange={(e) => onSelectRun(e.target.value)}
          >
            <option value="">ALL RUNS</option>
            {runs.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
          <ChevronDown size={14} color="var(--text-muted)" />
        </div>

        {/* Option 2 Glowing Live Badge */}
        <div className="live-pill">
          <span className="pulse-dot" />
          <span>Live</span>
        </div>

        {/* Quick Demo Scenario Injector */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid var(--border-glass-bright)',
            borderRadius: '20px',
            padding: '2px 4px',
          }}
        >
          <select
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-lavender)',
              fontSize: '12px',
              fontFamily: 'Inter, sans-serif',
              fontWeight: 500,
              padding: '4px 8px',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            {scenarios.map((s) => (
              <option key={s.id} value={s.id} style={{ background: '#111428', color: '#fff' }}>
                {s.label}
              </option>
            ))}
          </select>
          <button
            onClick={() => handleAction('Inject Scenario', () => onTriggerDemo(selectedScenario))}
            disabled={loadingAction !== null}
            style={{
              background: 'rgba(114, 9, 183, 0.4)',
              border: '1px solid rgba(168, 85, 247, 0.4)',
              color: '#ffffff',
              borderRadius: '16px',
              padding: '4px 10px',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            {loadingAction === 'Inject Scenario' ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />}
            <span>Inject</span>
          </button>
        </div>

        {/* Watchdog Trigger Button */}
        <button
          onClick={() => handleAction('Watchdogs', onTriggerWatchdogs)}
          disabled={loadingAction !== null}
          title="Trigger Watchdog Detection"
          style={{
            background: 'rgba(239, 35, 60, 0.15)',
            border: '1px solid rgba(239, 35, 60, 0.35)',
            color: '#ff4d6d',
            borderRadius: '20px',
            padding: '6px 14px',
            fontSize: '12px',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            transition: 'all 0.15s ease',
          }}
        >
          {loadingAction === 'Watchdogs' ? <Loader2 size={13} className="animate-spin" /> : <Flame size={13} />}
          <span>Watchdogs</span>
        </button>
      </div>

      {/* Floating toast notification */}
      {notification && (
        <div
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            background: notification.type === 'success' ? 'rgba(16, 185, 129, 0.9)' : 'rgba(239, 68, 68, 0.9)',
            color: 'white',
            padding: '10px 18px',
            borderRadius: '8px',
            fontSize: '13px',
            fontWeight: 600,
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            zIndex: 100,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <CheckCircle2 size={16} />
          <span>{notification.msg}</span>
        </div>
      )}
    </header>
  );
};
