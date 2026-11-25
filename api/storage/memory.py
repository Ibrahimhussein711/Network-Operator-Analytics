import copy
from datetime import datetime
import threading
from typing import Dict, List, Optional
from uuid import UUID
from models.envelope import CommonEventEnvelope
from .interface import IEventRepository, IngestionOutcome, IngestionResultStatus

class ThreadSafeInMemoryEventRepository(IEventRepository):
    """
    Thread-safe in-memory implementation of IEventRepository.
    Enforces atomic idempotency and full deep-copy data isolation.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._events: Dict[UUID, CommonEventEnvelope] = {}
        self._hashes: Dict[UUID, str] = {}
        self._ordered_ids: List[UUID] = []
        self._healthy: bool = True

    def save_if_absent(self, event: CommonEventEnvelope, payload_hash: str) -> IngestionOutcome:
        with self._lock:
            event_id = event.event_id
            if event_id in self._events:
                stored_hash = self._hashes[event_id]
                original_event = copy.deepcopy(self._events[event_id])
                if stored_hash == payload_hash:
                    return IngestionOutcome(
                        status=IngestionResultStatus.DUPLICATE,
                        stored_event=original_event
                    )
                else:
                    return IngestionOutcome(
                        status=IngestionResultStatus.CONFLICT,
                        stored_event=original_event
                    )

            # Newly seen event: store deep copy to isolate internal state from external callers
            event_to_store = copy.deepcopy(event)
            self._events[event_id] = event_to_store
            self._hashes[event_id] = payload_hash
            self._ordered_ids.append(event_id)

            return IngestionOutcome(
                status=IngestionResultStatus.CREATED,
                stored_event=copy.deepcopy(event_to_store)
            )

    def get_by_id(self, event_id: UUID) -> Optional[CommonEventEnvelope]:
        with self._lock:
            event = self._events.get(event_id)
            if event is None:
                return None
            return copy.deepcopy(event)

    def count(self) -> int:
        with self._lock:
            return len(self._events)

    def is_healthy(self) -> bool:
        with self._lock:
            return self._healthy

    def set_healthy(self, healthy: bool) -> None:
        """Helper for testing readiness probe failure conditions."""
        with self._lock:
            self._healthy = healthy

    def query_events(
        self,
        campaign_id: Optional[str] = None,
        run_id: Optional[str] = None,
        source: Optional[str] = None,
        event_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CommonEventEnvelope]:
        with self._lock:
            results: List[CommonEventEnvelope] = []
            for eid in self._ordered_ids:
                ev = self._events[eid]
                if campaign_id is not None and ev.campaign_id != campaign_id:
                    continue
                if run_id is not None and ev.run_id != run_id:
                    continue
                if source is not None and ev.source != source:
                    continue
                if event_type is not None and ev.type != event_type:
                    continue
                if entity_id is not None and ev.correlation.entity_id != entity_id:
                    continue
                event_time = ev.received_at or ev.ts
                if start_time is not None and event_time < start_time:
                    continue
                if end_time is not None and event_time > end_time:
                    continue
                results.append(ev)

            # Deterministic ordering by (received_at or ts, ts, event_id)
            results.sort(key=lambda x: (x.received_at or x.ts, x.ts, str(x.event_id)))
            sliced = results[offset : offset + limit]
            return [copy.deepcopy(e) for e in sliced]

    def get_campaigns(self) -> List[str]:
        with self._lock:
            campaigns = {ev.campaign_id for ev in self._events.values()}
            return sorted(list(campaigns))

    def get_runs(self, campaign_id: str) -> List[str]:
        with self._lock:
            runs = {
                ev.run_id
                for ev in self._events.values()
                if ev.campaign_id == campaign_id
            }
            return sorted(list(runs))

    def clear(self) -> None:
        """Helper for test isolation."""
        with self._lock:
            self._events.clear()
            self._hashes.clear()
            self._ordered_ids.clear()

