"""
Synthetic event generator for Project 04 C2 Framework.
Generates full simulated C2 lifecycles: registration, beacon check-ins, tasks, and completion/failure.
"""

from typing import Any, Dict, List, Optional
from uuid import uuid4

from .base import BaseSyntheticGenerator


class P4C2Generator(BaseSyntheticGenerator):
    """Generates synthetic events modeling Project 04 C2 operations."""

    def __init__(
        self,
        campaign_id: str = "campaign-alpha",
        run_id: str = "run-01",
        host_id: str = "target-node-01",
        host_ip: str = "10.0.10.15",
        c2_ip: str = "198.51.100.10",
        c2_port: int = 443,
    ):
        super().__init__(
            campaign_id=campaign_id,
            run_id=run_id,
            host_id=host_id,
            host_ip=host_ip,
            generator_name="p4-c2-simulator",
        )
        self.c2_destination = {
            "ip": c2_ip,
            "hostname": "c2.exercise.local",
            "port": c2_port,
            "protocol": "https",
            "role": "c2_server",
        }
        self.c2_technique = {
            "id": "c2-beacon-web",
            "internal_name": "Simulated Web Beaconing",
            "attack_id": "T1071.001",
            "attack_name": "Application Layer Protocol: Web Protocols",
            "tactic": "Command and Control",
        }

    def register_agent(
        self,
        agent_id: str,
        beacon_interval_sec: int = 10,
        jitter_percent: int = 15,
        timeout_sec: int = 30,
    ) -> Dict[str, Any]:
        """Generates an agent_registered event."""
        correlation = {
            "entity_id": agent_id,
            "entity_type": "agent",
            "parent_id": None,
        }
        details = {
            "channel": "https",
            "agent_version": "1.0.0",
            "beacon_interval_sec": beacon_interval_sec,
            "jitter_percent": jitter_percent,
            "encryption_scheme": "xor_static",
            "supported_executors": ["simulated_posix", "internal_simulator"],
        }
        return self.create_envelope(
            source="p4_c2",
            event_type="agent_registered",
            status="running",
            technique=self.c2_technique,
            correlation=correlation,
            details=details,
            destination=self.c2_destination,
            timeout_sec=timeout_sec,
        )

    def beacon_checkin(
        self,
        agent_id: str,
        counter: int = 1,
        latency_ms: int = 35,
        tasks_pending: int = 0,
        timeout_sec: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generates a beacon_checkin event."""
        correlation = {
            "entity_id": agent_id,
            "entity_type": "agent",
            "parent_id": None,
        }
        details = {
            "channel": "https",
            "beacon_counter": counter,
            "latency_ms": latency_ms,
            "tasks_pending_count": tasks_pending,
            "active_jitter_sec": 1.5,
        }
        return self.create_envelope(
            source="p4_c2",
            event_type="beacon_checkin",
            status="running",
            technique=self.c2_technique,
            correlation=correlation,
            details=details,
            destination=self.c2_destination,
            timeout_sec=timeout_sec,
        )

    def start_task(
        self,
        agent_id: str,
        task_id: str,
        timeout_sec: int = 60,
    ) -> Dict[str, Any]:
        """Generates a task_started event (simulated host inventory)."""
        correlation = {
            "entity_id": task_id,
            "entity_type": "task",
            "parent_id": agent_id,
        }
        technique = {
            "id": "c2-exec-inventory",
            "internal_name": "Simulated Discovery Execution",
            "attack_id": "T1082",
            "attack_name": "System Information Discovery",
            "tactic": "Discovery",
        }
        details = {
            "channel": "https",
            "action_label": "simulate_host_inventory",
            "task_parameters": {
                "scope": "system",
                "detail_level": "basic",
            },
            "executor": "simulated_posix",
        }
        return self.create_envelope(
            source="p4_c2",
            event_type="task_started",
            status="running",
            technique=technique,
            correlation=correlation,
            details=details,
            destination=self.c2_destination,
            timeout_sec=timeout_sec,
        )

    def progress_task(
        self,
        agent_id: str,
        task_id: str,
        progress_percent: int = 50,
        bytes_delta: int = 1024,
    ) -> Dict[str, Any]:
        """Generates a task_progress event."""
        correlation = {
            "entity_id": task_id,
            "entity_type": "task",
            "parent_id": agent_id,
        }
        technique = {
            "id": "c2-exec-inventory",
            "internal_name": "Simulated Discovery Execution",
            "attack_id": "T1082",
            "attack_name": "System Information Discovery",
            "tactic": "Discovery",
        }
        details = {
            "progress_percent": progress_percent,
            "output_chunk_index": 1,
            "partial_output_len": bytes_delta,
            "total_size_bytes": bytes_delta * 2,
            "bytes_transferred_total": bytes_delta,
        }
        return self.create_envelope(
            source="p4_c2",
            event_type="task_progress",
            status="running",
            technique=technique,
            correlation=correlation,
            details=details,
            destination=self.c2_destination,
            bytes_transferred_delta=bytes_delta,
        )

    def complete_task(
        self,
        agent_id: str,
        task_id: str,
        duration_ms: int = 2500,
        output_bytes: int = 2048,
    ) -> Dict[str, Any]:
        """Generates a task_completed event (terminal status)."""
        correlation = {
            "entity_id": task_id,
            "entity_type": "task",
            "parent_id": agent_id,
        }
        technique = {
            "id": "c2-exec-inventory",
            "internal_name": "Simulated Discovery Execution",
            "attack_id": "T1082",
            "attack_name": "System Information Discovery",
            "tactic": "Discovery",
        }
        details = {
            "exit_code": 0,
            "execution_duration_ms": duration_ms,
            "output_summary": "Simulated host inventory completed successfully.",
            "total_output_bytes": output_bytes,
            "bytes_transferred_total": output_bytes,
        }
        return self.create_envelope(
            source="p4_c2",
            event_type="task_completed",
            status="completed",
            technique=technique,
            correlation=correlation,
            details=details,
            destination=self.c2_destination,
            bytes_transferred_delta=output_bytes // 2,
        )
