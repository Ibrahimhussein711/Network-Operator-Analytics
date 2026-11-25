"""
Base class and HTTP submission utilities for Synthetic Event Generators.
Enforces strict synthetic safety constraints: no real shells, subprocesses, or live network calls.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
import httpx

from models.envelope import CommonEventEnvelope


class BaseSyntheticGenerator:
    """Base class for all synthetic event stream generators."""

    def __init__(
        self,
        campaign_id: str = "campaign-synthetic-alpha",
        run_id: str = "run-01",
        host_id: str = "target-node-01",
        host_ip: str = "10.0.10.15",
        generator_name: str = "synthetic-generator",
    ):
        self.campaign_id = campaign_id
        self.run_id = run_id
        self.host_id = host_id
        self.host_ip = host_ip
        self.generator_name = generator_name

    def create_envelope(
        self,
        source: str,
        event_type: str,
        status: str,
        technique: Dict[str, Any],
        correlation: Dict[str, Any],
        details: Dict[str, Any],
        destination: Optional[Dict[str, Any]] = None,
        timeout_sec: Optional[float] = None,
        bytes_transferred_delta: Optional[int] = None,
        ts: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Constructs an envelope dictionary adhering strictly to the canonical contract."""
        event_time = ts or datetime.now(timezone.utc)
        return {
            "event_id": str(uuid4()),
            "schema_version": "1.0.0",
            "campaign_id": self.campaign_id,
            "run_id": self.run_id,
            "ts": event_time.isoformat(),
            "received_at": None,  # Will be assigned upon API ingestion
            "source": source,
            "type": event_type,
            "status": status,
            "host": {
                "host_id": self.host_id,
                "ip": self.host_ip,
                "hostname": f"{self.host_id}.lab",
                "role": "target",
            },
            "destination": destination,
            "technique": technique,
            "correlation": correlation,
            "timeout_sec": timeout_sec,
            "bytes_transferred_delta": bytes_transferred_delta,
            "details": details,
            "metadata": {
                "is_simulated": True,
                "generator": self.generator_name,
                "inferred": False,
            },
        }

    @staticmethod
    def submit_event(
        event_dict: Dict[str, Any],
        api_url: str = "http://127.0.0.1:8000",
        api_key: Optional[str] = None,
        timeout: float = 5.0,
    ) -> httpx.Response:
        """Submits an individual event via HTTP to the ingestion API."""
        headers = {}
        if api_key:
            headers["X-API-Key"] = api_key
        url = f"{api_url.rstrip('/')}/api/v1/events"
        return httpx.post(url, json=event_dict, headers=headers, timeout=timeout)

    @staticmethod
    def submit_batch(
        events: List[Dict[str, Any]],
        api_url: str = "http://127.0.0.1:8000",
        api_key: Optional[str] = None,
        timeout: float = 10.0,
    ) -> httpx.Response:
        """Submits a batch of events via HTTP to the ingestion API."""
        headers = {}
        if api_key:
            headers["X-API-Key"] = api_key
        url = f"{api_url.rstrip('/')}/api/v1/events/batch"
        return httpx.post(url, json=events, headers=headers, timeout=timeout)
