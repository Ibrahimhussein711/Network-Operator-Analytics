"""
API route definitions for Project 07 Red Ingestion API.
"""

from .analytics import router as analytics_router
from .events import router as events_router
from .health import router as health_router

__all__ = ["health_router", "events_router", "analytics_router"]
