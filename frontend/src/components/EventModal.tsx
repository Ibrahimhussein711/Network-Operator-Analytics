import React from 'react';
import { X, Copy, Check } from 'lucide-react';
import { CommonEventEnvelope } from '../types';

interface EventModalProps {
  event: CommonEventEnvelope | null;
  onClose: () => void;
}

export const EventModal: React.FC<EventModalProps> = ({ event, onClose }) => {
  const [copied, setCopied] = React.useState(false);

  if (!event) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(event, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className={`badge badge-${event.source}`}>{event.source}</span>
            <span style={{ fontWeight: 700, fontSize: '15px' }}>{event.type}</span>
            <span className={`badge badge-status-${event.status}`}>{event.status}</span>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {/* Metadata Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '12px',
              background: 'var(--bg-darker)',
              padding: '14px',
              borderRadius: '6px',
              marginBottom: '18px',
              border: '1px solid var(--border)',
              fontSize: '12px',
            }}
          >
            <div>
              <span style={{ color: 'var(--text-dim)', fontWeight: 600 }}>EVENT ID: </span>
              <span className="font-mono">{event.event_id}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-dim)', fontWeight: 600 }}>TIMESTAMP: </span>
              <span className="font-mono">{event.ts}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-dim)', fontWeight: 600 }}>CAMPAIGN / RUN: </span>
              <span className="font-mono">{event.campaign_id} / {event.run_id}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-dim)', fontWeight: 600 }}>ENTITY: </span>
              <span className="font-mono">{event.correlation.entity_type} [{event.correlation.entity_id}]</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-dim)', fontWeight: 600 }}>HOST: </span>
              <span className="font-mono">{event.host.ip} ({event.host.host_id})</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-dim)', fontWeight: 600 }}>TECHNIQUE: </span>
              <span>{event.technique.internal_name} ({event.technique.attack_id})</span>
            </div>
          </div>

          {/* Formatted JSON Viewer */}
          <div style={{ position: 'relative' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '6px',
              }}
            >
              <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                Canonical Envelope Payload
              </span>
              <button
                className="btn btn-outline"
                style={{ padding: '3px 8px', fontSize: '11px' }}
                onClick={handleCopy}
              >
                {copied ? <Check size={12} color="#34d399" /> : <Copy size={12} />}
                <span>{copied ? 'Copied' : 'Copy JSON'}</span>
              </button>
            </div>
            <pre
              style={{
                background: 'var(--bg-darker)',
                padding: '16px',
                borderRadius: '6px',
                border: '1px solid var(--border)',
                overflowX: 'auto',
                fontSize: '12px',
                color: '#93c5fd',
                lineHeight: 1.5,
              }}
            >
              {JSON.stringify(event, null, 2)}
            </pre>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-primary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
