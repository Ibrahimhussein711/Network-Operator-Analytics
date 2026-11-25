"""
Clock abstraction for deterministic and testable time operations in Project 07.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone


class IClock(ABC):
    """Abstract interface for reading current system time."""

    @abstractmethod
    def now(self) -> datetime:
        """Returns current UTC timestamp."""
        pass


class SystemClock(IClock):
    """Production clock returning actual UTC system time."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class VirtualClock(IClock):
    """Test clock allowing explicit time advances without real sleeping."""

    def __init__(self, initial_time: datetime | None = None):
        self._current = initial_time or datetime(2026, 11, 24, 12, 0, 0, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self._current

    def advance(self, seconds: float) -> datetime:
        """Advance time by specified number of seconds."""
        from datetime import timedelta
        self._current += timedelta(seconds=seconds)
        return self._current

    def set_time(self, dt: datetime) -> None:
        """Set clock to an explicit timestamp."""
        self._current = dt
