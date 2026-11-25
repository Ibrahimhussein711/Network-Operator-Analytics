from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import List, NamedTuple, Optional
from uuid import UUID
from models.envelope import CommonEventEnvelope

class IngestionResultStatus(str, Enum):
    """Result status of an atomic ingestion attempt."""
    CREATED = "created"        # New event_id; successfully stored
    DUPLICATE = "duplicate"    # event_id exists and payload hash matches
    CONFLICT = "conflict"      # event_id exists but payload hash differs

class IngestionOutcome(NamedTuple):
    """Outcome of an atomic save_if_absent call."""
    status: IngestionResultStatus
    stored_event: CommonEventEnvelope

class IEventRepository(ABC):
    """Abstract repository interface for Project 07 event persistence."""

    @abstractmethod
    def save_if_absent(self, event: CommonEventEnvelope, payload_hash: str) -> IngestionOutcome:
        """
        Atomically inspects event_id and persists event if absent.
        - If event_id absent: persists (event, payload_hash), returns CREATED with stored event.
        - If event_id exists and stored_hash == payload_hash: returns DUPLICATE with original stored event.
        - If event_id exists and stored_hash != payload_hash: returns CONFLICT with original stored event.
        Must be thread-safe and guarantee data isolation.
        """
        pass

    @abstractmethod
    def get_by_id(self, event_id: UUID) -> Optional[CommonEventEnvelope]:
        """Retrieves a stored event by its unique ID. Returns deep copy for data isolation."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Returns the total number of unique events stored."""
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """Returns True if the underlying storage mechanism is available and functional."""
        pass

    @abstractmethod
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
        """
        Retrieves events matching the filter criteria in deterministic chronological order.
        Returns deep copies of all returned events.
        """
        pass

    @abstractmethod
    def get_campaigns(self) -> List[str]:
        """Returns a list of distinct campaign IDs currently present in storage."""
        pass

    @abstractmethod
    def get_runs(self, campaign_id: str) -> List[str]:
        """Returns a list of distinct run IDs for the specified campaign."""
        pass
