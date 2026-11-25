import copy
import json
from pathlib import Path
import pytest
import jsonschema

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "event.schema.json"

@pytest.fixture(scope="session")
def raw_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="session")
def schema_validator(raw_schema):
    validator_cls = jsonschema.validators.validator_for(raw_schema)
    validator_cls.check_schema(raw_schema)
    return validator_cls(raw_schema)

CANONICAL_EVENTS_DATA = {
        # --- P4 C2 Events (6) ---
        "agent_registered": {
            "event_id": "550e8400-e29b-41d4-a716-446655440001",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:00:00.000Z",
            "received_at": None,
            "source": "p4_c2",
            "type": "agent_registered",
            "status": "running",
            "host": {
                "host_id": "target-node-01",
                "ip": "10.0.10.15",
                "hostname": "wkst-hr-01.lab",
                "role": "target"
            },
            "destination": {
                "ip": "198.51.100.10",
                "hostname": "c2.exercise.local",
                "port": 443,
                "protocol": "https",
                "role": "c2_server"
            },
            "technique": {
                "id": "c2-beacon-web",
                "internal_name": "Simulated Web Beaconing Registration",
                "attack_id": "T1071.001",
                "attack_name": "Application Layer Protocol: Web Protocols",
                "tactic": "Command and Control"
            },
            "correlation": {
                "entity_id": "agent-c2-01",
                "entity_type": "agent",
                "parent_id": None
            },
            "timeout_sec": 30,
            "bytes_transferred_delta": None,
            "details": {
                "channel": "https",
                "agent_version": "1.0.0",
                "beacon_interval_sec": 10,
                "jitter_percent": 15,
                "encryption_scheme": "xor_static",
                "supported_executors": ["simulated_posix", "internal_simulator"]
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p4-c2-simulator",
                "inferred": False
            }
        },
        "beacon_checkin": {
            "event_id": "550e8400-e29b-41d4-a716-446655440002",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:00:10.000Z",
            "received_at": None,
            "source": "p4_c2",
            "type": "beacon_checkin",
            "status": "running",
            "host": {
                "host_id": "target-node-01",
                "ip": "10.0.10.15",
                "role": "target"
            },
            "destination": {
                "ip": "198.51.100.10",
                "port": 443,
                "protocol": "https",
                "role": "c2_server"
            },
            "technique": {
                "id": "c2-beacon-web",
                "internal_name": "Simulated Web Beaconing Heartbeat",
                "attack_id": "T1071.001",
                "attack_name": "Application Layer Protocol: Web Protocols",
                "tactic": "Command and Control"
            },
            "correlation": {
                "entity_id": "agent-c2-01",
                "entity_type": "agent",
                "parent_id": None
            },
            "timeout_sec": None,
            "bytes_transferred_delta": 128,
            "details": {
                "channel": "https",
                "beacon_counter": 1,
                "latency_ms": 25,
                "tasks_pending_count": 0,
                "active_jitter_sec": 1.5
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p4-c2-simulator",
                "inferred": False
            }
        },
        "task_started": {
            "event_id": "550e8400-e29b-41d4-a716-446655440003",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:01:00.000Z",
            "received_at": None,
            "source": "p4_c2",
            "type": "task_started",
            "status": "running",
            "host": {
                "host_id": "target-node-01",
                "ip": "10.0.10.15",
                "role": "target"
            },
            "destination": None,
            "technique": {
                "id": "c2-task-exec",
                "internal_name": "Simulated Command Execution Task",
                "attack_id": "T1059",
                "attack_name": "Command and Scripting Interpreter",
                "tactic": "Execution"
            },
            "correlation": {
                "entity_id": "task-c2-101",
                "entity_type": "task",
                "parent_id": "agent-c2-01"
            },
            "timeout_sec": 45,
            "bytes_transferred_delta": None,
            "details": {
                "channel": "https",
                "action_label": "simulate_host_inventory",
                "task_parameters": {
                    "scope": "system",
                    "detail_level": "basic"
                },
                "executor": "simulated_posix"
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p4-c2-simulator",
                "inferred": False
            }
        },
        "task_progress": {
            "event_id": "550e8400-e29b-41d4-a716-446655440004",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:01:15.000Z",
            "received_at": None,
            "source": "p4_c2",
            "type": "task_progress",
            "status": "running",
            "host": {
                "host_id": "target-node-01",
                "ip": "10.0.10.15",
                "role": "target"
            },
            "destination": None,
            "technique": {
                "id": "c2-task-exec",
                "internal_name": "Simulated Command Execution Task",
                "attack_id": "T1059",
                "attack_name": "Command and Scripting Interpreter",
                "tactic": "Execution"
            },
            "correlation": {
                "entity_id": "task-c2-101",
                "entity_type": "task",
                "parent_id": "agent-c2-01"
            },
            "timeout_sec": None,
            "bytes_transferred_delta": 256,
            "details": {
                "progress_percent": 50,
                "output_chunk_index": 0,
                "partial_output_len": 256,
                "total_size_bytes": 512,
                "bytes_transferred_total": 256
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p4-c2-simulator",
                "inferred": False
            }
        },
        "task_completed": {
            "event_id": "550e8400-e29b-41d4-a716-446655440005",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:01:30.000Z",
            "received_at": None,
            "source": "p4_c2",
            "type": "task_completed",
            "status": "completed",
            "host": {
                "host_id": "target-node-01",
                "ip": "10.0.10.15",
                "role": "target"
            },
            "destination": None,
            "technique": {
                "id": "c2-task-exec",
                "internal_name": "Simulated Command Execution Task",
                "attack_id": "T1059",
                "attack_name": "Command and Scripting Interpreter",
                "tactic": "Execution"
            },
            "correlation": {
                "entity_id": "task-c2-101",
                "entity_type": "task",
                "parent_id": "agent-c2-01"
            },
            "timeout_sec": None,
            "bytes_transferred_delta": 256,
            "details": {
                "exit_code": 0,
                "execution_duration_ms": 1250,
                "output_summary": "Simulated inventory generated successfully",
                "total_output_bytes": 512,
                "bytes_transferred_total": 512
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p4-c2-simulator",
                "inferred": False
            }
        },
        "task_failed": {
            "event_id": "550e8400-e29b-41d4-a716-446655440006",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:02:00.000Z",
            "received_at": None,
            "source": "p4_c2",
            "type": "task_failed",
            "status": "failed",
            "host": {
                "host_id": "target-node-01",
                "ip": "10.0.10.15",
                "role": "target"
            },
            "destination": None,
            "technique": {
                "id": "c2-task-exec",
                "internal_name": "Simulated Command Execution Task",
                "attack_id": "T1059",
                "attack_name": "Command and Scripting Interpreter",
                "tactic": "Execution"
            },
            "correlation": {
                "entity_id": "task-c2-102",
                "entity_type": "task",
                "parent_id": "agent-c2-01"
            },
            "timeout_sec": None,
            "bytes_transferred_delta": 0,
            "details": {
                "exit_code": 1,
                "execution_duration_ms": 350,
                "error_type": "permission_denied",
                "error_message": "Synthetic access test failed"
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p4-c2-simulator",
                "inferred": False
            }
        },

        # --- P5 Shell Events (5) ---
        "connection_requested": {
            "event_id": "550e8400-e29b-41d4-a716-446655440010",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:05:00.000Z",
            "received_at": None,
            "source": "p5_shell",
            "type": "connection_requested",
            "status": "pending",
            "host": {
                "host_id": "target-node-02",
                "ip": "10.0.10.35",
                "role": "target"
            },
            "destination": {
                "ip": "198.51.100.50",
                "port": 4444,
                "protocol": "tcp",
                "role": "operator_listener"
            },
            "technique": {
                "id": "shell-reverse-tcp",
                "internal_name": "Simulated Obfuscated TCP Reverse Shell",
                "attack_id": "T1059.004",
                "attack_name": "Command and Scripting Interpreter: Unix Shell",
                "tactic": "Execution"
            },
            "correlation": {
                "entity_id": "session-sim-501",
                "entity_type": "session",
                "parent_id": None
            },
            "timeout_sec": 15,
            "bytes_transferred_delta": 0,
            "details": {
                "shell_technique": "tcp_reverse",
                "shell_environment": "posix",
                "is_obfuscated": True,
                "encoding_type": "xor_stream"
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p5-shell-simulator",
                "inferred": False
            }
        },
        "connection_established": {
            "event_id": "550e8400-e29b-41d4-a716-446655440011",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:05:02.000Z",
            "received_at": None,
            "source": "p5_shell",
            "type": "connection_established",
            "status": "running",
            "host": {
                "host_id": "target-node-02",
                "ip": "10.0.10.35",
                "role": "target"
            },
            "destination": {
                "ip": "198.51.100.50",
                "port": 4444,
                "protocol": "tcp",
                "role": "operator_listener"
            },
            "technique": {
                "id": "shell-reverse-tcp",
                "internal_name": "Simulated Obfuscated TCP Reverse Shell",
                "attack_id": "T1059.004",
                "attack_name": "Command and Scripting Interpreter: Unix Shell",
                "tactic": "Execution"
            },
            "correlation": {
                "entity_id": "session-sim-501",
                "entity_type": "session",
                "parent_id": None
            },
            "timeout_sec": 60,
            "bytes_transferred_delta": 128,
            "details": {
                "shell_technique": "tcp_reverse",
                "shell_environment": "posix",
                "is_obfuscated": True,
                "encoding_type": "xor_stream",
                "handshake_duration_ms": 45,
                "interactive_prompt_ready": True
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p5-shell-simulator",
                "inferred": False
            }
        },
        "connection_failed": {
            "event_id": "550e8400-e29b-41d4-a716-446655440012",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:05:15.000Z",
            "received_at": None,
            "source": "p5_shell",
            "type": "connection_failed",
            "status": "failed",
            "host": {
                "host_id": "target-node-02",
                "ip": "10.0.10.35",
                "role": "target"
            },
            "destination": {
                "ip": "198.51.100.50",
                "port": 4444,
                "protocol": "tcp",
                "role": "operator_listener"
            },
            "technique": {
                "id": "shell-reverse-tcp",
                "internal_name": "Simulated Obfuscated TCP Reverse Shell",
                "attack_id": "T1059.004",
                "attack_name": "Command and Scripting Interpreter: Unix Shell",
                "tactic": "Execution"
            },
            "correlation": {
                "entity_id": "session-sim-502",
                "entity_type": "session",
                "parent_id": None
            },
            "timeout_sec": None,
            "bytes_transferred_delta": 0,
            "details": {
                "shell_technique": "tcp_reverse",
                "shell_environment": "posix",
                "failure_reason": "connection_refused",
                "attempt_duration_ms": 15000
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p5-shell-simulator",
                "inferred": False
            }
        },
        "session_activity": {
            "event_id": "550e8400-e29b-41d4-a716-446655440013",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:06:00.000Z",
            "received_at": None,
            "source": "p5_shell",
            "type": "session_activity",
            "status": "running",
            "host": {
                "host_id": "target-node-02",
                "ip": "10.0.10.35",
                "role": "target"
            },
            "destination": {
                "ip": "198.51.100.50",
                "port": 4444,
                "protocol": "tcp",
                "role": "operator_listener"
            },
            "technique": {
                "id": "shell-reverse-tcp",
                "internal_name": "Simulated Obfuscated TCP Reverse Shell",
                "attack_id": "T1059.004",
                "attack_name": "Command and Scripting Interpreter: Unix Shell",
                "tactic": "Execution"
            },
            "correlation": {
                "entity_id": "session-sim-501",
                "entity_type": "session",
                "parent_id": None
            },
            "timeout_sec": None,
            "bytes_transferred_delta": 64,
            "details": {
                "shell_technique": "tcp_reverse",
                "shell_environment": "posix",
                "is_obfuscated": True,
                "encoding_type": "xor_stream",
                "command_label": "simulate_query_group_membership",
                "command_count_cumulative": 1,
                "session_uptime_sec": 58
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p5-shell-simulator",
                "inferred": False
            }
        },
        "session_closed": {
            "event_id": "550e8400-e29b-41d4-a716-446655440014",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:08:00.000Z",
            "received_at": None,
            "source": "p5_shell",
            "type": "session_closed",
            "status": "completed",
            "host": {
                "host_id": "target-node-02",
                "ip": "10.0.10.35",
                "role": "target"
            },
            "destination": {
                "ip": "198.51.100.50",
                "port": 4444,
                "protocol": "tcp",
                "role": "operator_listener"
            },
            "technique": {
                "id": "shell-reverse-tcp",
                "internal_name": "Simulated Obfuscated TCP Reverse Shell",
                "attack_id": "T1059.004",
                "attack_name": "Command and Scripting Interpreter: Unix Shell",
                "tactic": "Execution"
            },
            "correlation": {
                "entity_id": "session-sim-501",
                "entity_type": "session",
                "parent_id": None
            },
            "timeout_sec": None,
            "bytes_transferred_delta": 0,
            "details": {
                "shell_technique": "tcp_reverse",
                "shell_environment": "posix",
                "exit_reason": "clean_operator_exit",
                "total_session_duration_sec": 178,
                "total_commands_executed": 3
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p5-shell-simulator",
                "inferred": False
            }
        },

        # --- P6 Exfiltration Events (4) ---
        "transfer_started": {
            "event_id": "550e8400-e29b-41d4-a716-446655440020",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:10:00.000Z",
            "received_at": None,
            "source": "p6_exfil",
            "type": "transfer_started",
            "status": "running",
            "host": {
                "host_id": "target-node-01",
                "ip": "10.0.10.15",
                "role": "target"
            },
            "destination": {
                "ip": "198.51.100.53",
                "hostname": "ns1.tunnel.synthetic.lab",
                "port": 53,
                "protocol": "dns",
                "role": "exfil_receiver"
            },
            "technique": {
                "id": "exfil-tunnel-dns",
                "internal_name": "Simulated DNS Tunneling Exfiltration",
                "attack_id": "T1048.003",
                "attack_name": "Exfiltration Over Alternative Protocol: Exfiltration Over Unencrypted Non-C2 Protocol",
                "tactic": "Exfiltration"
            },
            "correlation": {
                "entity_id": "transfer-sim-901",
                "entity_type": "transfer",
                "parent_id": None
            },
            "timeout_sec": 45,
            "bytes_transferred_delta": 0,
            "details": {
                "channel": "dns_tunnel",
                "synthetic_payload_id": "synthetic_dataset_sample_42",
                "encoding_type": "base32_subdomain",
                "total_size_bytes": 10240,
                "chunk_size_bytes": 512,
                "chunks_total": 20
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p6-exfil-simulator",
                "inferred": False
            }
        },
        "transfer_progress": {
            "event_id": "550e8400-e29b-41d4-a716-446655440021",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:10:15.000Z",
            "received_at": None,
            "source": "p6_exfil",
            "type": "transfer_progress",
            "status": "running",
            "host": {
                "host_id": "target-node-01",
                "ip": "10.0.10.15",
                "role": "target"
            },
            "destination": {
                "ip": "198.51.100.53",
                "port": 53,
                "protocol": "dns",
                "role": "exfil_receiver"
            },
            "technique": {
                "id": "exfil-tunnel-dns",
                "internal_name": "Simulated DNS Tunneling Exfiltration",
                "attack_id": "T1048.003",
                "attack_name": "Exfiltration Over Alternative Protocol: Exfiltration Over Unencrypted Non-C2 Protocol",
                "tactic": "Exfiltration"
            },
            "correlation": {
                "entity_id": "transfer-sim-901",
                "entity_type": "transfer",
                "parent_id": None
            },
            "timeout_sec": None,
            "bytes_transferred_delta": 512,
            "details": {
                "channel": "dns_tunnel",
                "synthetic_payload_id": "synthetic_dataset_sample_42",
                "encoding_type": "base32_subdomain",
                "chunk_index": 0,
                "chunks_total": 20,
                "bytes_transferred_total": 512,
                "total_size_bytes": 10240,
                "effective_throughput_bps": 2400.0,
                "chunk_queries_count": 8
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p6-exfil-simulator",
                "inferred": False
            }
        },
        "transfer_completed": {
            "event_id": "550e8400-e29b-41d4-a716-446655440022",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:11:00.000Z",
            "received_at": None,
            "source": "p6_exfil",
            "type": "transfer_completed",
            "status": "completed",
            "host": {
                "host_id": "target-node-01",
                "ip": "10.0.10.15",
                "role": "target"
            },
            "destination": {
                "ip": "198.51.100.53",
                "port": 53,
                "protocol": "dns",
                "role": "exfil_receiver"
            },
            "technique": {
                "id": "exfil-tunnel-dns",
                "internal_name": "Simulated DNS Tunneling Exfiltration",
                "attack_id": "T1048.003",
                "attack_name": "Exfiltration Over Alternative Protocol: Exfiltration Over Unencrypted Non-C2 Protocol",
                "tactic": "Exfiltration"
            },
            "correlation": {
                "entity_id": "transfer-sim-901",
                "entity_type": "transfer",
                "parent_id": None
            },
            "timeout_sec": None,
            "bytes_transferred_delta": 512,
            "details": {
                "channel": "dns_tunnel",
                "synthetic_payload_id": "synthetic_dataset_sample_42",
                "total_bytes_transferred": 10240,
                "total_chunks_sent": 20,
                "total_duration_sec": 60.0,
                "effective_throughput_bps": 2730.0,
                "verification_hash": "sha256:synthetic_verified_ok"
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p6-exfil-simulator",
                "inferred": False
            }
        },
        "transfer_failed": {
            "event_id": "550e8400-e29b-41d4-a716-446655440023",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:12:00.000Z",
            "received_at": None,
            "source": "p6_exfil",
            "type": "transfer_failed",
            "status": "failed",
            "host": {
                "host_id": "target-node-01",
                "ip": "10.0.10.15",
                "role": "target"
            },
            "destination": {
                "ip": "198.51.100.53",
                "port": 53,
                "protocol": "dns",
                "role": "exfil_receiver"
            },
            "technique": {
                "id": "exfil-tunnel-dns",
                "internal_name": "Simulated DNS Tunneling Exfiltration",
                "attack_id": "T1048.003",
                "attack_name": "Exfiltration Over Alternative Protocol: Exfiltration Over Unencrypted Non-C2 Protocol",
                "tactic": "Exfiltration"
            },
            "correlation": {
                "entity_id": "transfer-sim-902",
                "entity_type": "transfer",
                "parent_id": None
            },
            "timeout_sec": None,
            "bytes_transferred_delta": 0,
            "details": {
                "channel": "dns_tunnel",
                "synthetic_payload_id": "synthetic_dataset_sample_42",
                "failure_reason": "rate_limited",
                "bytes_transferred_before_failure": 2048,
                "chunks_transferred_before_failure": 4
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p6-exfil-simulator",
                "inferred": False
            }
        },

        # --- P7 Analytics Events (5) ---
        "beacon_missed": {
            "event_id": "550e8400-e29b-41d4-a716-446655440030",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:20:00.000Z",
            "received_at": "2026-11-24T12:20:00.000Z",
            "source": "p7_analytics",
            "type": "beacon_missed",
            "status": "stalled",
            "host": {
                "host_id": "target-node-01",
                "ip": "10.0.10.15",
                "role": "target"
            },
            "destination": None,
            "technique": {
                "id": "c2-beacon-web",
                "internal_name": "Simulated Web Beaconing",
                "attack_id": "T1071.001",
                "attack_name": "Application Layer Protocol: Web Protocols",
                "tactic": "Command and Control"
            },
            "correlation": {
                "entity_id": "agent-c2-01",
                "entity_type": "agent",
                "parent_id": None
            },
            "timeout_sec": None,
            "bytes_transferred_delta": None,
            "details": {
                "trigger_condition": "beacon_heartbeat_timeout",
                "last_event_id": "550e8400-e29b-41d4-a716-446655440002",
                "elapsed_sec": 35.0,
                "threshold_sec": 30.0,
                "recovery_permitted": True
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p7-analytics-engine",
                "inferred": True
            }
        },
        "task_stalled": {
            "event_id": "550e8400-e29b-41d4-a716-446655440031",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:21:00.000Z",
            "received_at": "2026-11-24T12:21:00.000Z",
            "source": "p7_analytics",
            "type": "task_stalled",
            "status": "stalled",
            "host": {
                "host_id": "target-node-01",
                "ip": "10.0.10.15",
                "role": "target"
            },
            "destination": None,
            "technique": {
                "id": "c2-task-exec",
                "internal_name": "Simulated Command Execution Task",
                "attack_id": "T1059",
                "attack_name": "Command and Scripting Interpreter",
                "tactic": "Execution"
            },
            "correlation": {
                "entity_id": "task-c2-101",
                "entity_type": "task",
                "parent_id": "agent-c2-01"
            },
            "timeout_sec": None,
            "bytes_transferred_delta": None,
            "details": {
                "trigger_condition": "task_progress_timeout",
                "last_event_id": "550e8400-e29b-41d4-a716-446655440004",
                "elapsed_sec": 50.0,
                "threshold_sec": 45.0,
                "recovery_permitted": True
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p7-analytics-engine",
                "inferred": True
            }
        },
        "session_stalled": {
            "event_id": "550e8400-e29b-41d4-a716-446655440032",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:22:00.000Z",
            "received_at": "2026-11-24T12:22:00.000Z",
            "source": "p7_analytics",
            "type": "session_stalled",
            "status": "stalled",
            "host": {
                "host_id": "target-node-02",
                "ip": "10.0.10.35",
                "role": "target"
            },
            "destination": {
                "ip": "198.51.100.50",
                "port": 4444,
                "protocol": "tcp",
                "role": "operator_listener"
            },
            "technique": {
                "id": "shell-reverse-tcp",
                "internal_name": "Simulated Obfuscated TCP Reverse Shell",
                "attack_id": "T1059.004",
                "attack_name": "Command and Scripting Interpreter: Unix Shell",
                "tactic": "Execution"
            },
            "correlation": {
                "entity_id": "session-sim-501",
                "entity_type": "session",
                "parent_id": None
            },
            "timeout_sec": None,
            "bytes_transferred_delta": None,
            "details": {
                "trigger_condition": "session_idle_timeout",
                "last_event_id": "550e8400-e29b-41d4-a716-446655440013",
                "elapsed_sec": 65.0,
                "threshold_sec": 60.0,
                "recovery_permitted": True
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p7-analytics-engine",
                "inferred": True
            }
        },
        "transfer_stalled": {
            "event_id": "550e8400-e29b-41d4-a716-446655440033",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:23:00.000Z",
            "received_at": "2026-11-24T12:23:00.000Z",
            "source": "p7_analytics",
            "type": "transfer_stalled",
            "status": "stalled",
            "host": {
                "host_id": "target-node-01",
                "ip": "10.0.10.15",
                "role": "target"
            },
            "destination": {
                "ip": "198.51.100.53",
                "port": 53,
                "protocol": "dns",
                "role": "exfil_receiver"
            },
            "technique": {
                "id": "exfil-tunnel-dns",
                "internal_name": "Simulated DNS Tunneling Exfiltration",
                "attack_id": "T1048.003",
                "attack_name": "Exfiltration Over Alternative Protocol: Exfiltration Over Unencrypted Non-C2 Protocol",
                "tactic": "Exfiltration"
            },
            "correlation": {
                "entity_id": "transfer-sim-901",
                "entity_type": "transfer",
                "parent_id": None
            },
            "timeout_sec": None,
            "bytes_transferred_delta": None,
            "details": {
                "trigger_condition": "transfer_chunk_timeout",
                "last_event_id": "550e8400-e29b-41d4-a716-446655440021",
                "elapsed_sec": 50.0,
                "threshold_sec": 45.0,
                "recovery_permitted": True
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p7-analytics-engine",
                "inferred": True
            }
        },
        "timeout_expired": {
            "event_id": "550e8400-e29b-41d4-a716-446655440034",
            "schema_version": "1.0.0",
            "campaign_id": "campaign-alpha",
            "run_id": "run-01",
            "ts": "2026-11-24T12:25:00.000Z",
            "received_at": "2026-11-24T12:25:00.000Z",
            "source": "p7_analytics",
            "type": "timeout_expired",
            "status": "timeout",
            "host": {
                "host_id": "target-node-01",
                "ip": "10.0.10.15",
                "role": "target"
            },
            "destination": None,
            "technique": {
                "id": "c2-beacon-web",
                "internal_name": "Simulated Web Beaconing",
                "attack_id": "T1071.001",
                "attack_name": "Application Layer Protocol: Web Protocols",
                "tactic": "Command and Control"
            },
            "correlation": {
                "entity_id": "agent-c2-01",
                "entity_type": "agent",
                "parent_id": None
            },
            "timeout_sec": None,
            "bytes_transferred_delta": None,
            "details": {
                "trigger_condition": "grace_period_expired",
                "last_event_id": "550e8400-e29b-41d4-a716-446655440030",
                "total_elapsed_sec": 65.0,
                "grace_period_sec": 30.0,
                "recovery_permitted": False
            },
            "metadata": {
                "is_simulated": True,
                "generator": "p7-analytics-engine",
                "inferred": True
            }
        }
    }

@pytest.fixture
def canonical_events():
    return copy.deepcopy(CANONICAL_EVENTS_DATA)
