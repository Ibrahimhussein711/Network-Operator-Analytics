from pydantic import BaseModel, ConfigDict, Field
from ..enums import P5CommandLabelEnum, ShellEnvironmentEnum, ShellTechniqueEnum

class P5ConnectionRequestedDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    shell_technique: ShellTechniqueEnum
    shell_environment: ShellEnvironmentEnum
    is_obfuscated: bool
    encoding_type: str = Field(..., min_length=1)

class P5ConnectionEstablishedDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    shell_technique: ShellTechniqueEnum
    shell_environment: ShellEnvironmentEnum
    is_obfuscated: bool
    encoding_type: str = Field(..., min_length=1)
    handshake_duration_ms: int = Field(..., ge=0)
    interactive_prompt_ready: bool

class P5ConnectionFailedDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    shell_technique: ShellTechniqueEnum
    shell_environment: ShellEnvironmentEnum
    failure_reason: str = Field(..., min_length=1)
    attempt_duration_ms: int = Field(..., ge=0)

class P5SessionActivityDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    shell_technique: ShellTechniqueEnum
    shell_environment: ShellEnvironmentEnum
    is_obfuscated: bool
    encoding_type: str = Field(..., min_length=1)
    command_label: P5CommandLabelEnum
    command_count_cumulative: int = Field(..., ge=1)
    session_uptime_sec: int = Field(..., ge=0)

class P5SessionClosedDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    shell_technique: ShellTechniqueEnum
    shell_environment: ShellEnvironmentEnum
    exit_reason: str = Field(..., min_length=1)
    total_session_duration_sec: int = Field(..., ge=0)
    total_commands_executed: int = Field(..., ge=0)
