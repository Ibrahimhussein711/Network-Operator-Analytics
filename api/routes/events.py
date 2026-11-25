"""
Event ingestion and query routes for Project 07 Red Ingestion API.
Implements single event ingestion, batch ingestion, query, and campaign/run discovery.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, Response, Security, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from api.config import IngestionSettings, settings
from api.dependencies import (
    get_event_repository,
    get_lifecycle_tracker,
    get_settings,
    get_system_clock,
    verify_api_key,
)
from api.hashing import compute_canonical_payload_hash
from api.responses import (
    BatchIngestionResponse,
    BatchItemOutcome,
    ErrorDetail,
    ErrorResponse,
    EventIngestedResponse,
)
from api.storage.interface import IEventRepository, IngestionResultStatus
from engine.clock import IClock
from engine.tracker import LifecycleTracker
from models.envelope import CommonEventEnvelope

router = APIRouter(prefix="/events", tags=["Events & Ingestion"])


# ==============================================================================
# SINGLE EVENT INGESTION
# ==============================================================================

@router.post(
    "",
    response_model=EventIngestedResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "model": EventIngestedResponse,
            "description": "Event newly created and stored.",
        },
        status.HTTP_200_OK: {
            "model": EventIngestedResponse,
            "description": "Duplicate event accepted idempotently without mutation.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Malformed JSON payload.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Missing or invalid API key.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Event ID conflict with different payload hash.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ErrorResponse,
            "description": "Schema validation failure or external P7 source rejection.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "Storage backend unavailable.",
        },
    },
    summary="Ingest a single canonical event",
)
async def ingest_event(
    request: Request,
    response: Response,
    _auth: Optional[str] = Security(verify_api_key),
    repo: IEventRepository = Depends(get_event_repository),
    tracker: LifecycleTracker = Depends(get_lifecycle_tracker),
    clock: IClock = Depends(get_system_clock),
) -> Union[EventIngestedResponse, JSONResponse]:
    """
    Ingests an individual canonical event from upstream simulators (P4, P5, P6).
    Applies authoritative receipt timestamp, schema validation, canonical hashing,
    and atomic idempotency.
    """
    now = clock.now()

    # 0. Parse JSON body directly
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error="Bad Request",
                message="Malformed JSON payload.",
                timestamp=now,
            ).model_dump(mode="json"),
        )

    if not isinstance(payload, dict):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error="Unprocessable Entity",
                message="Event payload must be a JSON object.",
                timestamp=now,
            ).model_dump(mode="json"),
        )

    # 1. Reject external submission of internal P7 analytics events
    if payload.get("source") == "p7_analytics":
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error="Unprocessable Entity",
                message="Event source 'p7_analytics' is internally generated and cannot be accepted through external ingestion.",
                timestamp=now,
            ).model_dump(mode="json"),
        )

    # 2. Assign authoritative receipt time BEFORE validation
    payload["received_at"] = now.isoformat()

    # 3. Formally validate envelope against canonical Pydantic model
    try:
        event = CommonEventEnvelope.model_validate(payload)
    except ValidationError as err:
        error_details = [
            ErrorDetail(loc=list(e["loc"]), msg=e["msg"], type=e["type"])
            for e in err.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error="Validation Error",
                message="Event envelope failed schema validation.",
                timestamp=now,
                details=error_details,
            ).model_dump(mode="json"),
        )

    # 4. Check repository health
    if not repo.is_healthy():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ErrorResponse(
                error="Service Unavailable",
                message="Event repository storage is currently unavailable.",
                timestamp=now,
            ).model_dump(mode="json"),
        )

    # 5. Deterministic canonical hash computation
    payload_hash = compute_canonical_payload_hash(event)

    # 6. Atomic save_if_absent
    outcome = repo.save_if_absent(event, payload_hash)

    if outcome.status == IngestionResultStatus.CREATED:
        # Feed event to correlation and lifecycle tracker
        tracker.process_event(event)
        response.status_code = status.HTTP_201_CREATED
        return EventIngestedResponse(
            status="accepted",
            event_id=event.event_id,
            received_at=event.received_at,
            message="Event successfully ingested and stored.",
        )

    elif outcome.status == IngestionResultStatus.DUPLICATE:
        # Return original stored event details and 200 OK
        response.status_code = status.HTTP_200_OK
        return EventIngestedResponse(
            status="deduplicated",
            event_id=outcome.stored_event.event_id,
            received_at=outcome.stored_event.received_at,
            message="Duplicate event ignored; existing record retained.",
        )

    elif outcome.status == IngestionResultStatus.CONFLICT:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                error="Conflict",
                message="Event ID already exists with different payload hash.",
                timestamp=now,
                event_id=event.event_id,
            ).model_dump(mode="json"),
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Error",
            message="Unexpected repository outcome status.",
            timestamp=now,
        ).model_dump(mode="json"),
    )


# ==============================================================================
# BATCH EVENT INGESTION
# ==============================================================================

@router.post(
    "/batch",
    response_model=BatchIngestionResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": BatchIngestionResponse,
            "description": "Batch processed; contains per-item acceptance and failure details.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ErrorResponse,
            "description": "Batch limit exceeded or batch structure invalid.",
        },
    },
    summary="Ingest a batch of canonical events",
)
async def ingest_batch(
    request: Request,
    _auth: Optional[str] = Security(verify_api_key),
    app_settings: IngestionSettings = Depends(get_settings),
    repo: IEventRepository = Depends(get_event_repository),
    tracker: LifecycleTracker = Depends(get_lifecycle_tracker),
    clock: IClock = Depends(get_system_clock),
) -> Union[BatchIngestionResponse, JSONResponse]:
    """
    Ingests a batch of events independently.
    Failures in individual events do not abort processing of valid events.
    """
    now = clock.now()

    # 0. Parse JSON body directly
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error="Bad Request",
                message="Malformed JSON payload in batch.",
                timestamp=now,
            ).model_dump(mode="json"),
        )

    # Normalize input
    if isinstance(body, dict):
        raw_items = body.get("events", [])
    elif isinstance(body, list):
        raw_items = body
    else:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error="Unprocessable Entity",
                message="Batch payload must be a list of events or an object containing an 'events' list.",
                timestamp=now,
            ).model_dump(mode="json"),
        )

    # Enforce batch size limit
    if len(raw_items) > app_settings.MAX_BATCH_SIZE:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error="Unprocessable Entity",
                message=f"Batch size {len(raw_items)} exceeds maximum allowed limit of {app_settings.MAX_BATCH_SIZE}.",
                timestamp=now,
            ).model_dump(mode="json"),
        )

    total_submitted = len(raw_items)
    accepted_count = 0
    deduplicated_count = 0
    failed_count = 0
    results: List[BatchItemOutcome] = []

    for item in raw_items:
        if not isinstance(item, dict):
            failed_count += 1
            results.append(
                BatchItemOutcome(
                    event_id=None,
                    outcome="failed",
                    http_status=422,
                    error="Item must be a JSON object.",
                )
            )
            continue

        item_event_id_raw = item.get("event_id")
        item_uuid: Optional[UUID] = None
        if item_event_id_raw:
            try:
                item_uuid = UUID(str(item_event_id_raw))
            except ValueError:
                item_uuid = None

        # Disallow P7
        if item.get("source") == "p7_analytics":
            failed_count += 1
            results.append(
                BatchItemOutcome(
                    event_id=item_uuid,
                    outcome="failed",
                    http_status=422,
                    error="Event source 'p7_analytics' is not accepted on external ingestion.",
                )
            )
            continue

        # Set authoritative receipt time
        item["received_at"] = now.isoformat()

        # Validate
        try:
            event = CommonEventEnvelope.model_validate(item)
        except ValidationError as val_err:
            failed_count += 1
            results.append(
                BatchItemOutcome(
                    event_id=item_uuid,
                    outcome="failed",
                    http_status=422,
                    error=f"Schema validation failed: {val_err.errors()[0]['msg']}",
                )
            )
            continue

        # Storage health
        if not repo.is_healthy():
            failed_count += 1
            results.append(
                BatchItemOutcome(
                    event_id=event.event_id,
                    outcome="failed",
                    http_status=503,
                    error="Storage backend unavailable.",
                )
            )
            continue

        # Hash & Save
        payload_hash = compute_canonical_payload_hash(event)
        outcome = repo.save_if_absent(event, payload_hash)

        if outcome.status == IngestionResultStatus.CREATED:
            tracker.process_event(event)
            accepted_count += 1
            results.append(
                BatchItemOutcome(
                    event_id=event.event_id,
                    outcome="accepted",
                    http_status=201,
                    received_at=event.received_at,
                )
            )
        elif outcome.status == IngestionResultStatus.DUPLICATE:
            deduplicated_count += 1
            results.append(
                BatchItemOutcome(
                    event_id=outcome.stored_event.event_id,
                    outcome="deduplicated",
                    http_status=200,
                    received_at=outcome.stored_event.received_at,
                )
            )
        elif outcome.status == IngestionResultStatus.CONFLICT:
            failed_count += 1
            results.append(
                BatchItemOutcome(
                    event_id=event.event_id,
                    outcome="failed",
                    http_status=409,
                    error="Event ID conflict: existing event has different payload hash.",
                )
            )

    return BatchIngestionResponse(
        total_submitted=total_submitted,
        accepted_count=accepted_count,
        deduplicated_count=deduplicated_count,
        failed_count=failed_count,
        results=results,
    )


# ==============================================================================
# EVENT QUERY AND RETRIEVAL
# ==============================================================================

@router.get(
    "",
    response_model=List[CommonEventEnvelope],
    summary="Query stored events with filtering",
)
def query_events(
    campaign_id: Optional[str] = Query(None, description="Filter by campaign ID"),
    run_id: Optional[str] = Query(None, description="Filter by run ID"),
    source: Optional[str] = Query(None, description="Filter by source (e.g. p4_c2, p5_shell)"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    entity_id: Optional[str] = Query(None, description="Filter by correlation entity ID"),
    limit: int = Query(100, ge=1, le=1000, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    repo: IEventRepository = Depends(get_event_repository),
) -> List[CommonEventEnvelope]:
    """Retrieves stored events matching filters in deterministic chronological order."""
    return repo.query_events(
        campaign_id=campaign_id,
        run_id=run_id,
        source=source,
        event_type=event_type,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{event_id}",
    response_model=CommonEventEnvelope,
    summary="Retrieve single event by ID",
)
def get_event_by_id(
    event_id: UUID,
    repo: IEventRepository = Depends(get_event_repository),
) -> CommonEventEnvelope:
    """Retrieves an individual stored event by UUID."""
    event = repo.get_by_id(event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID '{event_id}' not found.",
        )
    return event
