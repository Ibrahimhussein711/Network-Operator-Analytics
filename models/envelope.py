from datetime import datetime, timezone
from typing import Annotated, Any, Dict, Literal, Optional, Union
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .base import Correlation, DestinationEndpoint, HostEndpoint, Metadata, Technique
from .enums import EntityTypeEnum, SourceEnum, StatusEnum
from .details import (
    P4AgentRegisteredDetails,
    P4BeaconCheckinDetails,
    P4TaskStartedDetails,
    P4TaskProgressDetails,
    P4TaskCompletedDetails,
    P4TaskFailedDetails,
    P5ConnectionRequestedDetails,
    P5ConnectionEstablishedDetails,
    P5ConnectionFailedDetails,
    P5SessionActivityDetails,
    P5SessionClosedDetails,
    P6TransferStartedDetails,
    P6TransferProgressDetails,
    P6TransferCompletedDetails,
    P6TransferFailedDetails,
    P7BeaconMissedDetails,
    P7TaskStalledDetails,
    P7SessionStalledDetails,
    P7TransferStalledDetails,
    P7TimeoutExpiredDetails,
)

# Mapping of event types to their dedicated details models
EVENT_DETAILS_MAP = {
    "agent_registered": P4AgentRegisteredDetails,
    "beacon_checkin": P4BeaconCheckinDetails,
    "task_started": P4TaskStartedDetails,
    "task_progress": P4TaskProgressDetails,
    "task_completed": P4TaskCompletedDetails,
    "task_failed": P4TaskFailedDetails,
    "connection_requested": P5ConnectionRequestedDetails,
    "connection_established": P5ConnectionEstablishedDetails,
    "connection_failed": P5ConnectionFailedDetails,
    "session_activity": P5SessionActivityDetails,
    "session_closed": P5SessionClosedDetails,
    "transfer_started": P6TransferStartedDetails,
    "transfer_progress": P6TransferProgressDetails,
    "transfer_completed": P6TransferCompletedDetails,
    "transfer_failed": P6TransferFailedDetails,
    "beacon_missed": P7BeaconMissedDetails,
    "task_stalled": P7TaskStalledDetails,
    "session_stalled": P7SessionStalledDetails,
    "transfer_stalled": P7TransferStalledDetails,
    "timeout_expired": P7TimeoutExpiredDetails,
}

SOURCE_TYPE_MAP = {
    SourceEnum.P4_C2: {
        "agent_registered",
        "beacon_checkin",
        "task_started",
        "task_progress",
        "task_completed",
        "task_failed",
    },
    SourceEnum.P5_SHELL: {
        "connection_requested",
        "connection_established",
        "connection_failed",
        "session_activity",
        "session_closed",
    },
    SourceEnum.P6_EXFIL: {
        "transfer_started",
        "transfer_progress",
        "transfer_completed",
        "transfer_failed",
    },
    SourceEnum.P7_ANALYTICS: {
        "beacon_missed",
        "task_stalled",
        "session_stalled",
        "transfer_stalled",
        "timeout_expired",
    },
}

TYPE_STATUS_MAP = {
    "agent_registered": StatusEnum.RUNNING,
    "beacon_checkin": StatusEnum.RUNNING,
    "task_started": StatusEnum.RUNNING,
    "task_progress": StatusEnum.RUNNING,
    "task_completed": StatusEnum.COMPLETED,
    "task_failed": StatusEnum.FAILED,
    "connection_requested": StatusEnum.PENDING,
    "connection_established": StatusEnum.RUNNING,
    "connection_failed": StatusEnum.FAILED,
    "session_activity": StatusEnum.RUNNING,
    "session_closed": StatusEnum.COMPLETED,
    "transfer_started": StatusEnum.RUNNING,
    "transfer_progress": StatusEnum.RUNNING,
    "transfer_completed": StatusEnum.COMPLETED,
    "transfer_failed": StatusEnum.FAILED,
    "beacon_missed": StatusEnum.STALLED,
    "task_stalled": StatusEnum.STALLED,
    "session_stalled": StatusEnum.STALLED,
    "transfer_stalled": StatusEnum.STALLED,
    "timeout_expired": StatusEnum.TIMEOUT,
}

MANDATORY_TIMEOUT_EVENTS = {
    "agent_registered",
    "task_started",
    "connection_requested",
    "connection_established",
    "transfer_started",
}

FORBIDDEN_TIMEOUT_EVENTS = {
    "beacon_missed",
    "task_stalled",
    "session_stalled",
    "transfer_stalled",
    "timeout_expired",
}

EventDetailsUnion = Union[
    P4AgentRegisteredDetails,
    P4BeaconCheckinDetails,
    P4TaskStartedDetails,
    P4TaskProgressDetails,
    P4TaskCompletedDetails,
    P4TaskFailedDetails,
    P5ConnectionRequestedDetails,
    P5ConnectionEstablishedDetails,
    P5ConnectionFailedDetails,
    P5SessionActivityDetails,
    P5SessionClosedDetails,
    P6TransferStartedDetails,
    P6TransferProgressDetails,
    P6TransferCompletedDetails,
    P6TransferFailedDetails,
    P7BeaconMissedDetails,
    P7TaskStalledDetails,
    P7SessionStalledDetails,
    P7TransferStalledDetails,
    P7TimeoutExpiredDetails,
]

class CommonEventEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    schema_version: str = Field("1.0.0", pattern=r"^1\.[0-9]+\.[0-9]+$")
    campaign_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    ts: datetime
    received_at: Optional[datetime] = None
    source: SourceEnum
    type: str
    status: StatusEnum
    host: HostEndpoint
    destination: Optional[DestinationEndpoint] = None
    technique: Technique
    correlation: Correlation
    timeout_sec: Optional[int] = Field(None, gt=0)
    bytes_transferred_delta: Optional[int] = Field(None, ge=0)
    details: Union[EventDetailsUnion, Dict[str, Any]]
    metadata: Metadata

    @model_validator(mode="before")
    @classmethod
    def parse_details_object(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            event_type = data.get("type")
            details = data.get("details")
            if event_type in EVENT_DETAILS_MAP and isinstance(details, dict):
                model_cls = EVENT_DETAILS_MAP[event_type]
                data["details"] = model_cls.model_validate(details)
        return data

    @model_validator(mode="after")
    def validate_envelope_rules(self) -> "CommonEventEnvelope":
        # 1. Source - Type compatibility
        valid_types = SOURCE_TYPE_MAP.get(self.source, set())
        if self.type not in valid_types:
            raise ValueError(f"Event type '{self.type}' is not permitted for source '{self.source}'.")

        # 2. Type - Status compatibility
        expected_status = TYPE_STATUS_MAP.get(self.type)
        if expected_status is not None and self.status != expected_status:
            raise ValueError(
                f"Event type '{self.type}' requires status '{expected_status}', got '{self.status}'."
            )

        # 3. Mandatory & Forbidden Timeout Rules
        if self.type in MANDATORY_TIMEOUT_EVENTS and self.timeout_sec is None:
            raise ValueError(f"Event type '{self.type}' strictly requires a positive 'timeout_sec'.")
        if self.type in FORBIDDEN_TIMEOUT_EVENTS and self.timeout_sec is not None:
            raise ValueError(f"P7-derived event type '{self.type}' cannot declare a 'timeout_sec'.")

        # 4. Correlation Entity Type and Parent ID Rules
        if self.type in {"agent_registered", "beacon_checkin", "beacon_missed"}:
            if self.correlation.entity_type != EntityTypeEnum.AGENT:
                raise ValueError(f"Event '{self.type}' requires entity_type 'agent'.")
            if self.correlation.parent_id is not None:
                raise ValueError(f"Agent event '{self.type}' requires parent_id == None.")

        elif self.type in {"task_started", "task_progress", "task_completed", "task_failed", "task_stalled"}:
            if self.correlation.entity_type != EntityTypeEnum.TASK:
                raise ValueError(f"Event '{self.type}' requires entity_type 'task'.")
            if not self.correlation.parent_id:
                raise ValueError(f"Task event '{self.type}' requires a non-empty parent_id (agent_id).")

        elif self.type in {"connection_requested", "connection_established", "connection_failed", "session_activity", "session_closed", "session_stalled"}:
            if self.correlation.entity_type != EntityTypeEnum.SESSION:
                raise ValueError(f"Event '{self.type}' requires entity_type 'session'.")

        elif self.type in {"transfer_started", "transfer_progress", "transfer_completed", "transfer_failed", "transfer_stalled"}:
            if self.correlation.entity_type != EntityTypeEnum.TRANSFER:
                raise ValueError(f"Event '{self.type}' requires entity_type 'transfer'.")

        elif self.type == "timeout_expired":
            # Must be a concrete type
            if self.correlation.entity_type not in {EntityTypeEnum.AGENT, EntityTypeEnum.TASK, EntityTypeEnum.SESSION, EntityTypeEnum.TRANSFER}:
                raise ValueError(f"timeout_expired requires a concrete entity_type, got '{self.correlation.entity_type}'.")
            if self.correlation.entity_type == EntityTypeEnum.AGENT and self.correlation.parent_id is not None:
                raise ValueError("timeout_expired for agent requires parent_id == None.")
            if self.correlation.entity_type == EntityTypeEnum.TASK and not self.correlation.parent_id:
                raise ValueError("timeout_expired for task requires a non-empty parent_id.")

        # 5. Metadata Provenance Checks
        if self.source == SourceEnum.P7_ANALYTICS:
            if not self.metadata.inferred:
                raise ValueError("P7 analytics events must have metadata.inferred == True.")
        else:
            if self.metadata.inferred:
                raise ValueError(f"Simulator source '{self.source}' must have metadata.inferred == False.")

        # 6. Type-Specific Details Model Verification
        expected_details_cls = EVENT_DETAILS_MAP.get(self.type)
        if expected_details_cls is not None and not isinstance(self.details, expected_details_cls):
            raise ValueError(
                f"Event type '{self.type}' details must be an instance of {expected_details_cls.__name__}."
            )

        return self
