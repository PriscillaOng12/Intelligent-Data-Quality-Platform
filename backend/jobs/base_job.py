"""Base class for scheduled jobs.

All long-running jobs in the platform should inherit from this class. It
encapsulates common initialisation logic such as connecting to the database
and reading configuration. The concrete `run` method should be implemented by
subclasses.
"""

from abc import ABC, abstractmethod

from sqlmodel import Session

from app.db.session import get_session


class BaseJob(ABC):
    """Abstract base class for jobs."""

    @abstractmethod
    def run(self) -> None:
        """Execute the job."""
        raise NotImplementedError

    def get_session(self) -> Session:
        """Helper to obtain a SQLModel session."""
        return next(get_session())