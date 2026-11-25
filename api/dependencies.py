import secrets
from typing import Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from .config import EnvironmentEnum, IngestionSettings, settings
from .storage.interface import IEventRepository
from .storage.memory import ThreadSafeInMemoryEventRepository
from engine.clock import IClock, SystemClock
from engine.tracker import LifecycleTracker
from engine.watchdog import WatchdogEngine

# Header extraction: X-API-Key (auto_error=False to allow custom validation handling)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Singleton instances for the application lifespan
_repository_instance: Optional[IEventRepository] = None
_tracker_instance: Optional[LifecycleTracker] = None
_watchdog_instance: Optional[WatchdogEngine] = None
_clock_instance: Optional[IClock] = None

def get_event_repository() -> IEventRepository:
    """Dependency provider returning the event repository instance."""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = ThreadSafeInMemoryEventRepository()
    return _repository_instance

def get_lifecycle_tracker() -> LifecycleTracker:
    """Dependency provider returning the lifecycle tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = LifecycleTracker()
    return _tracker_instance

def get_system_clock() -> IClock:
    """Dependency provider returning the active clock."""
    global _clock_instance
    if _clock_instance is None:
        _clock_instance = SystemClock()
    return _clock_instance

def set_system_clock(clock: IClock) -> None:
    """Allows setting the active clock instance (e.g. for testing)."""
    global _clock_instance, _watchdog_instance
    _clock_instance = clock
    if _watchdog_instance is not None:
        _watchdog_instance._clock = clock

def get_watchdog_engine() -> WatchdogEngine:
    """Dependency provider returning the watchdog engine instance."""
    global _watchdog_instance
    if _watchdog_instance is None:
        _watchdog_instance = WatchdogEngine(
            repository=get_event_repository(),
            tracker=get_lifecycle_tracker(),
            clock=get_system_clock(),
        )
    return _watchdog_instance

def reset_event_repository(clock: Optional[IClock] = None) -> None:
    """Utility for testing teardown/isolation."""
    global _repository_instance, _tracker_instance, _watchdog_instance, _clock_instance
    _repository_instance = ThreadSafeInMemoryEventRepository()
    _tracker_instance = LifecycleTracker()
    _clock_instance = clock or SystemClock()
    _watchdog_instance = WatchdogEngine(
        repository=_repository_instance,
        tracker=_tracker_instance,
        clock=_clock_instance,
    )

def get_settings() -> IngestionSettings:
    """Dependency provider returning the active configuration settings."""
    return settings

def verify_api_key(
    header_key: Optional[str] = Security(api_key_header),
    app_settings: IngestionSettings = Depends(get_settings),
) -> Optional[str]:
    """
    Validates the X-API-Key request header against configured settings.

    Invariants:
    1. If app_settings.API_KEY_REQUIRED is False (development/testing only), authentication passes.
    2. If app_settings.API_KEY_REQUIRED is True:
       - If header_key is missing: raises HTTP 401 Unauthorized.
       - If header_key is invalid: raises HTTP 401 Unauthorized.
       - Uses secrets.compare_digest for constant-time comparison to prevent timing attacks.
    3. Never exposes, reflects, or logs the expected API key.
    """
    if not app_settings.API_KEY_REQUIRED:
        return None

    if not header_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required API key header (X-API-Key)."
        )

    # Constant-time comparison
    is_valid = secrets.compare_digest(header_key, app_settings.API_KEY)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key provided."
        )

    return header_key
