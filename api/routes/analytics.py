"""
Analytics and campaign discovery endpoints for Project 07 Red Analytics.
Provides high-level operational statistics, entity inspectors, and campaign summaries.
"""

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict

from api.dependencies import (
    get_event_repository,
    get_lifecycle_tracker,
    get_system_clock,
    get_watchdog_engine,
)
from api.storage.interface import IEventRepository
from engine.clock import IClock
from engine.tracker import LifecycleTracker, EntityState
from engine.watchdog import WatchdogEngine
from models.envelope import CommonEventEnvelope

router = APIRouter(prefix="", tags=["Analytics & Reporting"])


class EntitySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entity_id: str
    entity_type: str
    parent_id: Optional[str]
    campaign_id: str
    run_id: str
    current_status: str
    is_terminal: bool
    is_stalled: bool
    is_established: bool
    timeout_sec: Optional[float]
    first_seen_ts: datetime
    last_seen_ts: datetime
    last_received_at: datetime
    bytes_transferred_total: int
    event_count: int


class AnalyticsOverviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    timestamp: datetime
    campaign_id: Optional[str] = None
    run_id: Optional[str] = None
    total_events: int
    events_by_source: Dict[str, int]
    events_by_type: Dict[str, int]
    entities: Dict[str, int]
    stalled_count: int
    timeout_count: int


class AlertItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alert_id: str
    alert_type: str
    severity: str
    campaign_id: str
    run_id: str
    entity_id: str
    entity_type: str
    event_id: str
    first_detected_at: datetime
    last_updated_at: datetime
    current_status: str
    is_recovered: bool
    recovered_at: Optional[datetime]
    is_timeout: bool
    timeout_at: Optional[datetime]
    message: str


class AlertsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    active: List[AlertItem]
    resolved: List[AlertItem]
    historical: List[AlertItem]
    total_active: int
    total_resolved: int
    total_historical: int


class RunMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str
    total_events: int
    events_by_source: Dict[str, int]
    events_by_type: Dict[str, int]
    unique_entities: int
    entities_by_type: Dict[str, int]
    technique_ids: List[str]
    completed_entities: int
    failed_entities: int
    stalled_entities: int
    recovered_count: int
    total_alerts: int
    bytes_transferred: int
    duration_sec: Optional[float]


class RunComparisonResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    campaign_id: str
    run_a: RunMetrics
    run_b: RunMetrics
    differences: Dict[str, Any]
    generated_at: datetime


class CampaignReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    campaign_id: str
    generated_at: datetime
    runs: List[str]
    total_events: int
    events_by_source: Dict[str, int]
    events_by_type: Dict[str, int]
    total_agents: int
    total_tasks: int
    total_sessions: int
    total_transfers: int
    bytes_transferred_total: int
    stalled_incidents: int
    timeout_failures: int
    entities: List[EntitySummary]


# ==============================================================================
# CAMPAIGN AND RUN DISCOVERY
# ==============================================================================

@router.get("/campaigns", response_model=List[str], summary="List distinct campaigns")
def list_campaigns(
    repo: IEventRepository = Depends(get_event_repository),
) -> List[str]:
    """Returns all campaign IDs present in event storage."""
    return repo.get_campaigns()


@router.get(
    "/campaigns/{campaign_id}/runs",
    response_model=List[str],
    summary="List runs for campaign",
)
def list_runs(
    campaign_id: str,
    repo: IEventRepository = Depends(get_event_repository),
) -> List[str]:
    """Returns all run IDs for the specified campaign."""
    return repo.get_runs(campaign_id)


# ==============================================================================
# ANALYTICS OVERVIEW
# ==============================================================================

@router.get(
    "/analytics/overview",
    response_model=AnalyticsOverviewResponse,
    summary="Get operational overview analytics",
)
def get_analytics_overview(
    campaign_id: Optional[str] = Query(None, description="Optional campaign scope"),
    run_id: Optional[str] = Query(None, description="Optional run scope"),
    repo: IEventRepository = Depends(get_event_repository),
    tracker: LifecycleTracker = Depends(get_lifecycle_tracker),
) -> AnalyticsOverviewResponse:
    """Calculates operational metrics across sources, types, and entity lifecycles."""
    events = repo.query_events(
        campaign_id=campaign_id,
        run_id=run_id,
        limit=10000,
    )

    source_counter = Counter(ev.source for ev in events)
    type_counter = Counter(ev.type for ev in events)

    entities = tracker.get_all_entities(campaign_id=campaign_id, run_id=run_id)

    stalled_count = sum(1 for e in entities if e.is_stalled)
    timeout_count = sum(1 for e in entities if e.current_status == "timeout")

    active_agents = sum(1 for e in entities if e.entity_type == "agent" and not e.is_terminal)
    active_tasks = sum(1 for e in entities if e.entity_type == "task" and not e.is_terminal)
    active_sessions = sum(1 for e in entities if e.entity_type == "session" and not e.is_terminal)
    active_transfers = sum(1 for e in entities if e.entity_type == "transfer" and not e.is_terminal)

    return AnalyticsOverviewResponse(
        timestamp=datetime.now(timezone.utc),
        campaign_id=campaign_id,
        run_id=run_id,
        total_events=len(events),
        events_by_source=dict(source_counter),
        events_by_type=dict(type_counter),
        entities={
            "total": len(entities),
            "active_agents": active_agents,
            "active_tasks": active_tasks,
            "active_sessions": active_sessions,
            "active_transfers": active_transfers,
        },
        stalled_count=stalled_count,
        timeout_count=timeout_count,
    )


# ==============================================================================
# ENTITY STATE INSPECTOR
# ==============================================================================

@router.get(
    "/analytics/entities",
    response_model=List[EntitySummary],
    summary="Inspect tracked entity states",
)
def get_entities(
    campaign_id: Optional[str] = Query(None),
    run_id: Optional[str] = Query(None),
    tracker: LifecycleTracker = Depends(get_lifecycle_tracker),
) -> List[EntitySummary]:
    """Returns detailed state summaries of tracked entities."""
    entities = tracker.get_all_entities(campaign_id=campaign_id, run_id=run_id)
    return [
        EntitySummary(
            entity_id=e.entity_id,
            entity_type=e.entity_type,
            parent_id=e.parent_id,
            campaign_id=e.campaign_id,
            run_id=e.run_id,
            current_status=e.current_status,
            is_terminal=e.is_terminal,
            is_stalled=e.is_stalled,
            is_established=e.is_established,
            timeout_sec=e.timeout_sec,
            first_seen_ts=e.first_seen_ts,
            last_seen_ts=e.last_seen_ts,
            last_received_at=e.last_received_at,
            bytes_transferred_total=e.bytes_transferred_total,
            event_count=len(e.history_event_ids),
        )
        for e in entities
    ]


# ==============================================================================
# CAMPAIGN REPORT
# ==============================================================================

@router.get(
    "/analytics/campaigns/{campaign_id}/report",
    response_model=CampaignReportResponse,
    summary="Generate comprehensive campaign report",
)
def get_campaign_report(
    campaign_id: str,
    repo: IEventRepository = Depends(get_event_repository),
    tracker: LifecycleTracker = Depends(get_lifecycle_tracker),
) -> CampaignReportResponse:
    """Generates an executive campaign report summarizing events, entities, and outcomes."""
    runs = repo.get_runs(campaign_id)
    events = repo.query_events(campaign_id=campaign_id, limit=10000)
    entities = tracker.get_all_entities(campaign_id=campaign_id)

    source_counter = Counter(ev.source for ev in events)
    type_counter = Counter(ev.type for ev in events)

    total_agents = sum(1 for e in entities if e.entity_type == "agent")
    total_tasks = sum(1 for e in entities if e.entity_type == "task")
    total_sessions = sum(1 for e in entities if e.entity_type == "session")
    total_transfers = sum(1 for e in entities if e.entity_type == "transfer")
    bytes_transferred = sum(e.bytes_transferred_total for e in entities)

    stalled_incidents = sum(1 for e in entities if e.is_stalled)
    timeout_failures = sum(1 for e in entities if e.current_status == "timeout")

    entity_summaries = [
        EntitySummary(
            entity_id=e.entity_id,
            entity_type=e.entity_type,
            parent_id=e.parent_id,
            campaign_id=e.campaign_id,
            run_id=e.run_id,
            current_status=e.current_status,
            is_terminal=e.is_terminal,
            is_stalled=e.is_stalled,
            is_established=e.is_established,
            timeout_sec=e.timeout_sec,
            first_seen_ts=e.first_seen_ts,
            last_seen_ts=e.last_seen_ts,
            last_received_at=e.last_received_at,
            bytes_transferred_total=e.bytes_transferred_total,
            event_count=len(e.history_event_ids),
        )
        for e in entities
    ]

    return CampaignReportResponse(
        campaign_id=campaign_id,
        generated_at=datetime.now(timezone.utc),
        runs=runs,
        total_events=len(events),
        events_by_source=dict(source_counter),
        events_by_type=dict(type_counter),
        total_agents=total_agents,
        total_tasks=total_tasks,
        total_sessions=total_sessions,
        total_transfers=total_transfers,
        bytes_transferred_total=bytes_transferred,
        stalled_incidents=stalled_incidents,
        timeout_failures=timeout_failures,
        entities=entity_summaries,
    )


# ==============================================================================
# ALERTS CENTER
# ==============================================================================

@router.get(
    "/analytics/alerts",
    response_model=AlertsResponse,
    summary="Get categorized alerts (active, resolved, historical)",
)
def get_alerts(
    campaign_id: Optional[str] = Query(None, description="Optional campaign filter"),
    run_id: Optional[str] = Query(None, description="Optional run filter"),
    severity: Optional[str] = Query(None, description="Optional severity filter (warning, critical)"),
    tracker: LifecycleTracker = Depends(get_lifecycle_tracker),
) -> AlertsResponse:
    """Returns active, resolved, and historical alerts across entities."""
    raw_alerts = tracker.get_alerts(
        campaign_id=campaign_id,
        run_id=run_id,
        severity=severity,
    )

    alert_items = [
        AlertItem(
            alert_id=a.alert_id,
            alert_type=a.alert_type,
            severity=a.severity,
            campaign_id=a.campaign_id,
            run_id=a.run_id,
            entity_id=a.entity_id,
            entity_type=a.entity_type,
            event_id=a.event_id,
            first_detected_at=a.first_detected_at,
            last_updated_at=a.last_updated_at,
            current_status=a.current_status,
            is_recovered=a.is_recovered,
            recovered_at=a.recovered_at,
            is_timeout=a.is_timeout,
            timeout_at=a.timeout_at,
            message=a.message,
        )
        for a in raw_alerts
    ]

    active = [a for a in alert_items if a.current_status == "active"]
    resolved = [a for a in alert_items if a.current_status == "resolved"]
    historical = [a for a in alert_items if a.current_status in ("timed_out", "completed", "failed")]

    return AlertsResponse(
        active=active,
        resolved=resolved,
        historical=historical,
        total_active=len(active),
        total_resolved=len(resolved),
        total_historical=len(historical),
    )


# ==============================================================================
# WATCHDOG EVALUATION TRIGGER
# ==============================================================================

@router.post(
    "/watchdogs/trigger",
    response_model=List[CommonEventEnvelope],
    summary="Trigger watchdog evaluation cycle",
)
def trigger_watchdogs(
    campaign_id: Optional[str] = Query(None, description="Optional campaign scope"),
    run_id: Optional[str] = Query(None, description="Optional run scope"),
    engine: WatchdogEngine = Depends(get_watchdog_engine),
) -> List[CommonEventEnvelope]:
    """Manually triggers a watchdog evaluation cycle and returns newly emitted P7 events."""
    return engine.check_watchdogs(campaign_id=campaign_id, run_id=run_id)


# ==============================================================================
# RUN COMPARISON ENDPOINT
# ==============================================================================

@router.get(
    "/campaigns/{campaign_id}/compare",
    response_model=RunComparisonResponse,
    summary="Compare two exercise runs within a campaign",
)
@router.get(
    "/analytics/campaigns/{campaign_id}/compare",
    response_model=RunComparisonResponse,
    include_in_schema=False,
)
def compare_runs(
    campaign_id: str,
    run_a: str = Query(..., description="First run ID to compare"),
    run_b: str = Query(..., description="Second run ID to compare"),
    repo: IEventRepository = Depends(get_event_repository),
    tracker: LifecycleTracker = Depends(get_lifecycle_tracker),
) -> RunComparisonResponse:
    """Computes comparative telemetry, entity outcomes, and technique coverage between two runs."""

    def _calc_run_metrics(rid: str) -> RunMetrics:
        events = repo.query_events(campaign_id=campaign_id, run_id=rid, limit=10000)
        entities = tracker.get_entities_for_run(campaign_id, rid)
        alerts = tracker.get_alerts(campaign_id=campaign_id, run_id=rid)

        source_counter = Counter(ev.source for ev in events)
        type_counter = Counter(ev.type for ev in events)
        ent_type_counter = Counter(e.entity_type for e in entities)
        tech_ids = sorted(list({ev.technique.id for ev in events if ev.technique and ev.technique.id}))

        completed = sum(1 for e in entities if e.current_status == "completed")
        failed = sum(1 for e in entities if e.current_status in ("failed", "timeout"))
        stalled = sum(1 for e in entities if e.is_stalled)
        recovered = sum(1 for a in alerts if a.is_recovered)
        bytes_total = sum(e.bytes_transferred_total for e in entities)

        duration = None
        if len(events) >= 2:
            duration = round((max(ev.ts for ev in events) - min(ev.ts for ev in events)).total_seconds(), 2)

        return RunMetrics(
            run_id=rid,
            total_events=len(events),
            events_by_source=dict(source_counter),
            events_by_type=dict(type_counter),
            unique_entities=len(entities),
            entities_by_type=dict(ent_type_counter),
            technique_ids=tech_ids,
            completed_entities=completed,
            failed_entities=failed,
            stalled_entities=stalled,
            recovered_count=recovered,
            total_alerts=len(alerts),
            bytes_transferred=bytes_total,
            duration_sec=duration,
        )

    metrics_a = _calc_run_metrics(run_a)
    metrics_b = _calc_run_metrics(run_b)

    diffs = {
        "event_count_delta": metrics_b.total_events - metrics_a.total_events,
        "unique_entities_delta": metrics_b.unique_entities - metrics_a.unique_entities,
        "completed_entities_delta": metrics_b.completed_entities - metrics_a.completed_entities,
        "failed_entities_delta": metrics_b.failed_entities - metrics_a.failed_entities,
        "stalled_entities_delta": metrics_b.stalled_entities - metrics_a.stalled_entities,
        "alerts_delta": metrics_b.total_alerts - metrics_a.total_alerts,
        "bytes_transferred_delta": metrics_b.bytes_transferred - metrics_a.bytes_transferred,
        "new_techniques_in_run_b": [t for t in metrics_b.technique_ids if t not in metrics_a.technique_ids],
    }

    return RunComparisonResponse(
        campaign_id=campaign_id,
        run_a=metrics_a,
        run_b=metrics_b,
        differences=diffs,
        generated_at=datetime.now(timezone.utc),
    )


# ==============================================================================
# DEMO CONTROLS ENDPOINT
# ==============================================================================

@router.post(
    "/demo/inject",
    summary="Inject pre-packaged synthetic demonstration scenario",
)
def inject_demo_scenario(
    scenario: str = Query("normal", description="Scenario type: normal, agent_stalled, task_stalled, handshake_timeout, session_stalled, transfer_stalled, mixed"),
    campaign_id: Optional[str] = Query(None),
    run_id: Optional[str] = Query(None),
    repo: IEventRepository = Depends(get_event_repository),
    tracker: LifecycleTracker = Depends(get_lifecycle_tracker),
    clock: IClock = Depends(get_system_clock),
) -> Dict[str, Any]:
    from synthetic.scenarios import (
        generate_normal_scenario,
        generate_agent_stalled_scenario,
        generate_task_stalled_scenario,
        generate_session_handshake_timeout_scenario,
        generate_established_session_stalled_scenario,
        generate_transfer_stalled_scenario,
        generate_mixed_campaign_scenario,
        generate_stalled_scenario,
    )
    from api.hashing import compute_canonical_payload_hash
    from uuid import uuid4

    cid = campaign_id or f"demo-{scenario.replace('_', '-')}-{uuid4().hex[:6]}"
    rid = run_id or "run-01"

    builders = {
        "normal": generate_normal_scenario,
        "agent_stalled": generate_agent_stalled_scenario,
        "task_stalled": generate_task_stalled_scenario,
        "handshake_timeout": generate_session_handshake_timeout_scenario,
        "session_stalled": generate_established_session_stalled_scenario,
        "transfer_stalled": generate_transfer_stalled_scenario,
        "mixed": generate_mixed_campaign_scenario,
        "stalled": generate_stalled_scenario,
    }

    builder = builders.get(scenario, generate_normal_scenario)
    raw_events = builder(campaign_id=cid, run_id=rid)

    now = clock.now()
    ingested = 0
    for raw in raw_events:
        raw["received_at"] = now.isoformat()
        raw["ts"] = now.isoformat()
        ev = CommonEventEnvelope.model_validate(raw)
        h = compute_canonical_payload_hash(ev)
        repo.save_if_absent(ev, h)
        tracker.process_event(ev)
        ingested += 1

    return {
        "status": "success",
        "scenario": scenario,
        "campaign_id": cid,
        "run_id": rid,
        "events_injected": ingested,
    }
