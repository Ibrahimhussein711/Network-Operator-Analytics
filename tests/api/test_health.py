"""
Unit tests for Health & Readiness endpoints (Phase 4.1 - Step 5).

Verifies:
1. GET /api/v1/health/live returns HTTP 200 and LivenessResponse.
2. Liveness succeeds even when storage/repository is unhealthy.
3. Liveness does not touch or invoke the repository.
4. GET /api/v1/health/ready returns HTTP 200 and ReadinessResponse when healthy.
5. GET /api/v1/health/ready returns HTTP 503 and ReadinessResponse when unhealthy.
6. Readiness accurately reflects repository event count.
7. Readiness uses FastAPI dependency injection (get_event_repository).
8. Health endpoints do not require API key authentication even when auth is globally configured.
9. Health responses do not expose sensitive credentials or extra fields.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.config import EnvironmentEnum, IngestionSettings
from api.dependencies import get_event_repository, reset_event_repository
from api.responses import LivenessResponse, ReadinessResponse
from api.storage.interface import IEventRepository
from api.storage.memory import ThreadSafeInMemoryEventRepository


@pytest.fixture(autouse=True)
def clean_repository():
    """Ensure a clean repository singleton before and after each test."""
    reset_event_repository()
    yield
    reset_event_repository()


@pytest.fixture
def client():
    """Default test client with default test settings."""
    app = create_app()
    return TestClient(app)


# ==============================================================================
# LIVENESS ENDPOINT TESTS
# ==============================================================================

def test_liveness_returns_200_and_valid_model(client):
    """1. Liveness probe returns HTTP 200 and conforms to LivenessResponse."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200

    data = response.json()
    model = LivenessResponse.model_validate(data)
    assert model.status == "live"
    assert isinstance(model.timestamp, datetime)
    assert (datetime.now(timezone.utc) - model.timestamp).total_seconds() < 10


def test_liveness_independent_of_repository_health(client):
    """2. Liveness succeeds even if the underlying repository is unhealthy."""
    repo = get_event_repository()
    assert isinstance(repo, ThreadSafeInMemoryEventRepository)
    repo.set_healthy(False)

    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "live"


def test_liveness_does_not_invoke_repository():
    """3. Liveness does not touch or depend on the repository."""
    mock_repo = MagicMock(spec=IEventRepository)
    app = create_app()
    app.dependency_overrides[get_event_repository] = lambda: mock_repo

    test_client = TestClient(app)
    response = test_client.get("/api/v1/health/live")

    assert response.status_code == 200
    mock_repo.is_healthy.assert_not_called()
    mock_repo.count.assert_not_called()
    mock_repo.get_by_id.assert_not_called()
    mock_repo.save_if_absent.assert_not_called()


# ==============================================================================
# READINESS ENDPOINT TESTS
# ==============================================================================

def test_readiness_returns_200_when_healthy(client):
    """4. Readiness returns HTTP 200 and complete storage metadata when healthy."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200

    data = response.json()
    model = ReadinessResponse.model_validate(data)
    assert model.status == "ready"
    assert model.storage.type == "in_memory"
    assert model.storage.connected is True
    assert model.storage.event_count == 0
    assert isinstance(model.timestamp, datetime)


def test_readiness_returns_503_when_unhealthy(client):
    """5. Readiness returns HTTP 503 and connected=False when repository is unhealthy."""
    repo = get_event_repository()
    assert isinstance(repo, ThreadSafeInMemoryEventRepository)
    repo.set_healthy(False)

    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503

    data = response.json()
    model = ReadinessResponse.model_validate(data)
    assert model.status == "unhealthy"
    assert model.storage.type == "in_memory"
    assert model.storage.connected is False
    assert model.storage.event_count == 0


def test_readiness_reflects_event_count(client):
    """6. Readiness accurately reports stored event count."""
    repo = get_event_repository()
    mock_event = MagicMock()
    mock_event.event_id = "00000000-0000-0000-0000-000000000001"

    # Insert dummy event into repository directly
    repo.save_if_absent(mock_event, "hash-1")
    assert repo.count() == 1

    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["storage"]["event_count"] == 1


def test_readiness_uses_dependency_injection():
    """7. Readiness resolves repository through FastAPI dependency injection."""
    mock_repo = MagicMock(spec=IEventRepository)
    mock_repo.is_healthy.return_value = True
    mock_repo.count.return_value = 42

    app = create_app()
    app.dependency_overrides[get_event_repository] = lambda: mock_repo

    test_client = TestClient(app)
    response = test_client.get("/api/v1/health/ready")

    assert response.status_code == 200
    mock_repo.is_healthy.assert_called_once()
    mock_repo.count.assert_called_once()
    data = response.json()
    assert data["status"] == "ready"
    assert data["storage"]["event_count"] == 42


# ==============================================================================
# SECURITY AND CONTRACT TESTS
# ==============================================================================

def test_health_endpoints_do_not_require_auth_when_auth_configured():
    """8. Health endpoints are accessible without X-API-Key even when auth is required."""
    secured_settings = IngestionSettings(
        ENVIRONMENT=EnvironmentEnum.TESTING,
        API_KEY_REQUIRED=True,
        API_KEY="super-secret-testing-key-12345",
    )
    app = create_app(app_settings=secured_settings)
    test_client = TestClient(app)

    # Neither endpoint should require X-API-Key header
    live_resp = test_client.get("/api/v1/health/live")
    assert live_resp.status_code == 200

    ready_resp = test_client.get("/api/v1/health/ready")
    assert ready_resp.status_code == 200


def test_health_responses_do_not_leak_secrets(client):
    """9. Health responses contain only designated fields and no credentials."""
    for path in ["/api/v1/health/live", "/api/v1/health/ready"]:
        resp = client.get(path)
        content_str = resp.text.lower()
        assert "api_key" not in content_str
        assert "secret" not in content_str
        assert "password" not in content_str
        assert "token" not in content_str
