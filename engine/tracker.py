"""
Entity correlation and lifecycle tracking for Project 07 Red Analytics.
Tracks Agents, Tasks, Sessions, and Transfers per campaign_id and run_id.
Enforces terminal state immutability, parent-child links, and recovery from stalled states.
"""

from dataclasses import dataclass, field
from datetime import datetime
import threading
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from models.enums import EntityTypeEnum, StatusEnum
from models.envelope import CommonEventEnvelope

TERMINAL_STATUSES = {
    StatusEnum.COMPLETED.value,
    StatusEnum.FAILED.value,
    StatusEnum.TIMEOUT.value,
}


@dataclass
class AlertRecord:
    """Operational alert record tracking stall, recovery, and timeout incidents."""
    alert_id: str
    alert_type: str
    severity: str  # "warning" | "critical" | "info"
    campaign_id: str
    run_id: str
    entity_id: str
    entity_type: str
    event_id: str
    first_detected_at: datetime
    last_updated_at: datetime
    current_status: str  # "active" | "resolved" | "timed_out"
    is_recovered: bool = False
    recovered_at: Optional[datetime] = None
    is_timeout: bool = False
    timeout_at: Optional[datetime] = None
    message: str = ""


@dataclass
class EntityState:
    """Current consolidated lifecycle state of a tracked entity."""
    entity_id: str
    entity_type: str
    parent_id: Optional[str]
    campaign_id: str
    run_id: str
    current_status: str
    is_terminal: bool
    is_stalled: bool
    is_established: bool  # Specific to sessions (connection_established received)
    timeout_sec: Optional[float]
    first_seen_ts: datetime
    last_seen_ts: datetime
    last_received_at: datetime
    last_event_id: UUID
    stalled_event_id: Optional[UUID] = None  # Reference to stalled event for grace period integrity
    stalled_at: Optional[datetime] = None
    bytes_transferred_total: int = 0
    history_event_ids: List[UUID] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LifecycleTracker:
    """
    Thread-safe tracker maintaining current state and historical event links
    for entities across campaigns and runs.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # Key: (campaign_id, run_id, entity_id) -> EntityState
        self._entities: Dict[Tuple[str, str, str], EntityState] = {}
        # Entity hierarchy: (campaign_id, run_id, parent_id) -> List[child_entity_id]
        self._children: Dict[Tuple[str, str, str], List[str]] = {}
        # Operational alerts list
        self._alerts: List[AlertRecord] = []

    def process_event(self, event: CommonEventEnvelope) -> EntityState:
        """
        Processes an incoming canonical event, updating or creating the entity's lifecycle state.
        Enforces terminal immutability, timeout inheritance, and stalled recovery.
        """
        with self._lock:
            key = (event.campaign_id, event.run_id, event.correlation.entity_id)
            entity_type = (
                event.correlation.entity_type.value
                if hasattr(event.correlation.entity_type, "value")
                else str(event.correlation.entity_type)
            )
            event_status = (
                event.status.value
                if hasattr(event.status, "value")
                else str(event.status)
            )
            event_recv_at = event.received_at or event.ts
            parent_id = event.correlation.parent_id

            if key not in self._entities:
                # First time seeing this entity (Initiation)
                is_terminal = event_status in TERMINAL_STATUSES
                is_stalled = event_status == StatusEnum.STALLED.value
                is_established = event.type == "connection_established"
                timeout_val = float(event.timeout_sec) if event.timeout_sec is not None else None

                bytes_delta = event.bytes_transferred_delta or 0

                state = EntityState(
                    entity_id=event.correlation.entity_id,
                    entity_type=entity_type,
                    parent_id=parent_id,
                    campaign_id=event.campaign_id,
                    run_id=event.run_id,
                    current_status=event_status,
                    is_terminal=is_terminal,
                    is_stalled=is_stalled,
                    is_established=is_established,
                    timeout_sec=timeout_val,
                    first_seen_ts=event.ts,
                    last_seen_ts=event.ts,
                    last_received_at=event_recv_at,
                    last_event_id=event.event_id,
                    stalled_event_id=event.event_id if is_stalled else None,
                    stalled_at=event_recv_at if is_stalled else None,
                    bytes_transferred_total=bytes_delta,
                    history_event_ids=[event.event_id],
                )
                self._entities[key] = state

                # Track parent-child relationship
                if parent_id:
                    parent_key = (event.campaign_id, event.run_id, parent_id)
                    self._children.setdefault(parent_key, []).append(event.correlation.entity_id)

                if is_stalled:
                    self._record_alert(
                        event=event,
                        entity_type=entity_type,
                        severity="warning",
                        status="active",
                        message=f"Entity {entity_type} {event.correlation.entity_id} stalled ({event.type}).",
                    )
                elif event_status == StatusEnum.TIMEOUT.value or event.type == "timeout_expired":
                    self._record_alert(
                        event=event,
                        entity_type=entity_type,
                        severity="critical",
                        status="timed_out",
                        is_timeout=True,
                        message=f"Entity {entity_type} {event.correlation.entity_id} timed out ({event.type}).",
                    )

                return state

            # Existing entity update
            state = self._entities[key]
            state.history_event_ids.append(event.event_id)

            if event.bytes_transferred_delta:
                state.bytes_transferred_total += event.bytes_transferred_delta

            if event.type == "connection_established":
                state.is_established = True

            # Terminal state immutability:
            # If entity is already terminal, retain history but do not mutate status or re-arm watchdog
            if state.is_terminal:
                # Update last seen timestamp only if event is newer
                if event.ts > state.last_seen_ts:
                    state.last_seen_ts = event.ts
                return state

            # Check if this event makes entity terminal
            if event_status in TERMINAL_STATUSES:
                state.is_terminal = True
                state.current_status = event_status
                state.timeout_sec = None  # Deactivate watchdog
                state.is_stalled = False
                state.stalled_event_id = None
                state.stalled_at = None
                state.last_event_id = event.event_id
                state.last_received_at = event_recv_at
                state.last_seen_ts = max(state.last_seen_ts, event.ts)

                if event_status == StatusEnum.TIMEOUT.value or event.type == "timeout_expired":
                    self._handle_timeout_alert(event, entity_type)
                return state

            # Stalled handling and recovery
            if event_status == StatusEnum.STALLED.value:
                state.is_stalled = True
                state.current_status = event_status
                state.stalled_event_id = event.event_id
                state.stalled_at = event_recv_at
                state.last_event_id = event.event_id
                state.last_received_at = event_recv_at
                state.last_seen_ts = max(state.last_seen_ts, event.ts)

                self._record_alert(
                    event=event,
                    entity_type=entity_type,
                    severity="warning",
                    status="active",
                    message=f"Entity {entity_type} {event.correlation.entity_id} stalled ({event.type}).",
                )
                return state

            # If entity was previously stalled and receives a non-stalled event (e.g. running progress),
            # it recovers!
            if state.is_stalled and event_status in (StatusEnum.RUNNING.value, StatusEnum.PENDING.value):
                state.is_stalled = False
                state.stalled_event_id = None
                state.stalled_at = None
                self._handle_recovery_alert(event, entity_type)

            state.current_status = event_status
            state.last_event_id = event.event_id
            state.last_received_at = event_recv_at
            if event.ts > state.last_seen_ts:
                state.last_seen_ts = event.ts

            # Timeout inheritance rule:
            # Non-initiation progress events update timeout only when source provides a new valid timeout
            if event.source != "p7_analytics":
                if event.timeout_sec is not None and event.timeout_sec > 0:
                    state.timeout_sec = float(event.timeout_sec)
                # If event.timeout_sec is None, inherit existing configured timeout (state.timeout_sec untouched)

            return state

    def _record_alert(
        self,
        event: CommonEventEnvelope,
        entity_type: str,
        severity: str,
        status: str,
        message: str,
        is_timeout: bool = False,
    ) -> None:
        """Records a new alert if not already active for the entity."""
        # Check if active alert already exists
        for a in self._alerts:
            if (
                a.campaign_id == event.campaign_id
                and a.run_id == event.run_id
                and a.entity_id == event.correlation.entity_id
                and a.current_status == "active"
            ):
                return

        alert = AlertRecord(
            alert_id=str(uuid4()),
            alert_type=event.type,
            severity=severity,
            campaign_id=event.campaign_id,
            run_id=event.run_id,
            entity_id=event.correlation.entity_id,
            entity_type=entity_type,
            event_id=str(event.event_id),
            first_detected_at=event.ts,
            last_updated_at=event.ts,
            current_status=status,
            is_recovered=False,
            recovered_at=None,
            is_timeout=is_timeout,
            timeout_at=event.ts if is_timeout else None,
            message=message,
        )
        self._alerts.append(alert)

    def _handle_recovery_alert(self, event: CommonEventEnvelope, entity_type: str) -> None:
        """Marks any active alert for this entity as resolved."""
        for a in self._alerts:
            if (
                a.campaign_id == event.campaign_id
                and a.run_id == event.run_id
                and a.entity_id == event.correlation.entity_id
                and a.current_status == "active"
            ):
                a.current_status = "resolved"
                a.is_recovered = True
                a.recovered_at = event.ts
                a.last_updated_at = event.ts
                a.message = f"Entity {entity_type} {event.correlation.entity_id} recovered from stall."

    def _handle_timeout_alert(self, event: CommonEventEnvelope, entity_type: str) -> None:
        """Transitions active alert to timed_out or creates a new critical alert."""
        for a in self._alerts:
            if (
                a.campaign_id == event.campaign_id
                and a.run_id == event.run_id
                and a.entity_id == event.correlation.entity_id
                and a.current_status == "active"
            ):
                a.current_status = "timed_out"
                a.severity = "critical"
                a.is_timeout = True
                a.timeout_at = event.ts
                a.last_updated_at = event.ts
                a.message = f"Entity {entity_type} {event.correlation.entity_id} timed out ({event.type})."
                return

        # Direct timeout (e.g. handshake timeout)
        self._record_alert(
            event=event,
            entity_type=entity_type,
            severity="critical",
            status="timed_out",
            message=f"Entity {entity_type} {event.correlation.entity_id} timed out ({event.type}).",
            is_timeout=True,
        )

    def get_alerts(
        self,
        campaign_id: Optional[str] = None,
        run_id: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[AlertRecord]:
        with self._lock:
            return [
                a
                for a in self._alerts
                if (campaign_id is None or a.campaign_id == campaign_id)
                and (run_id is None or a.run_id == run_id)
                and (severity is None or a.severity == severity)
            ]

    def get_entity(self, campaign_id: str, run_id: str, entity_id: str) -> Optional[EntityState]:
        with self._lock:
            return self._entities.get((campaign_id, run_id, entity_id))

    def get_entities_for_run(self, campaign_id: str, run_id: str) -> List[EntityState]:
        with self._lock:
            return [
                state
                for (c_id, r_id, _), state in self._entities.items()
                if c_id == campaign_id and r_id == run_id
            ]

    def get_all_entities(self, campaign_id: Optional[str] = None, run_id: Optional[str] = None) -> List[EntityState]:
        with self._lock:
            return [
                state
                for (c_id, r_id, _), state in self._entities.items()
                if (campaign_id is None or c_id == campaign_id)
                and (run_id is None or r_id == run_id)
            ]

    def get_children(self, campaign_id: str, run_id: str, parent_id: str) -> List[str]:
        with self._lock:
            return list(self._children.get((campaign_id, run_id, parent_id), []))

    def clear(self) -> None:
        """Reset state (for test isolation)."""
        with self._lock:
            self._entities.clear()
            self._children.clear()
            self._alerts.clear()
