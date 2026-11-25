"""
Unit tests for Watchdog and Lifecycle Correlation Engine (Zero-sleep, deterministic VirtualClock).
"""

import copy
from datetime import datetime, timezone
from uuid import uuid4
import pytest

from api.hashing import compute_canonical_payload_hash
from api.storage.memory import ThreadSafeInMemoryEventRepository
from engine.clock import VirtualClock
from engine.tracker import LifecycleTracker
from engine.watchdog import WatchdogEngine
from models.envelope import CommonEventEnvelope


@pytest.fixture
def repo():
    return ThreadSafeInMemoryEventRepository()


@pytest.fixture
def tracker():
    return LifecycleTracker()


@pytest.fixture
def vclock():
    return VirtualClock(initial_time=datetime(2026, 11, 24, 12, 0, 0, tzinfo=timezone.utc))


@pytest.fixture
def engine(repo, tracker, vclock):
    return WatchdogEngine(repository=repo, tracker=tracker, clock=vclock)


def save_and_track(repo, tracker, event_dict, vclock):
    raw = copy.deepcopy(event_dict)
    raw["received_at"] = vclock.now().isoformat()
    ev = CommonEventEnvelope.model_validate(raw)
    h = compute_canonical_payload_hash(ev)
    repo.save_if_absent(ev, h)
    tracker.process_event(ev)
    return ev


# ==============================================================================
# WATCHDOG TIMEOUT AND GRACE PERIOD TESTS
# ==============================================================================

def test_agent_heartbeat_stall_and_grace_expiration(repo, tracker, engine, vclock, canonical_events):
    """1. Agent stalls after timeout_sec, then expires after grace_period."""
    raw = copy.deepcopy(canonical_events["agent_registered"])
    raw["event_id"] = str(uuid4())
    raw["timeout_sec"] = 10
    agent_ev = save_and_track(repo, tracker, raw, vclock)

    # At t=0, no watchdog events
    assert engine.check_watchdogs() == []

    # Advance to t=5 (below 10s threshold) -> no stall
    vclock.advance(5)
    assert engine.check_watchdogs() == []

    # Advance to t=11 (past 10s threshold) -> emits beacon_missed
    vclock.advance(6)
    stalled_events = engine.check_watchdogs()
    assert len(stalled_events) == 1
    stall_ev = stalled_events[0]
    assert stall_ev.type == "beacon_missed"
    assert stall_ev.status == "stalled"
    assert stall_ev.source == "p7_analytics"
    assert stall_ev.details.last_event_id == agent_ev.event_id
    assert stall_ev.details.threshold_sec == 10.0

    # Entity is now stalled in tracker
    entity = tracker.get_entity(raw["campaign_id"], raw["run_id"], raw["correlation"]["entity_id"])
    assert entity.is_stalled is True
    assert entity.stalled_event_id == stall_ev.event_id

    # Advance another 5s (total elapsed 16s, grace period elapsed 5s < 10s) -> no timeout yet
    vclock.advance(5)
    assert engine.check_watchdogs() == []

    # Advance another 6s (total grace elapsed 11s >= 10s) -> emits timeout_expired
    vclock.advance(6)
    timeout_events = engine.check_watchdogs()
    assert len(timeout_events) == 1
    te_ev = timeout_events[0]
    assert te_ev.type == "timeout_expired"
    assert te_ev.status == "timeout"
    assert te_ev.details.trigger_condition == "grace_period_expired"
    # REFERENTIAL INTEGRITY: last_event_id must reference the exact stalled event!
    assert te_ev.details.last_event_id == stall_ev.event_id
    assert te_ev.details.grace_period_sec == 10.0

    # Entity is now terminal timeout
    entity_updated = tracker.get_entity(raw["campaign_id"], raw["run_id"], raw["correlation"]["entity_id"])
    assert entity_updated.is_terminal is True
    assert entity_updated.current_status == "timeout"


def test_agent_recovery_from_stalled_state(repo, tracker, engine, vclock, canonical_events):
    """2. Agent recovers from stalled state when check-in arrives before grace period expires."""
    raw = copy.deepcopy(canonical_events["agent_registered"])
    raw["event_id"] = str(uuid4())
    raw["timeout_sec"] = 10
    save_and_track(repo, tracker, raw, vclock)

    # Advance past 10s -> beacon_missed emitted
    vclock.advance(11)
    stalled_events = engine.check_watchdogs()
    assert len(stalled_events) == 1
    assert stalled_events[0].type == "beacon_missed"

    entity = tracker.get_entity(raw["campaign_id"], raw["run_id"], raw["correlation"]["entity_id"])
    assert entity.is_stalled is True

    # Checkin arrives before grace period expires!
    checkin_raw = copy.deepcopy(canonical_events["beacon_checkin"])
    checkin_raw["event_id"] = str(uuid4())
    checkin_raw["correlation"]["entity_id"] = raw["correlation"]["entity_id"]
    save_and_track(repo, tracker, checkin_raw, vclock)

    # Entity is recovered
    entity_after = tracker.get_entity(raw["campaign_id"], raw["run_id"], raw["correlation"]["entity_id"])
    assert entity_after.is_stalled is False
    assert entity_after.current_status == "running"

    # Advance time within the new checkin window:
    # Former grace deadline (which was at t=21) does not trigger timeout because entity recovered
    vclock.advance(6)
    assert engine.check_watchdogs() == []

    # Verify that entity is still running
    assert tracker.get_entity(raw["campaign_id"], raw["run_id"], raw["correlation"]["entity_id"]).current_status == "running"


def test_session_handshake_timeout_directly_expires(repo, tracker, engine, vclock, canonical_events):
    """3. Unestablished session connection directly produces timeout_expired without session_stalled."""
    raw = copy.deepcopy(canonical_events["connection_requested"])
    raw["event_id"] = str(uuid4())
    raw["timeout_sec"] = 8  # Handshake timeout
    req_ev = save_and_track(repo, tracker, raw, vclock)

    # Advance past 8s without connection_established
    vclock.advance(9)
    events = engine.check_watchdogs()
    assert len(events) == 1
    te_ev = events[0]
    assert te_ev.type == "timeout_expired"
    assert te_ev.status == "timeout"
    assert te_ev.details.trigger_condition == "handshake_timeout"
    assert te_ev.details.grace_period_sec == 0.0
    assert te_ev.details.last_event_id == req_ev.event_id


def test_established_session_idle_timeout(repo, tracker, engine, vclock, canonical_events):
    """4. Established session emits session_stalled when idle."""
    req_raw = copy.deepcopy(canonical_events["connection_requested"])
    req_raw["event_id"] = str(uuid4())
    session_id = req_raw["correlation"]["entity_id"]
    save_and_track(repo, tracker, req_raw, vclock)

    # Establish session
    est_raw = copy.deepcopy(canonical_events["connection_established"])
    est_raw["event_id"] = str(uuid4())
    est_raw["correlation"]["entity_id"] = session_id
    est_raw["timeout_sec"] = 12
    save_and_track(repo, tracker, est_raw, vclock)

    # Advance past 12s -> session_stalled
    vclock.advance(13)
    stalled = engine.check_watchdogs()
    assert len(stalled) == 1
    assert stalled[0].type == "session_stalled"
    assert stalled[0].details.trigger_condition == "session_idle_timeout"


def test_task_stalled_and_timeout(repo, tracker, engine, vclock, canonical_events):
    """5. Task progress stall generates task_stalled and then timeout_expired."""
    task_raw = copy.deepcopy(canonical_events["task_started"])
    task_raw["event_id"] = str(uuid4())
    task_raw["timeout_sec"] = 15
    save_and_track(repo, tracker, task_raw, vclock)

    vclock.advance(16)
    stalled = engine.check_watchdogs()
    assert len(stalled) == 1
    assert stalled[0].type == "task_stalled"
    assert stalled[0].details.trigger_condition == "task_progress_timeout"


def test_transfer_stalled_and_timeout(repo, tracker, engine, vclock, canonical_events):
    """6. Transfer chunk stall generates transfer_stalled and then timeout_expired."""
    xfer_raw = copy.deepcopy(canonical_events["transfer_started"])
    xfer_raw["event_id"] = str(uuid4())
    xfer_raw["timeout_sec"] = 10
    save_and_track(repo, tracker, xfer_raw, vclock)

    vclock.advance(11)
    stalled = engine.check_watchdogs()
    assert len(stalled) == 1
    assert stalled[0].type == "transfer_stalled"
    assert stalled[0].details.trigger_condition == "transfer_chunk_timeout"


def test_terminal_state_immutability_in_tracker(repo, tracker, vclock, canonical_events):
    """7. Terminal states cannot be rolled back by late events."""
    raw_start = copy.deepcopy(canonical_events["task_started"])
    raw_start["event_id"] = str(uuid4())
    task_id = raw_start["correlation"]["entity_id"]
    save_and_track(repo, tracker, raw_start, vclock)

    # Complete task
    raw_comp = copy.deepcopy(canonical_events["task_completed"])
    raw_comp["event_id"] = str(uuid4())
    raw_comp["correlation"]["entity_id"] = task_id
    save_and_track(repo, tracker, raw_comp, vclock)

    entity = tracker.get_entity(raw_start["campaign_id"], raw_start["run_id"], task_id)
    assert entity.is_terminal is True
    assert entity.current_status == "completed"

    # Late progress event arrives
    raw_late = copy.deepcopy(canonical_events["task_progress"])
    raw_late["event_id"] = str(uuid4())
    raw_late["correlation"]["entity_id"] = task_id
    save_and_track(repo, tracker, raw_late, vclock)

    entity_after = tracker.get_entity(raw_start["campaign_id"], raw_start["run_id"], task_id)
    assert entity_after.is_terminal is True
    assert entity_after.current_status == "completed"
    assert len(entity_after.history_event_ids) == 3


def test_parent_child_correlation(repo, tracker, vclock, canonical_events):
    """8. Parent-child relationships are accurately recorded."""
    agent_raw = copy.deepcopy(canonical_events["agent_registered"])
    agent_raw["event_id"] = str(uuid4())
    agent_id = "agent-parent-01"
    agent_raw["correlation"]["entity_id"] = agent_id
    save_and_track(repo, tracker, agent_raw, vclock)

    task_raw = copy.deepcopy(canonical_events["task_started"])
    task_raw["event_id"] = str(uuid4())
    task_id = "task-child-01"
    task_raw["correlation"]["entity_id"] = task_id
    task_raw["correlation"]["parent_id"] = agent_id
    save_and_track(repo, tracker, task_raw, vclock)

    children = tracker.get_children(agent_raw["campaign_id"], agent_raw["run_id"], agent_id)
    assert task_id in children


def test_task_recovery_from_stalled_state(repo, tracker, engine, vclock, canonical_events):
    """9. Task recovers from stalled state when task_progress arrives before grace expires."""
    task_raw = copy.deepcopy(canonical_events["task_started"])
    task_raw["event_id"] = str(uuid4())
    task_raw["timeout_sec"] = 10
    task_id = task_raw["correlation"]["entity_id"]
    save_and_track(repo, tracker, task_raw, vclock)

    vclock.advance(11)
    stalled = engine.check_watchdogs()
    assert len(stalled) == 1
    assert stalled[0].type == "task_stalled"
    assert tracker.get_entity(task_raw["campaign_id"], task_raw["run_id"], task_id).is_stalled is True

    # Progress arrives
    prog_raw = copy.deepcopy(canonical_events["task_progress"])
    prog_raw["event_id"] = str(uuid4())
    prog_raw["correlation"]["entity_id"] = task_id
    save_and_track(repo, tracker, prog_raw, vclock)

    entity = tracker.get_entity(task_raw["campaign_id"], task_raw["run_id"], task_id)
    assert entity.is_stalled is False
    assert entity.current_status == "running"


def test_session_recovery_from_stalled_state(repo, tracker, engine, vclock, canonical_events):
    """10. Established session recovers from stalled state when session_activity arrives."""
    est_raw = copy.deepcopy(canonical_events["connection_established"])
    est_raw["event_id"] = str(uuid4())
    est_raw["timeout_sec"] = 10
    session_id = est_raw["correlation"]["entity_id"]
    save_and_track(repo, tracker, est_raw, vclock)

    vclock.advance(11)
    stalled = engine.check_watchdogs()
    assert len(stalled) == 1
    assert stalled[0].type == "session_stalled"
    assert tracker.get_entity(est_raw["campaign_id"], est_raw["run_id"], session_id).is_stalled is True

    # Activity arrives
    act_raw = copy.deepcopy(canonical_events["session_activity"])
    act_raw["event_id"] = str(uuid4())
    act_raw["correlation"]["entity_id"] = session_id
    save_and_track(repo, tracker, act_raw, vclock)

    entity = tracker.get_entity(est_raw["campaign_id"], est_raw["run_id"], session_id)
    assert entity.is_stalled is False
    assert entity.current_status == "running"


def test_transfer_recovery_from_stalled_state(repo, tracker, engine, vclock, canonical_events):
    """11. Transfer recovers from stalled state when transfer_progress arrives."""
    xfer_raw = copy.deepcopy(canonical_events["transfer_started"])
    xfer_raw["event_id"] = str(uuid4())
    xfer_raw["timeout_sec"] = 10
    xfer_id = xfer_raw["correlation"]["entity_id"]
    save_and_track(repo, tracker, xfer_raw, vclock)

    vclock.advance(11)
    stalled = engine.check_watchdogs()
    assert len(stalled) == 1
    assert stalled[0].type == "transfer_stalled"
    assert tracker.get_entity(xfer_raw["campaign_id"], xfer_raw["run_id"], xfer_id).is_stalled is True

    # Progress arrives
    prog_raw = copy.deepcopy(canonical_events["transfer_progress"])
    prog_raw["event_id"] = str(uuid4())
    prog_raw["correlation"]["entity_id"] = xfer_id
    save_and_track(repo, tracker, prog_raw, vclock)

    entity = tracker.get_entity(xfer_raw["campaign_id"], xfer_raw["run_id"], xfer_id)
    assert entity.is_stalled is False
    assert entity.current_status == "running"


def test_all_terminal_events_prevent_watchdog_evaluation(repo, tracker, engine, vclock, canonical_events):
    """12. Terminal events close watchdogs and prevent timeouts."""
    terminal_types = [
        ("task_started", "task_failed", "task"),
        ("connection_requested", "connection_failed", "session"),
        ("connection_established", "session_closed", "session"),
        ("transfer_started", "transfer_completed", "transfer"),
        ("transfer_started", "transfer_failed", "transfer"),
    ]

    for init_type, term_type, ent_type in terminal_types:
        init_raw = copy.deepcopy(canonical_events[init_type])
        init_raw["event_id"] = str(uuid4())
        init_raw["timeout_sec"] = 5
        entity_id = f"ent-{uuid4().hex[:6]}"
        init_raw["correlation"]["entity_id"] = entity_id
        save_and_track(repo, tracker, init_raw, vclock)

        term_raw = copy.deepcopy(canonical_events[term_type])
        term_raw["event_id"] = str(uuid4())
        term_raw["correlation"]["entity_id"] = entity_id
        save_and_track(repo, tracker, term_raw, vclock)

        # Advance well past timeout
        vclock.advance(20)
        # Terminal entity must not generate watchdog events
        assert engine.check_watchdogs() == []
        entity = tracker.get_entity(init_raw["campaign_id"], init_raw["run_id"], entity_id)
        assert entity.is_terminal is True
