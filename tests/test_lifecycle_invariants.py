import copy
import math
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from models.envelope import CommonEventEnvelope

def calculate_p4_beacon_timeout(beacon_interval_sec: int, jitter_percent: int, safety_margin_sec: int = 5) -> int:
    """Formula: ceil(interval * (1 + jitter / 100) + safety_margin)"""
    jitter_ratio = jitter_percent / 100.0
    return math.ceil(beacon_interval_sec * (1.0 + jitter_ratio) + safety_margin_sec)

def test_p4_simulator_timeout_calculation():
    """Verify simulator calculates expected timeout_sec for different intervals and jitters."""
    # interval=10s, jitter=15%, margin=5s -> 10 * 1.15 + 5 = 16.5 -> 17s
    assert calculate_p4_beacon_timeout(10, 15, 5) == 17
    # interval=30s, jitter=20%, margin=5s -> 30 * 1.20 + 5 = 41.0 -> 41s
    assert calculate_p4_beacon_timeout(30, 20, 5) == 41
    # interval=60s, jitter=0%, margin=5s -> 60 * 1.0 + 5 = 65s
    assert calculate_p4_beacon_timeout(60, 0, 5) == 65

def test_backend_consumes_exact_timeout_without_recalculation():
    """Project 07 must validate and store the exact declared timeout_sec."""
    sim_declared_timeout = 42
    payload = {
        "event_id": str(uuid4()),
        "schema_version": "1.0.0",
        "campaign_id": "test-campaign",
        "run_id": "run-01",
        "ts": "2026-11-24T12:00:00.000Z",
        "source": "p4_c2",
        "type": "agent_registered",
        "status": "running",
        "host": {"host_id": "h-1", "ip": "10.0.0.1", "role": "target"},
        "technique": {"id": "c2-b", "internal_name": "beacon"},
        "correlation": {"entity_id": "agent-1", "entity_type": "agent", "parent_id": None},
        "timeout_sec": sim_declared_timeout,
        "details": {
            "channel": "https",
            "agent_version": "1.0",
            "beacon_interval_sec": 10,
            "jitter_percent": 15,
            "encryption_scheme": "xor",
            "supported_executors": ["simulated_posix"]
        },
        "metadata": {"is_simulated": True, "generator": "p4", "inferred": False}
    }
    model = CommonEventEnvelope.model_validate(payload)
    assert model.timeout_sec == sim_declared_timeout

class MockEntityWatchdogState:
    """Mock state store to verify watchdog rules and referential integrity."""
    def __init__(self, entity_id: str, initial_timeout_sec: int):
        self.entity_id = entity_id
        self.stored_timeout_sec = initial_timeout_sec
        self.status = "running"
        self.latest_event_id = None
        self.campaign_id = "test-camp"
        self.run_id = "run-01"

    def process_event(self, event: CommonEventEnvelope):
        # Immutability check
        if self.status in {"completed", "failed", "timeout"}:
            return "IGNORED_TERMINAL_IMMUTABLE"

        if event.timeout_sec is not None:
            self.stored_timeout_sec = event.timeout_sec

        self.status = event.status
        self.latest_event_id = event.event_id
        return "PROCESSED"

    def validate_grace_period_expired(self, timeout_expired_event: CommonEventEnvelope):
        details = timeout_expired_event.details
        if details.trigger_condition == "grace_period_expired":
            # Invariant: grace_period_sec must equal stored_timeout_sec
            if details.grace_period_sec != self.stored_timeout_sec:
                raise ValueError(
                    f"Referential check failed: grace_period_sec ({details.grace_period_sec}) != stored_timeout_sec ({self.stored_timeout_sec})"
                )
            if details.last_event_id != self.latest_event_id:
                raise ValueError("Referential check failed: last_event_id does not match latest event in state store")
        return True

def test_timeout_updates_and_retention():
    """Verify timeout update and inheritance rules across non-initiation events."""
    state = MockEntityWatchdogState("agent-99", 15)
    assert state.stored_timeout_sec == 15

    # 1. Update timeout via beacon_checkin
    checkin_payload = {
        "event_id": str(uuid4()),
        "schema_version": "1.0.0",
        "campaign_id": "test-camp",
        "run_id": "run-01",
        "ts": "2026-11-24T12:00:10.000Z",
        "source": "p4_c2",
        "type": "beacon_checkin",
        "status": "running",
        "host": {"host_id": "h-1", "ip": "10.0.0.1", "role": "target"},
        "technique": {"id": "c2-b", "internal_name": "beacon"},
        "correlation": {"entity_id": "agent-99", "entity_type": "agent", "parent_id": None},
        "timeout_sec": 25,  # Updated timeout
        "details": {
            "channel": "https",
            "beacon_counter": 2,
            "latency_ms": 30,
            "tasks_pending_count": 0
        },
        "metadata": {"is_simulated": True, "generator": "p4", "inferred": False}
    }
    ev1 = CommonEventEnvelope.model_validate(checkin_payload)
    state.process_event(ev1)
    assert state.stored_timeout_sec == 25  # Updated

    # 2. Inherit previous timeout when omitted/null
    checkin_payload2 = copy.deepcopy(checkin_payload)
    checkin_payload2["event_id"] = str(uuid4())
    checkin_payload2["timeout_sec"] = None  # Omitted
    ev2 = CommonEventEnvelope.model_validate(checkin_payload2)
    state.process_event(ev2)
    assert state.stored_timeout_sec == 25  # Retained previous 25

def test_backend_referential_grace_period_validation():
    """Backend referential checks assert grace_period_sec == stored_timeout_sec."""
    state = MockEntityWatchdogState("agent-42", 30)
    last_id = uuid4()
    state.latest_event_id = last_id

    # Valid timeout_expired event matching state store
    valid_te_payload = {
        "event_id": str(uuid4()),
        "schema_version": "1.0.0",
        "campaign_id": "test-camp",
        "run_id": "run-01",
        "ts": "2026-11-24T12:05:00.000Z",
        "received_at": "2026-11-24T12:05:00.000Z",
        "source": "p7_analytics",
        "type": "timeout_expired",
        "status": "timeout",
        "host": {"host_id": "h-1", "ip": "10.0.0.1", "role": "target"},
        "technique": {"id": "c2-b", "internal_name": "beacon"},
        "correlation": {"entity_id": "agent-42", "entity_type": "agent", "parent_id": None},
        "timeout_sec": None,
        "details": {
            "trigger_condition": "grace_period_expired",
            "last_event_id": str(last_id),
            "total_elapsed_sec": 65.0,
            "grace_period_sec": 30.0,  # Matches stored 30
            "recovery_permitted": False
        },
        "metadata": {"is_simulated": True, "generator": "p7", "inferred": True}
    }
    te_ev = CommonEventEnvelope.model_validate(valid_te_payload)
    assert state.validate_grace_period_expired(te_ev) is True

    # Negative: grace_period_sec mismatch (e.g. 20 instead of 30)
    invalid_te_payload = copy.deepcopy(valid_te_payload)
    invalid_te_payload["event_id"] = str(uuid4())
    invalid_te_payload["details"] = dict(valid_te_payload["details"])
    invalid_te_payload["details"]["grace_period_sec"] = 20.0
    te_mismatch = CommonEventEnvelope.model_validate(invalid_te_payload)
    with pytest.raises(ValueError, match="grace_period_sec"):
        state.validate_grace_period_expired(te_mismatch)

def test_terminal_state_immutability():
    """Late arriving events cannot reopen or update an entity in terminal state."""
    state = MockEntityWatchdogState("task-101", 30)
    state.status = "completed"  # Terminal

    # Late progress event arrives
    late_payload = {
        "event_id": str(uuid4()),
        "schema_version": "1.0.0",
        "campaign_id": "test-camp",
        "run_id": "run-01",
        "ts": "2026-11-24T12:01:00.000Z",
        "source": "p4_c2",
        "type": "task_progress",
        "status": "running",
        "host": {"host_id": "h-1", "ip": "10.0.0.1", "role": "target"},
        "technique": {"id": "c2-t", "internal_name": "task"},
        "correlation": {"entity_id": "task-101", "entity_type": "task", "parent_id": "agent-1"},
        "details": {
            "progress_percent": 90,
            "output_chunk_index": 1,
            "partial_output_len": 100
        },
        "metadata": {"is_simulated": True, "generator": "p4", "inferred": False}
    }
    late_ev = CommonEventEnvelope.model_validate(late_payload)
    res = state.process_event(late_ev)
    assert res == "IGNORED_TERMINAL_IMMUTABLE"
    assert state.status == "completed"  # Still completed, never reverted
