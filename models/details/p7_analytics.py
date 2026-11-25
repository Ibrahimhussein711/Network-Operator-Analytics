from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator
from ..enums import P7StalledTriggerEnum, P7TimeoutTriggerEnum

class P7BeaconMissedDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trigger_condition: Literal[P7StalledTriggerEnum.BEACON_HEARTBEAT_TIMEOUT] = P7StalledTriggerEnum.BEACON_HEARTBEAT_TIMEOUT
    last_event_id: UUID
    elapsed_sec: float = Field(..., gt=0.0)
    threshold_sec: float = Field(..., gt=0.0)
    recovery_permitted: Literal[True] = True

class P7TaskStalledDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trigger_condition: Literal[P7StalledTriggerEnum.TASK_PROGRESS_TIMEOUT] = P7StalledTriggerEnum.TASK_PROGRESS_TIMEOUT
    last_event_id: UUID
    elapsed_sec: float = Field(..., gt=0.0)
    threshold_sec: float = Field(..., gt=0.0)
    recovery_permitted: Literal[True] = True

class P7SessionStalledDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trigger_condition: Literal[P7StalledTriggerEnum.SESSION_IDLE_TIMEOUT] = P7StalledTriggerEnum.SESSION_IDLE_TIMEOUT
    last_event_id: UUID
    elapsed_sec: float = Field(..., gt=0.0)
    threshold_sec: float = Field(..., gt=0.0)
    recovery_permitted: Literal[True] = True

class P7TransferStalledDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trigger_condition: Literal[P7StalledTriggerEnum.TRANSFER_CHUNK_TIMEOUT] = P7StalledTriggerEnum.TRANSFER_CHUNK_TIMEOUT
    last_event_id: UUID
    elapsed_sec: float = Field(..., gt=0.0)
    threshold_sec: float = Field(..., gt=0.0)
    recovery_permitted: Literal[True] = True

class P7TimeoutExpiredDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trigger_condition: P7TimeoutTriggerEnum
    last_event_id: UUID
    total_elapsed_sec: float = Field(..., gt=0.0)
    grace_period_sec: float = Field(..., ge=0.0)
    recovery_permitted: Literal[False] = False

    @model_validator(mode="after")
    def validate_grace_period_semantics(self) -> "P7TimeoutExpiredDetails":
        if self.trigger_condition == P7TimeoutTriggerEnum.HANDSHAKE_TIMEOUT:
            if self.grace_period_sec != 0.0:
                raise ValueError("handshake_timeout requires grace_period_sec == 0.0.")
        elif self.trigger_condition == P7TimeoutTriggerEnum.GRACE_PERIOD_EXPIRED:
            if self.grace_period_sec <= 0.0:
                raise ValueError("grace_period_expired requires grace_period_sec > 0.0.")
        return self
