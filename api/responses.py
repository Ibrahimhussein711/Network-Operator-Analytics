from datetime import datetime
from typing import Any, List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

# --- Single Event Responses ---

class EventIngestedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["accepted", "deduplicated"]
    event_id: UUID
    received_at: datetime
    message: str

# --- Error Responses ---

class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    loc: List[str | int]
    msg: str
    type: str

class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    error: str
    message: str
    timestamp: datetime
    event_id: Optional[UUID] = None
    details: Optional[List[ErrorDetail]] = None

# --- Batch Responses ---

class BatchItemOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: Optional[UUID] = None
    outcome: Literal["accepted", "deduplicated", "failed"]
    http_status: int
    received_at: Optional[datetime] = None
    error: Optional[str] = None

class BatchIngestionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total_submitted: int
    accepted_count: int
    deduplicated_count: int
    failed_count: int
    results: List[BatchItemOutcome]

# --- Health Responses ---

class LivenessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["live"]
    timestamp: datetime

class StorageStats(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str
    connected: bool
    event_count: int

class ReadinessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ready", "unhealthy"]
    timestamp: datetime
    storage: StorageStats
