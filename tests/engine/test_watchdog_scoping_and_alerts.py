"""
Unit tests for watchdog scoping (campaign/run isolation), alert lifecycle, and concurrency.
"""

from datetime import datetime, timezone
import threading
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.config import EnvironmentEnum, IngestionSettings
from api.dependencies import (
    get_event_repository,
    get_lifecycle_tracker,
    get_system_clock,
    get_watchdog_engine,
    reset_event_repository,
)
from engine.clock import VirtualClock
from engine.tracker import LifecycleTracker
from engine.watchdog import WatchdogEngine
from synthetic.p4_generator import P4C2Generator


@pytest.fixture
def mock_clock():
    return VirtualClock(datetime(2026, 11, 25, 12, 0, 0, tzinfo=timezone.utc))


@pytest.fixture
def setup_isolated_app(mock_clock):
    reset_event_repository(clock=mock_clock)
    settings = IngestionSettings(
        ENVIRONMENT=EnvironmentEnum.TESTING,
        API_KEY_REQUIRED=False,
        WATCHDOG_AUTO_EVALUATE=False,
    )
    app = create_app(app_settings=settings)

    # Inject mock clock into engine and clock dependencies
    repo = get_event_repository()
    tracker = get_lifecycle_tracker()
    engine = WatchdogEngine(repository=repo, tracker=tracker, clock=mock_clock)
    app.dependency_overrides[get_system_clock] = lambda: mock_clock
    app.dependency_overrides[get_watchdog_engine] = lambda: engine

    return app, client_fixture(app), repo, tracker, engine, mock_clock


def client_fixture(app):
    return TestClient(app)


def test_watchdog_campaign_and_run_scoping(setup_isolated_app):
    """Verifies that scoping by campaign and run evaluates ONLY the targeted entities."""
    app, client, repo, tracker, engine, clock = setup_isolated_app

    # Create entities in two separate campaigns
    gen_c1_r1 = P4C2Generator(campaign_id="campaign-A", run_id="run-1")
    gen_c1_r2 = P4C2Generator(campaign_id="campaign-A", run_id="run-2")
    gen_c2_r1 = P4C2Generator(campaign_id="campaign-B", run_id="run-1")

    ev_a1 = gen_c1_r1.register_agent(agent_id="agent-a1", timeout_sec=5)
    ev_a2 = gen_c1_r2.register_agent(agent_id="agent-a2", timeout_sec=5)
    ev_b1 = gen_c2_r1.register_agent(agent_id="agent-b1", timeout_sec=5)

    client.post("/api/v1/events", json=ev_a1)
    client.post("/api/v1/events", json=ev_a2)
    client.post("/api/v1/events", json=ev_b1)

    # Advance clock past stall deadline
    clock.advance(6)

    # 1. Scoped evaluate: only campaign-A, run-1
    res = client.post("/api/v1/watchdogs/trigger?campaign_id=campaign-A&run_id=run-1")
    assert res.status_code == 200
    emitted = res.json()
    assert len(emitted) == 1
    assert emitted[0]["campaign_id"] == "campaign-A"
    assert emitted[0]["run_id"] == "run-1"
    assert emitted[0]["type"] == "beacon_missed"

    # Entities in campaign-A run-2 and campaign-B run-1 must NOT have stalled yet
    e_a2 = tracker.get_entity("campaign-A", "run-2", "agent-a2")
    assert not e_a2.is_stalled

    e_b1 = tracker.get_entity("campaign-B", "run-1", "agent-b1")
    assert not e_b1.is_stalled

    # 2. Scoped evaluate: campaign-A without run_id (evaluates run-2)
    res2 = client.post("/api/v1/watchdogs/trigger?campaign_id=campaign-A")
    assert res2.status_code == 200
    emitted2 = res2.json()
    # run-1 is already stalled, so only run-2 emits
    assert len(emitted2) == 1
    assert emitted2[0]["campaign_id"] == "campaign-A"
    assert emitted2[0]["run_id"] == "run-2"

    # campaign-B is still untouched
    e_b1 = tracker.get_entity("campaign-B", "run-1", "agent-b1")
    assert not e_b1.is_stalled


def test_alert_lifecycle_active_resolved_historical(setup_isolated_app):
    """Verifies that alerts correctly transition from active -> resolved, or active -> timed_out."""
    app, client, repo, tracker, engine, clock = setup_isolated_app

    gen = P4C2Generator(campaign_id="campaign-alert", run_id="run-01")
    reg = gen.register_agent(agent_id="agent-alert-01", timeout_sec=5)
    client.post("/api/v1/events", json=reg)

    # Advance to stall
    clock.advance(6)
    client.post("/api/v1/watchdogs/trigger")

    # Check alert center: active alert present
    res_alerts = client.get("/api/v1/analytics/alerts?campaign_id=campaign-alert")
    assert res_alerts.status_code == 200
    data = res_alerts.json()
    assert data["total_active"] == 1
    assert data["total_resolved"] == 0
    assert data["total_historical"] == 0
    assert data["active"][0]["entity_id"] == "agent-alert-01"
    assert data["active"][0]["severity"] == "warning"

    # Now agent sends check-in before grace period expires -> RECOVERY
    checkin = gen.beacon_checkin(agent_id="agent-alert-01", timeout_sec=5)
    client.post("/api/v1/events", json=checkin)

    # Alert should now be resolved!
    res_alerts_rec = client.get("/api/v1/analytics/alerts?campaign_id=campaign-alert")
    data_rec = res_alerts_rec.json()
    assert data_rec["total_active"] == 0
    assert data_rec["total_resolved"] == 1
    assert data_rec["resolved"][0]["is_recovered"] is True

    # Advance clock to stall again -> new active alert
    clock.advance(6)
    client.post("/api/v1/watchdogs/trigger")

    res_alerts_stall2 = client.get("/api/v1/analytics/alerts?campaign_id=campaign-alert")
    data_s2 = res_alerts_stall2.json()
    assert data_s2["total_active"] == 1
    assert data_s2["total_resolved"] == 1

    # Advance past grace period -> TIMEOUT (critical, historical)
    clock.advance(6)
    client.post("/api/v1/watchdogs/trigger")

    res_alerts_to = client.get("/api/v1/analytics/alerts?campaign_id=campaign-alert")
    data_to = res_alerts_to.json()
    assert data_to["total_active"] == 0
    assert data_to["total_historical"] == 1
    assert data_to["historical"][0]["current_status"] == "timed_out"
    assert data_to["historical"][0]["severity"] == "critical"
    assert data_to["historical"][0]["is_timeout"] is True


def test_watchdog_concurrency_and_deduplication(setup_isolated_app):
    """Verifies that concurrent watchdog triggers do not duplicate P7 events."""
    app, client, repo, tracker, engine, clock = setup_isolated_app

    gen = P4C2Generator(campaign_id="campaign-concur", run_id="run-01")
    reg = gen.register_agent(agent_id="agent-concur-01", timeout_sec=5)
    client.post("/api/v1/events", json=reg)

    clock.advance(6)

    # Spawn 5 concurrent threads triggering watchdog evaluation
    results = []
    errors = []

    def run_trigger():
        try:
            evs = engine.check_watchdogs()
            results.append(evs)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=run_trigger) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    # Flatten results
    total_events = [ev for sublist in results for ev in sublist]
    # Exactly ONE beacon_missed event must have been emitted across all concurrent calls!
    assert len(total_events) == 1
    assert total_events[0].type == "beacon_missed"
