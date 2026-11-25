"""
Tests for multi-run comparison and comprehensive demo scenarios.
"""

from datetime import datetime, timezone
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


@pytest.fixture
def mock_clock():
    return VirtualClock(datetime(2026, 11, 25, 12, 0, 0, tzinfo=timezone.utc))


@pytest.fixture
def app_client(mock_clock):
    reset_event_repository(clock=mock_clock)
    settings = IngestionSettings(
        ENVIRONMENT=EnvironmentEnum.TESTING,
        API_KEY_REQUIRED=False,
        WATCHDOG_AUTO_EVALUATE=False,
    )
    app = create_app(app_settings=settings)
    repo = get_event_repository()
    tracker = get_lifecycle_tracker()
    engine = WatchdogEngine(repository=repo, tracker=tracker, clock=mock_clock)
    app.dependency_overrides[get_system_clock] = lambda: mock_clock
    app.dependency_overrides[get_watchdog_engine] = lambda: engine
    return TestClient(app), engine, mock_clock


def test_all_demo_scenarios_injection_and_watchdog_triggers(app_client):
    """Verifies that all 7 demo scenarios inject valid canonical events and trigger appropriate watchdogs."""
    client, engine, clock = app_client

    scenarios = [
        ("normal", 0),  # healthy, 0 stalls
        ("agent_stalled", 1),  # beacon_missed
        ("task_stalled", 1),  # task_stalled
        ("handshake_timeout", 1),  # timeout_expired (handshake_timeout)
        ("session_stalled", 1),  # session_stalled
        ("transfer_stalled", 1),  # transfer_stalled
        ("mixed", 3),  # multiple stalls + timeout
    ]

    for sc, expected_watchdog_count in scenarios:
        camp = f"camp-test-{sc}"
        res = client.post(f"/api/v1/demo/inject?scenario={sc}&campaign_id={camp}&run_id=run-01")
        assert res.status_code == 200, f"Scenario {sc} injection failed: {res.text}"
        data = res.json()
        assert data["status"] == "success"
        assert data["events_injected"] > 0

        # Advance clock past 2s
        clock.advance(2)

        # Trigger watchdog for this campaign
        emitted = engine.check_watchdogs(campaign_id=camp, run_id="run-01")
        assert len(emitted) == expected_watchdog_count, (
            f"Scenario {sc}: expected {expected_watchdog_count} watchdog events, got {len(emitted)}"
        )


def test_multi_run_comparison_endpoint(app_client):
    """Verifies that GET /campaigns/{campaign_id}/compare correctly reports differences across two runs."""
    client, engine, clock = app_client
    campaign_id = "camp-comparison-01"

    # Run A: Normal scenario
    res_a = client.post(f"/api/v1/demo/inject?scenario=normal&campaign_id={campaign_id}&run_id=run-01")
    assert res_a.status_code == 200

    # Run B: Stalled scenario with multiple events
    res_b = client.post(f"/api/v1/demo/inject?scenario=mixed&campaign_id={campaign_id}&run_id=run-02")
    assert res_b.status_code == 200

    # Trigger watchdog for run-02 to generate stalls
    clock.advance(3)
    engine.check_watchdogs(campaign_id=campaign_id, run_id="run-02")

    # Call comparison endpoint
    comp_res = client.get(f"/api/v1/analytics/campaigns/{campaign_id}/compare?run_a=run-01&run_b=run-02")
    assert comp_res.status_code == 200
    comp_data = comp_res.json()

    assert comp_data["campaign_id"] == campaign_id
    assert comp_data["run_a"]["run_id"] == "run-01"
    assert comp_data["run_b"]["run_id"] == "run-02"

    assert comp_data["run_a"]["total_events"] > 0
    assert comp_data["run_b"]["total_events"] > 0
    assert "differences" in comp_data
    assert "event_count_delta" in comp_data["differences"]
    assert "unique_entities_delta" in comp_data["differences"]
    assert comp_data["run_b"]["stalled_entities"] > 0
