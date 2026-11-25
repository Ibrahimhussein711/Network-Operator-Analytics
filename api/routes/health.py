"""
Health and readiness endpoints for Project 07 Red Ingestion API.
Provides liveness and readiness probe routes for orchestration and monitoring.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response, status

from api.dependencies import get_event_repository
from api.responses import LivenessResponse, ReadinessResponse, StorageStats
from api.storage.interface import IEventRepository

router = APIRouter(prefix="/health", tags=["Health & Monitoring"])


@router.get(
    "/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Returns HTTP 200 when the API process is alive. Does not check dependencies.",
)
def get_liveness() -> LivenessResponse:
    """
    Lightweight liveness check.
    Indicates whether the process is alive without touching storage or external services.
    """
    return LivenessResponse(
        status="live",
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={
        status.HTTP_200_OK: {
            "model": ReadinessResponse,
            "description": "API and repository storage are ready to accept traffic.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ReadinessResponse,
            "description": "API is not ready; repository storage is unhealthy or unavailable.",
        },
    },
    summary="Readiness probe",
    description="Checks the health of the repository and returns readiness status with storage metrics.",
)
def get_readiness(
    response: Response,
    repo: IEventRepository = Depends(get_event_repository),
) -> ReadinessResponse:
    """
    Readiness probe.
    Queries the injected event repository for health and event count.
    Returns HTTP 200 if healthy, HTTP 503 if unhealthy.
    """
    is_healthy = repo.is_healthy()
    event_count = repo.count()
    current_time = datetime.now(timezone.utc)

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(
            status="unhealthy",
            timestamp=current_time,
            storage=StorageStats(
                type="in_memory",
                connected=False,
                event_count=event_count,
            ),
        )

    return ReadinessResponse(
        status="ready",
        timestamp=current_time,
        storage=StorageStats(
            type="in_memory",
            connected=True,
            event_count=event_count,
        ),
    )
