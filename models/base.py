from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, model_validator
from .enums import EndpointRoleEnum, EntityTypeEnum, ProtocolEnum

class HostEndpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host_id: str = Field(..., min_length=1)
    ip: Optional[IPvAnyAddress] = None
    hostname: Optional[str] = Field(None, min_length=1)
    role: EndpointRoleEnum

    @model_validator(mode="after")
    def validate_identity(self) -> "HostEndpoint":
        if self.ip is None and self.hostname is None:
            raise ValueError("Host endpoint must provide at least an IP address or hostname.")
        return self

class DestinationEndpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ip: Optional[IPvAnyAddress] = None
    hostname: Optional[str] = Field(None, min_length=1)
    port: Optional[int] = Field(None, ge=1, le=65535)
    protocol: ProtocolEnum
    role: EndpointRoleEnum

    @model_validator(mode="after")
    def validate_destination(self) -> "DestinationEndpoint":
        if self.ip is None and self.hostname is None:
            raise ValueError("Destination endpoint must provide at least an IP address or hostname.")
        if self.protocol == ProtocolEnum.ICMP and self.port is not None:
            raise ValueError("ICMP destination protocol cannot have a port specified.")
        return self

class Technique(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    internal_name: str = Field(..., min_length=1)
    attack_id: Optional[str] = Field(None, pattern=r"^T[0-9]{4}(\.[0-9]{3})?$")
    attack_name: Optional[str] = None
    tactic: Optional[str] = None

class Correlation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    entity_type: EntityTypeEnum
    parent_id: Optional[str] = None

class Metadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_simulated: Literal[True] = True
    generator: str = Field(..., min_length=1)
    inferred: bool = False
