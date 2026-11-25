from enum import Enum

class StrEnum(str, Enum):
    """String enum compatible with Python 3.10 and earlier."""
    pass

class SourceEnum(StrEnum):
    P4_C2 = "p4_c2"
    P5_SHELL = "p5_shell"
    P6_EXFIL = "p6_exfil"
    P7_ANALYTICS = "p7_analytics"

class StatusEnum(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STALLED = "stalled"
    TIMEOUT = "timeout"

class EntityTypeEnum(StrEnum):
    AGENT = "agent"
    TASK = "task"
    SESSION = "session"
    TRANSFER = "transfer"

class EndpointRoleEnum(StrEnum):
    TARGET = "target"
    PIVOT = "pivot"
    C2_SERVER = "c2_server"
    OPERATOR_LISTENER = "operator_listener"
    EXFIL_RECEIVER = "exfil_receiver"

class ProtocolEnum(StrEnum):
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    HTTP = "http"
    HTTPS = "https"
    DNS = "dns"
    CUSTOM = "custom"

class ShellTechniqueEnum(StrEnum):
    TCP_REVERSE = "tcp_reverse"
    HTTPS_TUNNEL = "https_tunnel"
    DNS_CMD = "dns_cmd"
    ICMP_ECHO = "icmp_echo"
    UDP_RAW = "udp_raw"

class ShellEnvironmentEnum(StrEnum):
    POSIX = "posix"
    WINDOWS = "windows"
    CUSTOM = "custom"
    UNKNOWN = "unknown"

class ExfilChannelEnum(StrEnum):
    DNS_TUNNEL = "dns_tunnel"
    ICMP_TUNNEL = "icmp_tunnel"
    HTTPS_BEACON = "https_beacon"

class C2ChannelEnum(StrEnum):
    HTTP = "http"
    HTTPS = "https"
    DNS = "dns"

class P4ExecutorEnum(StrEnum):
    SIMULATED_POSIX = "simulated_posix"
    SIMULATED_WINDOWS = "simulated_windows"
    INTERNAL_SIMULATOR = "internal_simulator"

class P4ActionLabelEnum(StrEnum):
    SIMULATE_HOST_INVENTORY = "simulate_host_inventory"
    SIMULATE_PROCESS_ENUMERATION = "simulate_process_enumeration"
    SIMULATE_NETWORK_DISCOVERY = "simulate_network_discovery"
    SIMULATE_USER_DISCOVERY = "simulate_user_discovery"
    SIMULATE_SERVICE_STATUS_CHECK = "simulate_service_status_check"
    SIMULATE_FILE_METADATA_QUERY = "simulate_file_metadata_query"

class P5CommandLabelEnum(StrEnum):
    SIMULATE_QUERY_GROUP_MEMBERSHIP = "simulate_query_group_membership"
    SIMULATE_QUERY_OS_VERSION = "simulate_query_os_version"
    SIMULATE_CHECK_PRIVILEGES = "simulate_check_privileges"
    SIMULATE_INSPECT_INTERFACES = "simulate_inspect_interfaces"
    SIMULATE_READ_TEST_FLAG = "simulate_read_test_flag"

class P7StalledTriggerEnum(StrEnum):
    BEACON_HEARTBEAT_TIMEOUT = "beacon_heartbeat_timeout"
    TASK_PROGRESS_TIMEOUT = "task_progress_timeout"
    SESSION_IDLE_TIMEOUT = "session_idle_timeout"
    TRANSFER_CHUNK_TIMEOUT = "transfer_chunk_timeout"

class P7TimeoutTriggerEnum(StrEnum):
    GRACE_PERIOD_EXPIRED = "grace_period_expired"
    HANDSHAKE_TIMEOUT = "handshake_timeout"
