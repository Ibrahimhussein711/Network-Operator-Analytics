"""
Synthetic event generator for Project 05 Reverse & Bind Shells.
Generates full simulated interactive shell sessions: request, establish, activity, and close.
"""

from typing import Any, Dict, Optional
from uuid import uuid4

from .base import BaseSyntheticGenerator


class P5ShellGenerator(BaseSyntheticGenerator):
    """Generates synthetic events modeling Project 05 interactive shells."""

    def __init__(
        self,
        campaign_id: str = "campaign-alpha",
        run_id: str = "run-01",
        host_id: str = "target-node-01",
        host_ip: str = "10.0.10.15",
        operator_ip: str = "198.51.100.20",
        operator_port: int = 4444,
    ):
        super().__init__(
            campaign_id=campaign_id,
            run_id=run_id,
            host_id=host_id,
            host_ip=host_ip,
            generator_name="p5-shell-simulator",
        )
        self.operator_destination = {
            "ip": operator_ip,
            "hostname": "listener.exercise.local",
            "port": operator_port,
            "protocol": "tcp",
            "role": "operator_listener",
        }
        self.shell_technique = {
            "id": "shell-reverse-tcp",
            "internal_name": "Simulated Reverse TCP Shell",
            "attack_id": "T1059.004",
            "attack_name": "Command and Scripting Interpreter: Unix Shell",
            "tactic": "Execution",
        }

    def request_connection(
        self,
        session_id: str,
        parent_id: Optional[str] = None,
        timeout_sec: int = 15,
    ) -> Dict[str, Any]:
        """Generates connection_requested event (status: pending)."""
        correlation = {
            "entity_id": session_id,
            "entity_type": "session",
            "parent_id": parent_id,
        }
        details = {
            "shell_technique": "tcp_reverse",
            "shell_environment": "posix",
            "is_obfuscated": False,
            "encoding_type": "plain_utf8",
        }
        return self.create_envelope(
            source="p5_shell",
            event_type="connection_requested",
            status="pending",
            technique=self.shell_technique,
            correlation=correlation,
            details=details,
            destination=self.operator_destination,
            timeout_sec=timeout_sec,
        )

    def establish_connection(
        self,
        session_id: str,
        parent_id: Optional[str] = None,
        timeout_sec: int = 60,
    ) -> Dict[str, Any]:
        """Generates connection_established event (status: running)."""
        correlation = {
            "entity_id": session_id,
            "entity_type": "session",
            "parent_id": parent_id,
        }
        details = {
            "shell_technique": "tcp_reverse",
            "shell_environment": "posix",
            "is_obfuscated": False,
            "encoding_type": "plain_utf8",
            "handshake_duration_ms": 120,
            "interactive_prompt_ready": True,
        }
        return self.create_envelope(
            source="p5_shell",
            event_type="connection_established",
            status="running",
            technique=self.shell_technique,
            correlation=correlation,
            details=details,
            destination=self.operator_destination,
            timeout_sec=timeout_sec,
        )

    def record_activity(
        self,
        session_id: str,
        command_count: int = 1,
        uptime_sec: int = 10,
        parent_id: Optional[str] = None,
        bytes_delta: int = 256,
    ) -> Dict[str, Any]:
        """Generates session_activity event (status: running)."""
        correlation = {
            "entity_id": session_id,
            "entity_type": "session",
            "parent_id": parent_id,
        }
        details = {
            "shell_technique": "tcp_reverse",
            "shell_environment": "posix",
            "is_obfuscated": False,
            "encoding_type": "plain_utf8",
            "command_label": "simulate_query_os_version",
            "command_count_cumulative": command_count,
            "session_uptime_sec": uptime_sec,
        }
        return self.create_envelope(
            source="p5_shell",
            event_type="session_activity",
            status="running",
            technique=self.shell_technique,
            correlation=correlation,
            details=details,
            destination=self.operator_destination,
            bytes_transferred_delta=bytes_delta,
        )

    def close_session(
        self,
        session_id: str,
        total_duration_sec: int = 35,
        total_commands: int = 3,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generates session_closed event (status: completed)."""
        correlation = {
            "entity_id": session_id,
            "entity_type": "session",
            "parent_id": parent_id,
        }
        details = {
            "shell_technique": "tcp_reverse",
            "shell_environment": "posix",
            "exit_reason": "operator_exit",
            "total_session_duration_sec": total_duration_sec,
            "total_commands_executed": total_commands,
        }
        return self.create_envelope(
            source="p5_shell",
            event_type="session_closed",
            status="completed",
            technique=self.shell_technique,
            correlation=correlation,
            details=details,
            destination=self.operator_destination,
        )
