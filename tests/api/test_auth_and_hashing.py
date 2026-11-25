import copy
from datetime import datetime, timezone
import json
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from api.config import EnvironmentEnum, IngestionSettings
from api.dependencies import verify_api_key
from api.hashing import compute_canonical_payload_hash
from models.envelope import CommonEventEnvelope

@pytest.fixture
def base_event(canonical_events):
    raw = copy.deepcopy(canonical_events["agent_registered"])
    raw["received_at"] = datetime.now(timezone.utc)
    return CommonEventEnvelope.model_validate(raw)

# ==============================================================================
# AUTHENTICATION TESTS (6 required scenarios)
# ==============================================================================

def test_missing_api_key_rejected_when_auth_required():
    """1. Missing API key is rejected when authentication is required."""
    cfg = IngestionSettings(
        ENVIRONMENT=EnvironmentEnum.TESTING,
        API_KEY_REQUIRED=True,
        API_KEY="test-secret-key-12345"
    )
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key(header_key=None, app_settings=cfg)
    assert exc_info.value.status_code == 401
    assert "Missing required API key" in exc_info.value.detail

def test_invalid_api_key_rejected():
    """2. Invalid API key is rejected."""
    cfg = IngestionSettings(
        ENVIRONMENT=EnvironmentEnum.TESTING,
        API_KEY_REQUIRED=True,
        API_KEY="test-secret-key-12345"
    )
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key(header_key="wrong-attacker-key", app_settings=cfg)
    assert exc_info.value.status_code == 401
    assert "Invalid API key" in exc_info.value.detail

def test_correct_api_key_accepted():
    """3. Correct API key is accepted."""
    cfg = IngestionSettings(
        ENVIRONMENT=EnvironmentEnum.TESTING,
        API_KEY_REQUIRED=True,
        API_KEY="test-secret-key-12345"
    )
    result = verify_api_key(header_key="test-secret-key-12345", app_settings=cfg)
    assert result == "test-secret-key-12345"

def test_auth_disabled_behavior_in_permitted_configs():
    """4. Authentication-disabled behavior works only in permitted development/testing configurations."""
    cfg_dev = IngestionSettings(
        ENVIRONMENT=EnvironmentEnum.DEVELOPMENT,
        API_KEY_REQUIRED=False
    )
    # When disabled, None or any key passes without raising 401
    assert verify_api_key(header_key=None, app_settings=cfg_dev) is None
    assert verify_api_key(header_key="random", app_settings=cfg_dev) is None

def test_production_configuration_cannot_bypass_auth():
    """5. Production configuration cannot bypass authentication."""
    # Production with API_KEY_REQUIRED=False must be rejected at config initialization
    with pytest.raises(ValidationError):
        IngestionSettings(
            ENVIRONMENT=EnvironmentEnum.PRODUCTION,
            API_KEY_REQUIRED=False,
            API_KEY="super-secret-production-key"
        )

    # Production with default dev key must be rejected at config initialization
    with pytest.raises(ValidationError):
        IngestionSettings(
            ENVIRONMENT=EnvironmentEnum.PRODUCTION,
            API_KEY_REQUIRED=True,
            API_KEY="dev-insecure-test-key"
        )

def test_api_key_never_exposed_in_responses_or_errors():
    """6. API key is never exposed in responses or error messages."""
    secret_key = "super-confidential-secret-key-999"
    cfg = IngestionSettings(
        ENVIRONMENT=EnvironmentEnum.TESTING,
        API_KEY_REQUIRED=True,
        API_KEY=secret_key
    )
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key(header_key="wrong-key", app_settings=cfg)

    # Assert secret string is not in detail message
    assert secret_key not in exc_info.value.detail
    assert secret_key not in str(exc_info.value)

# ==============================================================================
# CANONICAL HASHING TESTS (7 required scenarios)
# ==============================================================================

def test_same_event_produces_same_hash(base_event):
    """1. Same event produces the same hash."""
    h1 = compute_canonical_payload_hash(base_event)
    h2 = compute_canonical_payload_hash(base_event)
    assert h1 == h2

def test_different_received_at_values_produce_same_hash(base_event):
    """2. Different received_at values produce the same hash."""
    ev1 = copy.deepcopy(base_event)
    ev1.received_at = datetime(2026, 11, 24, 12, 0, 0, tzinfo=timezone.utc)

    ev2 = copy.deepcopy(base_event)
    ev2.received_at = datetime(2026, 11, 24, 18, 30, 45, tzinfo=timezone.utc)

    ev3 = copy.deepcopy(base_event)
    ev3.received_at = None

    h1 = compute_canonical_payload_hash(ev1)
    h2 = compute_canonical_payload_hash(ev2)
    h3 = compute_canonical_payload_hash(ev3)

    assert h1 == h2 == h3

def test_different_json_key_ordering_produces_same_hash(canonical_events):
    """3. Different JSON key ordering produces the same hash."""
    raw1 = copy.deepcopy(canonical_events["agent_registered"])
    raw1["received_at"] = None

    # Construct raw2 with reversed / reordered root keys
    keys = list(raw1.keys())
    reversed_keys = list(reversed(keys))
    raw2 = {k: raw1[k] for k in reversed_keys}

    ev1 = CommonEventEnvelope.model_validate(raw1)
    ev2 = CommonEventEnvelope.model_validate(raw2)

    h1 = compute_canonical_payload_hash(ev1)
    h2 = compute_canonical_payload_hash(ev2)
    assert h1 == h2

def test_explicit_null_values_retained_in_canonical_serialization(base_event):
    """4. Explicit null values are retained in canonical serialization."""
    # Ensure fields like bytes_transferred_delta and correlation.parent_id are None
    ev = copy.deepcopy(base_event)
    ev.bytes_transferred_delta = None
    ev.correlation.parent_id = None

    dumped = ev.model_dump(mode="json", exclude={"received_at"})
    assert "bytes_transferred_delta" in dumped
    assert dumped["bytes_transferred_delta"] is None
    assert dumped["correlation"]["parent_id"] is None

    # Serialization with separators=(",", ":") and sort_keys=True
    serialized = json.dumps(dumped, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    assert '"bytes_transferred_delta":null' in serialized
    assert '"parent_id":null' in serialized

def test_meaningful_event_changes_produce_different_hashes(base_event):
    """5. Meaningful event changes produce different hashes."""
    base_hash = compute_canonical_payload_hash(base_event)

    # 1. Change campaign_id
    ev_changed_camp = copy.deepcopy(base_event)
    ev_changed_camp.campaign_id = "altered-campaign-99"
    assert compute_canonical_payload_hash(ev_changed_camp) != base_hash

    # 2. Change timeout_sec
    ev_changed_timeout = copy.deepcopy(base_event)
    ev_changed_timeout.timeout_sec = base_event.timeout_sec + 10
    assert compute_canonical_payload_hash(ev_changed_timeout) != base_hash

    # 3. Change details
    ev_changed_details = copy.deepcopy(base_event)
    ev_changed_details.details.jitter_percent = 50
    assert compute_canonical_payload_hash(ev_changed_details) != base_hash

def test_hashing_does_not_mutate_original_event(base_event):
    """6. Hashing does not mutate the original event."""
    # Snapshot original model dump
    original_dump = base_event.model_dump()

    _ = compute_canonical_payload_hash(base_event)

    # Assert exact equality after hashing
    assert base_event.model_dump() == original_dump

def test_hash_output_is_valid_sha256_hex_digest(base_event):
    """7. Hash output is a valid SHA-256 hexadecimal digest."""
    h = compute_canonical_payload_hash(base_event)
    assert isinstance(h, str)
    assert len(h) == 64
    # All characters must be lowercase hex digits
    assert all(c in "0123456789abcdef" for c in h)
