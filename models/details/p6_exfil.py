from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from ..enums import ExfilChannelEnum

class P6TransferStartedDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channel: ExfilChannelEnum
    synthetic_payload_id: str = Field(..., min_length=1)
    encoding_type: str = Field(..., min_length=1)
    total_size_bytes: int = Field(..., gt=0)
    chunk_size_bytes: int = Field(..., gt=0)
    chunks_total: int = Field(..., gt=0)

class P6TransferProgressDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channel: ExfilChannelEnum
    synthetic_payload_id: str = Field(..., min_length=1)
    encoding_type: str = Field(..., min_length=1)
    chunk_index: int = Field(..., ge=0)
    chunks_total: int = Field(..., gt=0)
    bytes_transferred_total: int = Field(..., ge=0)
    total_size_bytes: int = Field(..., gt=0)
    effective_throughput_bps: Optional[float] = Field(None, ge=0.0)
    chunk_queries_count: Optional[int] = Field(None, ge=1)

    @model_validator(mode="after")
    def validate_cross_field_bounds(self) -> "P6TransferProgressDetails":
        if self.chunk_index >= self.chunks_total:
            raise ValueError(
                f"chunk_index ({self.chunk_index}) must be strictly less than chunks_total ({self.chunks_total})."
            )
        if self.bytes_transferred_total > self.total_size_bytes:
            raise ValueError(
                f"bytes_transferred_total ({self.bytes_transferred_total}) cannot exceed total_size_bytes ({self.total_size_bytes})."
            )
        return self

class P6TransferCompletedDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channel: ExfilChannelEnum
    synthetic_payload_id: str = Field(..., min_length=1)
    total_bytes_transferred: int = Field(..., gt=0)
    total_chunks_sent: int = Field(..., gt=0)
    total_duration_sec: float = Field(..., gt=0.0)
    effective_throughput_bps: float = Field(..., gt=0.0)
    verification_hash: str = Field(..., min_length=1)

class P6TransferFailedDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channel: ExfilChannelEnum
    synthetic_payload_id: str = Field(..., min_length=1)
    failure_reason: str = Field(..., min_length=1)
    bytes_transferred_before_failure: int = Field(..., ge=0)
    chunks_transferred_before_failure: int = Field(..., ge=0)
