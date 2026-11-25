import React, { useEffect, useState, useCallback } from 'react';
import { Sidebar, PageId } from './components/Sidebar';
import { Header } from './components/Header';
import { EventModal } from './components/EventModal';
import { OverviewPage } from './pages/OverviewPage';
import { CampaignsPage } from './pages/CampaignsPage';
import { EventsPage } from './pages/EventsPage';
import { EntitiesPage } from './pages/EntitiesPage';
import { AlertsPage } from './pages/AlertsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ReportsPage } from './pages/ReportsPage';
import { api } from './services/api';
import {
  AlertsResponse,
  AnalyticsOverviewResponse,
  CommonEventEnvelope,
  EntitySummary,
} from './types';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageId>('overview');

  // Health
  const [isLive, setIsLive] = useState(false);
  const [isReady, setIsReady] = useState(false);

  // Scopes
  const [campaigns, setCampaigns] = useState<string[]>([]);
  const [runs, setRuns] = useState<string[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<string>('');
  const [selectedRun, setSelectedRun] = useState<string>('');

  // Telemetry data
  const [overview, setOverview] = useState<AnalyticsOverviewResponse | null>(null);
  const [events, setEvents] = useState<CommonEventEnvelope[]>([]);
  const [entities, setEntities] = useState<EntitySummary[]>([]);
  const [alertsData, setAlertsData] = useState<AlertsResponse | null>(null);

  // Active modal
  const [selectedEventModal, setSelectedEventModal] = useState<CommonEventEnvelope | null>(null);

  // Auto-polling
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch campaigns
  const fetchCampaigns = useCallback(async () => {
    try {
      const cList = await api.getCampaigns();
      setCampaigns(cList);
    } catch (e) {
      console.error('Error fetching campaigns:', e);
    }
  }, []);

  // Fetch runs when campaign changes
  useEffect(() => {
    if (selectedCampaign) {
      api.getRuns(selectedCampaign)
        .then((rList) => setRuns(rList))
        .catch(() => setRuns([]));
    } else {
      setRuns([]);
      setSelectedRun('');
    }
  }, [selectedCampaign]);

  // Main data polling
  const refreshAllData = useCallback(async () => {
    try {
      // 1. Health
      const [liveRes, readyRes] = await Promise.allSettled([api.getLiveness(), api.getReadiness()]);
      setIsLive(liveRes.status === 'fulfilled' && liveRes.value.status === 'live');
      setIsReady(readyRes.status === 'fulfilled' && readyRes.value.status === 'ready');

      // 2. Telemetry
      const [ovRes, evRes, entRes, altRes] = await Promise.allSettled([
        api.getOverview(selectedCampaign || undefined, selectedRun || undefined),
        api.getEvents({
          campaignId: selectedCampaign || undefined,
          runId: selectedRun || undefined,
          limit: 100,
        }),
        api.getEntities(selectedCampaign || undefined, selectedRun || undefined),
        api.getAlerts(selectedCampaign || undefined, selectedRun || undefined),
      ]);

      if (ovRes.status === 'fulfilled') setOverview(ovRes.value);
      if (evRes.status === 'fulfilled') setEvents(evRes.value);
      if (entRes.status === 'fulfilled') setEntities(entRes.value);
      if (altRes.status === 'fulfilled') setAlertsData(altRes.value);

      // Refresh campaigns list periodically
      fetchCampaigns();
    } catch (e) {
      console.error('Data polling error:', e);
    }
  }, [selectedCampaign, selectedRun, fetchCampaigns]);

  // Initial load
  useEffect(() => {
    refreshAllData();
  }, [refreshAllData]);

  // Auto refresh interval
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(refreshAllData, 3000);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshAllData]);

  // Trigger Demo Scenario
  const handleTriggerDemo = async (scenario: any) => {
    const res = await api.injectDemo(scenario, selectedCampaign || undefined, selectedRun || undefined);
    if (!selectedCampaign) {
      setSelectedCampaign(res.campaign_id);
    }
    await refreshAllData();
  };

  // Trigger Watchdogs
  const handleTriggerWatchdogs = async () => {
    await api.triggerWatchdogs(selectedCampaign || undefined, selectedRun || undefined);
    await refreshAllData();
  };

  return (
    <div className="app-container">
      <Sidebar
        currentPage={currentPage}
        onSelectPage={setCurrentPage}
        activeAlertCount={alertsData?.total_active || 0}
      />

      <div className="main-content">
        <Header
          campaigns={campaigns}
          runs={runs}
          selectedCampaign={selectedCampaign}
          selectedRun={selectedRun}
          onSelectCampaign={setSelectedCampaign}
          onSelectRun={setSelectedRun}
          isLive={isLive}
          isReady={isReady}
          onTriggerDemo={handleTriggerDemo}
          onTriggerWatchdogs={handleTriggerWatchdogs}
          onRefresh={refreshAllData}
        />

        <main>
          {currentPage === 'overview' && (
            <OverviewPage
              overview={overview}
              recentEvents={events}
              activeAlerts={alertsData?.active || []}
              onSelectEvent={setSelectedEventModal}
              onNavigate={setCurrentPage}
            />
          )}

          {currentPage === 'campaigns' && (
            <CampaignsPage
              campaigns={campaigns}
              selectedCampaign={selectedCampaign}
              onSelectCampaign={setSelectedCampaign}
              onNavigate={setCurrentPage}
            />
          )}

          {currentPage === 'events' && (
            <EventsPage
              events={events}
              onSelectEvent={setSelectedEventModal}
              onRefresh={refreshAllData}
              autoRefresh={autoRefresh}
              onToggleAutoRefresh={setAutoRefresh}
            />
          )}

          {currentPage === 'entities' && <EntitiesPage entities={entities} />}

          {currentPage === 'alerts' && (
            <AlertsPage alertsData={alertsData} onRefresh={refreshAllData} />
          )}

          {currentPage === 'analytics' && (
            <AnalyticsPage overview={overview} entities={entities} />
          )}

          {currentPage === 'reports' && (
            <ReportsPage
              campaigns={campaigns}
              selectedCampaign={selectedCampaign}
              onSelectCampaign={setSelectedCampaign}
            />
          )}
        </main>
      </div>

      <EventModal
        event={selectedEventModal}
        onClose={() => setSelectedEventModal(null)}
      />
    </div>
  );
};
export default App;
