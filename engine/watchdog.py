"""
Watchdog and Timeout Engine for Project 07 Red Analytics.
Monitors entities for heartbeat, progress, idle, and chunk stalls,
and generates canonical P7 analytics events upon timeout expiration.
"""

from datetime import datetime, timezone
import threading
from typing import List, Optional
from uuid import uuid4

from api.hashing import compute_canonical_payload_hash
from api.storage.interface import IEventRepository
from engine.clock import IClock, SystemClock
from engine.tracker import LifecycleTracker, EntityState
from models.details.p7_analytics import (
    P7BeaconMissedDetails,
    P7SessionStalledDetails,
    P7TaskStalledDetails,
    P7TimeoutExpiredDetails,
    P7TransferStalledDetails,
)
from models.enums import P7StalledTriggerEnum, P7TimeoutTriggerEnum, StatusEnum
from models.envelope import CommonEventEnvelope


class WatchdogEngine:
    """
    Watches active entities and evaluates timeout/grace deadlines.
    Emits canonical P7 events into storage and updates lifecycle state.
    """

    def __init__(
        self,
        repository: IEventRepository,
        tracker: LifecycleTracker,
        clock: Optional[IClock] = None,
    ):
        self._repo = repository
        self._tracker = tracker
        self._clock = clock or SystemClock()
        self._lock = threading.Lock()

    @property
    def clock(self) -> IClock:
        return self._clock

    def check_watchdogs(
        self,
        campaign_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> List[CommonEventEnvelope]:
        """
        Evaluates registered entities against the current clock time with optional scoping.
        Generates and persists P7 events for newly stalled or timed-out entities.
        Returns a list of all newly generated P7 event envelopes.
        """
        with self._lock:
            now = self._clock.now()
            generated_events: List[CommonEventEnvelope] = []

            entities = self._tracker.get_all_entities(campaign_id=campaign_id, run_id=run_id)
            for entity in entities:
                if entity.is_terminal:
                    continue

                if entity.timeout_sec is None or entity.timeout_sec <= 0:
                    continue

                elapsed = (now - entity.last_received_at).total_seconds()
                t_stall = entity.timeout_sec
                grace_period = entity.timeout_sec

                # -------------------------------------------------------------
                # Case 1: Session in connection_requested that never established
                # -------------------------------------------------------------
                if entity.entity_type == "session" and not entity.is_established:
                    if elapsed >= t_stall:
                        # Handshake timeout directly produces timeout_expired
                        details = P7TimeoutExpiredDetails(
                            trigger_condition=P7TimeoutTriggerEnum.HANDSHAKE_TIMEOUT,
                            last_event_id=entity.last_event_id,
                            total_elapsed_sec=round(max(elapsed, 0.001), 3),
                            grace_period_sec=0.0,
                            recovery_permitted=False,
                        )
                        event = self._create_p7_envelope(
                            entity=entity,
                            event_type="timeout_expired",
                            status="timeout",
                            details=details,
                            ts=now,
                        )
                        self._persist_and_apply(event)
                        generated_events.append(event)
                    continue

                # -------------------------------------------------------------
                # Case 2: Entity is already stalled -> Check Grace Period
                # -------------------------------------------------------------
                if entity.is_stalled:
                    stalled_time = entity.stalled_at or entity.last_received_at
                    grace_elapsed = (now - stalled_time).total_seconds()

                    if grace_elapsed >= grace_period:
                        # Grace period expired -> generate timeout_expired
                        # Invariant: last_event_id must reference the exact stalled event that initiated countdown
                        stalled_ref_id = entity.stalled_event_id or entity.last_event_id
                        details = P7TimeoutExpiredDetails(
                            trigger_condition=P7TimeoutTriggerEnum.GRACE_PERIOD_EXPIRED,
                            last_event_id=stalled_ref_id,
                            total_elapsed_sec=round(max(elapsed, 0.001), 3),
                            grace_period_sec=float(entity.timeout_sec),
                            recovery_permitted=False,
                        )
                        event = self._create_p7_envelope(
                            entity=entity,
                            event_type="timeout_expired",
                            status="timeout",
                            details=details,
                            ts=now,
                        )
                        self._persist_and_apply(event)
                        generated_events.append(event)
                    continue

                # -------------------------------------------------------------
                # Case 3: Entity is running -> Check Stall Deadline
                # -------------------------------------------------------------
                if elapsed >= t_stall:
                    stall_event = self._generate_stall_event(entity, elapsed, t_stall, now)
                    if stall_event:
                        self._persist_and_apply(stall_event)
                        generated_events.append(stall_event)

            return generated_events

    def _generate_stall_event(
        self, entity: EntityState, elapsed: float, threshold: float, now: datetime
    ) -> Optional[CommonEventEnvelope]:
        """Builds the appropriate stall event envelope based on entity type."""
        elapsed_rounded = round(max(elapsed, 0.001), 3)
        threshold_val = float(threshold)

        if entity.entity_type == "agent":
            details = P7BeaconMissedDetails(
                trigger_condition=P7StalledTriggerEnum.BEACON_HEARTBEAT_TIMEOUT,
                last_event_id=entity.last_event_id,
                elapsed_sec=elapsed_rounded,
                threshold_sec=threshold_val,
                recovery_permitted=True,
            )
            return self._create_p7_envelope(
                entity=entity,
                event_type="beacon_missed",
                status="stalled",
                details=details,
                ts=now,
            )

        elif entity.entity_type == "task":
            details = P7TaskStalledDetails(
                trigger_condition=P7StalledTriggerEnum.TASK_PROGRESS_TIMEOUT,
                last_event_id=entity.last_event_id,
                elapsed_sec=elapsed_rounded,
                threshold_sec=threshold_val,
                recovery_permitted=True,
            )
            return self._create_p7_envelope(
                entity=entity,
                event_type="task_stalled",
                status="stalled",
                details=details,
                ts=now,
            )

        elif entity.entity_type == "session":
            if not entity.is_established:
                # Never generate session_stalled for unestablished sessions
                return None
            details = P7SessionStalledDetails(
                trigger_condition=P7StalledTriggerEnum.SESSION_IDLE_TIMEOUT,
                last_event_id=entity.last_event_id,
                elapsed_sec=elapsed_rounded,
                threshold_sec=threshold_val,
                recovery_permitted=True,
            )
            return self._create_p7_envelope(
                entity=entity,
                event_type="session_stalled",
                status="stalled",
                details=details,
                ts=now,
            )

        elif entity.entity_type == "transfer":
            details = P7TransferStalledDetails(
                trigger_condition=P7StalledTriggerEnum.TRANSFER_CHUNK_TIMEOUT,
                last_event_id=entity.last_event_id,
                elapsed_sec=elapsed_rounded,
                threshold_sec=threshold_val,
                recovery_permitted=True,
            )
            return self._create_p7_envelope(
                entity=entity,
                event_type="transfer_stalled",
                status="stalled",
                details=details,
                ts=now,
            )

        return None

    def _create_p7_envelope(
        self,
        entity: EntityState,
        event_type: str,
        status: str,
        details: object,
        ts: datetime,
    ) -> CommonEventEnvelope:
        """Constructs and formally validates a CommonEventEnvelope for P7 analytics."""
        # Fetch last event to preserve host/technique context
        last_event = self._repo.get_by_id(entity.last_event_id)
        if last_event:
            host_dict = last_event.host.model_dump(mode="json")
            technique_dict = last_event.technique.model_dump(mode="json")
        else:
            host_dict = {
                "host_id": "analytics-host-01",
                "ip": "10.0.10.15",
                "role": "target",
            }
            technique_dict = {
                "id": "p7-watchdog",
                "internal_name": "P7 Watchdog Timeout",
                "attack_id": "T1071.001",
                "attack_name": "Application Layer Protocol",
                "tactic": "Command and Control",
            }

        payload = {
            "event_id": str(uuid4()),
            "schema_version": "1.0.0",
            "campaign_id": entity.campaign_id,
            "run_id": entity.run_id,
            "ts": ts.isoformat(),
            "received_at": ts.isoformat(),
            "source": "p7_analytics",
            "type": event_type,
            "status": status,
            "host": host_dict,
            "destination": None,
            "technique": technique_dict,
            "correlation": {
                "entity_id": entity.entity_id,
                "entity_type": entity.entity_type,
                "parent_id": entity.parent_id,
            },
            "timeout_sec": None,
            "bytes_transferred_delta": None,
            "details": details.model_dump(mode="json") if hasattr(details, "model_dump") else details,
            "metadata": {
                "is_simulated": True,
                "generator": "p7-analytics-engine",
                "inferred": True,
            },
        }
        return CommonEventEnvelope.model_validate(payload)

    def _persist_and_apply(self, event: CommonEventEnvelope) -> None:
        """Saves generated P7 event to the repository and updates tracker state."""
        payload_hash = compute_canonical_payload_hash(event)
        self._repo.save_if_absent(event, payload_hash)
        self._tracker.process_event(event)
