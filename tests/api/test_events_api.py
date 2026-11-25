"""
Integration tests for Event Ingestion (Single, Batch) and Analytics API routes.
"""

import copy
from datetime import datetime, timezone
from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.config import EnvironmentEnum, IngestionSettings
from api.dependencies import get_event_repository, reset_event_repository
from api.responses import (
    BatchIngestionResponse,
    ErrorResponse,
    EventIngestedResponse,
)
from api.storage.memory import ThreadSafeInMemoryEventRepository


@pytest.fixture(autouse=True)
def clean_state():
    reset_event_repository()
    yield
    reset_event_repository()


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


# ==============================================================================
# SINGLE EVENT INGESTION TESTS
# ==============================================================================

def test_ingest_single_event_success(client, canonical_events):
    """1. Ingest a valid P4 event -> returns HTTP 201 Created and accepted response."""
    payload = copy.deepcopy(canonical_events["agent_registered"])
    payload["event_id"] = str(uuid4())

    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 201

    data = response.json()
    model = EventIngestedResponse.model_validate(data)
    assert model.status == "accepted"
    assert str(model.event_id) == payload["event_id"]
    assert isinstance(model.received_at, datetime)

    # Verify event stored in repository
    repo = get_event_repository()
    stored = repo.get_by_id(model.event_id)
    assert stored is not None
    assert stored.received_at is not None


def test_ingest_single_event_idempotent_duplicate(client, canonical_events):
    """2. Submitting an identical event returns HTTP 200 OK and deduplicated response."""
    payload = copy.deepcopy(canonical_events["task_started"])
    payload["event_id"] = str(uuid4())

    # First submission
    resp1 = client.post("/api/v1/events", json=payload)
    assert resp1.status_code == 201
    orig_received_at = resp1.json()["received_at"]

    # Second submission with same payload
    resp2 = client.post("/api/v1/events", json=payload)
    assert resp2.status_code == 200

    data = resp2.json()
    assert data["status"] == "deduplicated"
    assert data["event_id"] == payload["event_id"]
    # Invariant: Must return original stored received_at
    assert data["received_at"] == orig_received_at


def test_ingest_single_event_conflict(client, canonical_events):
    """3. Submitting the same event_id with different payload returns HTTP 409 Conflict."""
    payload1 = copy.deepcopy(canonical_events["connection_established"])
    event_id = str(uuid4())
    payload1["event_id"] = event_id

    resp1 = client.post("/api/v1/events", json=payload1)
    assert resp1.status_code == 201

    # Mutate payload keeping same event_id
    payload2 = copy.deepcopy(payload1)
    payload2["details"]["interactive_prompt_ready"] = False

    resp2 = client.post("/api/v1/events", json=payload2)
    assert resp2.status_code == 409

    err = ErrorResponse.model_validate(resp2.json())
    assert err.error == "Conflict"
    assert str(err.event_id) == event_id


def test_ingest_rejects_external_p7_event(client, canonical_events):
    """4. Submitting a p7_analytics event to external ingestion returns HTTP 422."""
    payload = copy.deepcopy(canonical_events["beacon_missed"])
    payload["event_id"] = str(uuid4())

    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 422

    err = ErrorResponse.model_validate(response.json())
    assert "p7_analytics" in err.message


def test_ingest_rejects_schema_validation_failure(client, canonical_events):
    """5. Invalid schema (e.g. missing required field, bad status) returns HTTP 422."""
    payload = copy.deepcopy(canonical_events["agent_registered"])
    payload["event_id"] = str(uuid4())
    payload.pop("technique")  # Required envelope field

    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 422

    err = ErrorResponse.model_validate(response.json())
    assert err.error == "Validation Error"
    assert err.details is not None


def test_ingest_source_type_mismatch_rejected(client, canonical_events):
    """6. Cross-source type mismatch returns HTTP 422."""
    payload = copy.deepcopy(canonical_events["agent_registered"])
    payload["event_id"] = str(uuid4())
    payload["source"] = "p5_shell"  # Mismatch: agent_registered belongs to p4_c2

    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 422


def test_ingest_authentication_required(canonical_events):
    """7. Authentication is enforced when API_KEY_REQUIRED is True."""
    cfg = IngestionSettings(
        ENVIRONMENT=EnvironmentEnum.TESTING,
        API_KEY_REQUIRED=True,
        API_KEY="test-secret-key-xyz",
    )
    secured_app = create_app(app_settings=cfg)
    secured_client = TestClient(secured_app)

    payload = copy.deepcopy(canonical_events["agent_registered"])
    payload["event_id"] = str(uuid4())

    # Missing API key header -> 401
    resp_no_auth = secured_client.post("/api/v1/events", json=payload)
    assert resp_no_auth.status_code == 401

    # Invalid API key header -> 401
    resp_bad_auth = secured_client.post(
        "/api/v1/events",
        json=payload,
        headers={"X-API-Key": "wrong-key"},
    )
    assert resp_bad_auth.status_code == 401

    # Valid API key header -> 201
    resp_good_auth = secured_client.post(
        "/api/v1/events",
        json=payload,
        headers={"X-API-Key": "test-secret-key-xyz"},
    )
    assert resp_good_auth.status_code == 201


def test_ingest_storage_unavailable(client, canonical_events):
    """8. Storage failure returns HTTP 503."""
    repo = get_event_repository()
    assert isinstance(repo, ThreadSafeInMemoryEventRepository)
    repo.set_healthy(False)

    payload = copy.deepcopy(canonical_events["agent_registered"])
    payload["event_id"] = str(uuid4())

    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 503
    err = ErrorResponse.model_validate(response.json())
    assert err.error == "Service Unavailable"


# ==============================================================================
# BATCH EVENT INGESTION TESTS
# ==============================================================================

def test_ingest_batch_all_valid(client, canonical_events):
    """9. Ingesting a batch of valid events returns accepted for all items."""
    ev1 = copy.deepcopy(canonical_events["agent_registered"])
    ev1["event_id"] = str(uuid4())
    ev2 = copy.deepcopy(canonical_events["connection_requested"])
    ev2["event_id"] = str(uuid4())
    ev3 = copy.deepcopy(canonical_events["transfer_started"])
    ev3["event_id"] = str(uuid4())

    response = client.post("/api/v1/events/batch", json=[ev1, ev2, ev3])
    assert response.status_code == 200

    data = response.json()
    batch_resp = BatchIngestionResponse.model_validate(data)
    assert batch_resp.total_submitted == 3
    assert batch_resp.accepted_count == 3
    assert batch_resp.deduplicated_count == 0
    assert batch_resp.failed_count == 0
    assert len(batch_resp.results) == 3


def test_ingest_batch_partial_success(client, canonical_events):
    """10. Ingesting a mixed batch processes valid events even when some fail."""
    ev_valid = copy.deepcopy(canonical_events["agent_registered"])
    ev_valid["event_id"] = str(uuid4())

    ev_bad_schema = copy.deepcopy(canonical_events["connection_requested"])
    ev_bad_schema["event_id"] = str(uuid4())
    ev_bad_schema.pop("technique")

    ev_p7 = copy.deepcopy(canonical_events["beacon_missed"])
    ev_p7["event_id"] = str(uuid4())

    response = client.post(
        "/api/v1/events/batch",
        json={"events": [ev_valid, ev_bad_schema, ev_p7]},
    )
    assert response.status_code == 200

    data = response.json()
    batch_resp = BatchIngestionResponse.model_validate(data)
    assert batch_resp.total_submitted == 3
    assert batch_resp.accepted_count == 1
    assert batch_resp.failed_count == 2

    # Verify that valid event was indeed saved in repository
    repo = get_event_repository()
    assert repo.get_by_id(UUID(ev_valid["event_id"])) is not None


def test_ingest_batch_exceeds_max_limit(client, canonical_events):
    """11. Batch exceeding MAX_BATCH_SIZE is rejected with HTTP 422."""
    cfg = IngestionSettings(MAX_BATCH_SIZE=2)
    small_batch_app = create_app(app_settings=cfg)
    small_batch_client = TestClient(small_batch_app)

    items = [copy.deepcopy(canonical_events["agent_registered"]) for _ in range(3)]
    for item in items:
        item["event_id"] = str(uuid4())

    response = small_batch_client.post("/api/v1/events/batch", json=items)
    assert response.status_code == 422
    err = ErrorResponse.model_validate(response.json())
    assert "exceeds maximum allowed limit" in err.message


# ==============================================================================
# QUERY AND ANALYTICS ENDPOINTS TESTS
# ==============================================================================

def test_query_events_and_filtering(client, canonical_events):
    """12. Query stored events with campaign, run, and pagination filters."""
    ev1 = copy.deepcopy(canonical_events["agent_registered"])
    ev1["event_id"] = str(uuid4())
    ev1["campaign_id"] = "campaign-query-1"
    ev1["run_id"] = "run-01"

    ev2 = copy.deepcopy(canonical_events["connection_requested"])
    ev2["event_id"] = str(uuid4())
    ev2["campaign_id"] = "campaign-query-1"
    ev2["run_id"] = "run-02"

    ev3 = copy.deepcopy(canonical_events["transfer_started"])
    ev3["event_id"] = str(uuid4())
    ev3["campaign_id"] = "campaign-query-2"
    ev3["run_id"] = "run-01"

    client.post("/api/v1/events/batch", json=[ev1, ev2, ev3])

    # Query all
    resp_all = client.get("/api/v1/events")
    assert resp_all.status_code == 200
    assert len(resp_all.json()) == 3

    # Filter by campaign
    resp_c1 = client.get("/api/v1/events?campaign_id=campaign-query-1")
    assert len(resp_c1.json()) == 2

    # Filter by run
    resp_r2 = client.get("/api/v1/events?campaign_id=campaign-query-1&run_id=run-02")
    assert len(resp_r2.json()) == 1

    # Single event retrieval
    resp_single = client.get(f"/api/v1/events/{ev1['event_id']}")
    assert resp_single.status_code == 200
    assert resp_single.json()["event_id"] == ev1["event_id"]

    # Unknown event -> 404
    resp_not_found = client.get(f"/api/v1/events/{uuid4()}")
    assert resp_not_found.status_code == 404


def test_campaign_discovery_and_reporting(client, canonical_events):
    """13. Campaign listing, run listing, and executive campaign report."""
    ev1 = copy.deepcopy(canonical_events["agent_registered"])
    ev1["event_id"] = str(uuid4())
    ev1["campaign_id"] = "reporting-camp"
    ev1["run_id"] = "run-A"

    client.post("/api/v1/events", json=ev1)

    # Campaigns list
    resp_camps = client.get("/api/v1/campaigns")
    assert resp_camps.status_code == 200
    assert "reporting-camp" in resp_camps.json()

    # Runs list
    resp_runs = client.get("/api/v1/campaigns/reporting-camp/runs")
    assert resp_runs.status_code == 200
    assert "run-A" in resp_runs.json()

    # Analytics overview
    resp_overview = client.get("/api/v1/analytics/overview?campaign_id=reporting-camp")
    assert resp_overview.status_code == 200
    overview = resp_overview.json()
    assert overview["total_events"] == 1
    assert overview["events_by_source"]["p4_c2"] == 1

    # Campaign report
    resp_report = client.get("/api/v1/analytics/campaigns/reporting-camp/report")
    assert resp_report.status_code == 200
    report = resp_report.json()
    assert report["campaign_id"] == "reporting-camp"
    assert report["total_events"] == 1
    assert report["total_agents"] == 1
