"""
Synthetic event generator for Project 06 Exfiltration & Covert Channels.
Generates full simulated covert exfiltration operations: start, progress chunks, and completion/failure.
"""

from typing import Any, Dict, Optional
from uuid import uuid4

from .base import BaseSyntheticGenerator


class P6ExfilGenerator(BaseSyntheticGenerator):
    """Generates synthetic events modeling Project 06 covert exfiltration."""

    def __init__(
        self,
        campaign_id: str = "campaign-alpha",
        run_id: str = "run-01",
        host_id: str = "target-node-01",
        host_ip: str = "10.0.10.15",
        receiver_ip: str = "198.51.100.30",
        receiver_port: int = 53,
    ):
        super().__init__(
            campaign_id=campaign_id,
            run_id=run_id,
            host_id=host_id,
            host_ip=host_ip,
            generator_name="p6-exfil-simulator",
        )
        self.receiver_destination = {
            "ip": receiver_ip,
            "hostname": "exfil.exercise.local",
            "port": receiver_port,
            "protocol": "dns",
            "role": "exfil_receiver",
        }
        self.exfil_technique = {
            "id": "exfil-covert-dns",
            "internal_name": "Simulated DNS Tunneling Exfiltration",
            "attack_id": "T1048.003",
            "attack_name": "Exfiltration Over Alternative Protocol: DNS",
            "tactic": "Exfiltration",
        }

    def start_transfer(
        self,
        transfer_id: str,
        total_size: int = 10000,
        chunk_size: int = 1000,
        parent_id: Optional[str] = None,
        timeout_sec: int = 30,
    ) -> Dict[str, Any]:
        """Generates transfer_started event (status: running)."""
        chunks_total = (total_size + chunk_size - 1) // chunk_size
        correlation = {
            "entity_id": transfer_id,
            "entity_type": "transfer",
            "parent_id": parent_id,
        }
        details = {
            "channel": "dns_tunnel",
            "synthetic_payload_id": f"syn-payload-{transfer_id[:8]}",
            "encoding_type": "base32_subdomain",
            "total_size_bytes": total_size,
            "chunk_size_bytes": chunk_size,
            "chunks_total": chunks_total,
        }
        return self.create_envelope(
            source="p6_exfil",
            event_type="transfer_started",
            status="running",
            technique=self.exfil_technique,
            correlation=correlation,
            details=details,
            destination=self.receiver_destination,
            timeout_sec=timeout_sec,
        )

    def progress_transfer(
        self,
        transfer_id: str,
        chunk_index: int,
        chunks_total: int,
        bytes_transferred_total: int,
        total_size: int,
        bytes_delta: int = 1000,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generates transfer_progress event (status: running)."""
        correlation = {
            "entity_id": transfer_id,
            "entity_type": "transfer",
            "parent_id": parent_id,
        }
        details = {
            "channel": "dns_tunnel",
            "synthetic_payload_id": f"syn-payload-{transfer_id[:8]}",
            "encoding_type": "base32_subdomain",
            "chunk_index": chunk_index,
            "chunks_total": chunks_total,
            "bytes_transferred_total": bytes_transferred_total,
            "total_size_bytes": total_size,
            "effective_throughput_bps": 2400.0,
            "chunk_queries_count": 5,
        }
        return self.create_envelope(
            source="p6_exfil",
            event_type="transfer_progress",
            status="running",
            technique=self.exfil_technique,
            correlation=correlation,
            details=details,
            destination=self.receiver_destination,
            bytes_transferred_delta=bytes_delta,
        )

    def complete_transfer(
        self,
        transfer_id: str,
        total_size: int,
        chunks_total: int,
        duration_sec: float = 12.5,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generates transfer_completed event (status: completed)."""
        correlation = {
            "entity_id": transfer_id,
            "entity_type": "transfer",
            "parent_id": parent_id,
        }
        details = {
            "channel": "dns_tunnel",
            "synthetic_payload_id": f"syn-payload-{transfer_id[:8]}",
            "total_bytes_transferred": total_size,
            "total_chunks_sent": chunks_total,
            "total_duration_sec": duration_sec,
            "effective_throughput_bps": round((total_size * 8.0) / duration_sec, 2),
            "verification_hash": f"sha256-mock-{uuid4().hex[:16]}",
        }
        return self.create_envelope(
            source="p6_exfil",
            event_type="transfer_completed",
            status="completed",
            technique=self.exfil_technique,
            correlation=correlation,
            details=details,
            destination=self.receiver_destination,
            bytes_transferred_delta=total_size // chunks_total,
        )
