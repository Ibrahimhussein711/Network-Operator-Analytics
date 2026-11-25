from typing import Annotated, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field
from ..enums import C2ChannelEnum, P4ActionLabelEnum, P4ExecutorEnum

# --- Action Parameter Submodels ---

class HostInventoryParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scope: Literal["system", "hardware", "os"]
    detail_level: Literal["basic", "full"]

class ProcessEnumerationParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filter_system_procs: bool
    max_results: int = Field(..., ge=1, le=500)

class NetworkDiscoveryParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    simulation_scope: Literal["synthetic_lab_segment_01", "synthetic_lab_segment_02", "synthetic_dmz_zone"]
    discovery_method: Literal["simulated_icmp_sweep", "simulated_tcp_probe", "simulated_arp_broadcast"]

class UserDiscoveryParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    include_service_accounts: bool
    domain_scope: Literal["local", "domain"]

class ServiceStatusCheckParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service_name_tag: str = Field(..., min_length=1, max_length=32)
    check_timeout_sec: int = Field(..., ge=1, le=60)

class FileMetadataQueryParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    directory_tag: Literal["system_logs", "config_store", "staging_area"]
    recursive: bool

P4TaskParamsUnion = Union[
    HostInventoryParams,
    ProcessEnumerationParams,
    NetworkDiscoveryParams,
    UserDiscoveryParams,
    ServiceStatusCheckParams,
    FileMetadataQueryParams,
]

# --- P4 Event Details Models ---

class P4AgentRegisteredDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channel: C2ChannelEnum
    agent_version: str = Field(..., min_length=1)
    beacon_interval_sec: int = Field(..., gt=0)
    jitter_percent: int = Field(..., ge=0, le=100)
    encryption_scheme: str = Field(..., min_length=1)
    supported_executors: list[P4ExecutorEnum] = Field(..., min_length=1)

class P4BeaconCheckinDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channel: C2ChannelEnum
    beacon_counter: int = Field(..., ge=1)
    latency_ms: int = Field(..., ge=0)
    tasks_pending_count: int = Field(..., ge=0)
    active_jitter_sec: Optional[float] = Field(None, ge=0.0)

class P4TaskStartedDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channel: C2ChannelEnum
    action_label: P4ActionLabelEnum
    task_parameters: P4TaskParamsUnion
    executor: P4ExecutorEnum

class P4TaskProgressDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    progress_percent: int = Field(..., ge=0, le=100)
    output_chunk_index: int = Field(..., ge=0)
    partial_output_len: int = Field(..., ge=0)
    total_size_bytes: Optional[int] = Field(None, ge=0)
    bytes_transferred_total: Optional[int] = Field(None, ge=0)

class P4TaskCompletedDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exit_code: Literal[0] = 0
    execution_duration_ms: int = Field(..., ge=0)
    output_summary: str = Field(..., min_length=1)
    total_output_bytes: int = Field(..., ge=0)
    bytes_transferred_total: Optional[int] = Field(None, ge=0)

class P4TaskFailedDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exit_code: int = Field(..., ne=0)
    execution_duration_ms: int = Field(..., ge=0)
    error_type: str = Field(..., min_length=1)
    error_message: str = Field(..., min_length=1)
