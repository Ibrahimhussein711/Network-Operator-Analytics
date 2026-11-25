import React from 'react';
import {
  LayoutDashboard,
  Layers,
  Activity,
  Boxes,
  Bell,
  BarChart3,
  FileText,
} from 'lucide-react';

export type PageId =
  | 'overview'
  | 'campaigns'
  | 'events'
  | 'entities'
  | 'alerts'
  | 'analytics'
  | 'reports';

interface SidebarProps {
  currentPage: PageId;
  onSelectPage: (page: PageId) => void;
  activeAlertCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onSelectPage,
  activeAlertCount,
}) => {
  const navItems = [
    { id: 'overview' as PageId, label: 'Overview', icon: LayoutDashboard },
    { id: 'campaigns' as PageId, label: 'Campaigns & Runs', icon: Layers },
    { id: 'events' as PageId, label: 'Live Events', icon: Activity },
    { id: 'entities' as PageId, label: 'Tracked Entities', icon: Boxes },
    {
      id: 'alerts' as PageId,
      label: 'Alerts',
      icon: Bell,
      badge: activeAlertCount > 0 ? activeAlertCount : undefined,
    },
    { id: 'analytics' as PageId, label: 'Analytics', icon: BarChart3 },
    { id: 'reports' as PageId, label: 'Reports', icon: FileText },
  ];

  return (
    <aside className="sidebar">
      {/* Brand Header with Option 2 Concentric Radar Emblem */}
      <div className="sidebar-brand-header">
        {/* Purple Concentric Radar Icon */}
        <div
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(168, 85, 247, 0.3) 0%, rgba(114, 9, 183, 0.1) 70%)',
            border: '1.5px solid rgba(168, 85, 247, 0.6)',
            boxShadow: '0 0 16px rgba(168, 85, 247, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="9" stroke="#c084fc" strokeWidth="1.2" strokeDasharray="3 2" />
            <circle cx="12" cy="12" r="6" stroke="#a855f7" strokeWidth="1.2" />
            <circle cx="12" cy="12" r="3" stroke="#e879f9" strokeWidth="1.5" />
            <circle cx="12" cy="12" r="1.5" fill="#f43f5e" />
            <line x1="12" y1="3" x2="12" y2="21" stroke="#a855f7" strokeWidth="0.8" strokeOpacity="0.6" />
            <line x1="3" y1="12" x2="21" y2="12" stroke="#a855f7" strokeWidth="0.8" strokeOpacity="0.6" />
          </svg>
        </div>

        <div className="sidebar-brand-text">
          <div
            style={{
              fontWeight: 800,
              fontSize: '15px',
              letterSpacing: '0.4px',
              color: '#ffffff',
            }}
          >
            Project 07
          </div>
          <div
            style={{
              fontSize: '11px',
              color: 'var(--text-muted)',
              fontWeight: 500,
              letterSpacing: '0.3px',
            }}
          >
            Red Analytics
          </div>
        </div>
      </div>

      {/* Nav List with Option 2 Glow Buttons */}
      <nav
        style={{
          padding: '16px 10px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          flex: 1,
        }}
      >
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectPage(item.id)}
              className={`sidebar-nav-button ${isActive ? 'nav-item-active' : ''}`}
              title={item.label}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: '10px',
                background: isActive ? undefined : 'transparent',
                color: isActive ? '#ffffff' : 'var(--text-muted)',
                border: isActive ? undefined : '1px solid transparent',
                fontWeight: isActive ? 600 : 500,
                fontSize: '13px',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Icon size={17} color={isActive ? '#ffffff' : 'var(--text-dim)'} style={{ flexShrink: 0 }} />
                <span className="nav-label">{item.label}</span>
              </div>
              {item.badge !== undefined && (
                <span
                  style={{
                    background: '#ef233c',
                    color: 'white',
                    fontSize: '10px',
                    fontWeight: 700,
                    padding: '2px 7px',
                    borderRadius: '10px',
                    boxShadow: '0 0 10px rgba(239, 35, 60, 0.5)',
                  }}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Option 2 Bottom Status: System Online capsule */}
      <div className="sidebar-footer">
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '7px 12px',
            borderRadius: '20px',
            background: 'rgba(16, 185, 129, 0.12)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: '#34d399',
            fontSize: '11px',
            fontWeight: 600,
            width: 'fit-content',
          }}
        >
          <span
            style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: '#34d399',
              boxShadow: '0 0 8px #34d399',
              flexShrink: 0,
            }}
          />
          <span className="sidebar-footer-text">System Online</span>
        </div>

        <div className="sidebar-footer-text" style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '2px' }}>
          CYBER-N201 // Team 10
        </div>
      </div>
    </aside>
  );
};
