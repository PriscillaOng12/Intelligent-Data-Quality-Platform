"""Time utilities."""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current UTC time with timezone information."""

    return datetime.now(timezone.utc)