"""
Integration tests for Frontend Dashboard serving and Watchdog trigger endpoint.
"""

from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.dependencies import reset_event_repository
from synthetic.p4_generator import P4C2Generator


@pytest.fixture(autouse=True)
def clean_state():
    reset_event_repository()
    yield
    reset_event_repository()


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_dashboard_routes_serve_html(client):
    """Verify GET / and GET /dashboard return HTML dashboard."""
    resp_root = client.get("/")
    assert resp_root.status_code == 200
    assert "text/html" in resp_root.headers.get("content-type", "")
    assert "Project 07 // Red Team Network Operator Analytics" in resp_root.text

    resp_dash = client.get("/dashboard")
    assert resp_dash.status_code == 200
    assert "text/html" in resp_dash.headers.get("content-type", "")


def test_watchdog_trigger_endpoint_execution(client):
    """Verify POST /api/v1/watchdogs/trigger executes watchdog cycle."""
    resp = client.post("/api/v1/watchdogs/trigger")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_end_to_end_analytics_pipeline(client):
    """Verify full pipeline: event ingestion -> entity tracking -> report generation."""
    p4 = P4C2Generator(campaign_id="e2e-camp", run_id="run-01")
    agent_id = f"agent-e2e-{uuid4().hex[:6]}"
    task_id = f"task-e2e-{uuid4().hex[:6]}"

    ev1 = p4.register_agent(agent_id=agent_id, timeout_sec=60)
    ev2 = p4.start_task(agent_id=agent_id, task_id=task_id, timeout_sec=60)
    ev3 = p4.complete_task(agent_id=agent_id, task_id=task_id)

    # Ingest batch
    resp_ingest = client.post("/api/v1/events/batch", json={"events": [ev1, ev2, ev3]})
    assert resp_ingest.status_code == 200
    data = resp_ingest.json()
    assert data["accepted_count"] == 3

    # Overview analytics
    resp_ov = client.get("/api/v1/analytics/overview?campaign_id=e2e-camp")
    assert resp_ov.status_code == 200
    ov = resp_ov.json()
    assert ov["total_events"] == 3
    assert ov["entities"]["active_agents"] == 1

    # Entity states
    resp_ent = client.get("/api/v1/analytics/entities?campaign_id=e2e-camp")
    assert resp_ent.status_code == 200
    entities = resp_ent.json()
    assert len(entities) == 2
    task_entity = next(e for e in entities if e["entity_id"] == task_id)
    assert task_entity["is_terminal"] is True
    assert task_entity["current_status"] == "completed"

    # Campaign report
    resp_rep = client.get("/api/v1/analytics/campaigns/e2e-camp/report")
    assert resp_rep.status_code == 200
    rep = resp_rep.json()
    assert rep["campaign_id"] == "e2e-camp"
    assert rep["total_events"] == 3
    assert rep["total_agents"] == 1
    assert rep["total_tasks"] == 1
