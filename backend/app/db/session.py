"""Database session and engine initialisation.

This module encapsulates the SQLModel engine and session creation for use
throughout the application. It exposes a dependency for FastAPI endpoints to
obtain a session with proper lifecycle management.
"""

from contextlib import contextmanager
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings


# Create the SQLModel engine using the configured database URL. By default this
# uses a synchronous engine, which is sufficient for the current scope. For
# production workloads an asynchronous engine could be considered.
engine = create_engine(settings.database_url, echo=False)


def init_db() -> None:
    """Initialise the database by creating all tables if they do not exist.

    This function should be called at application start-up. It will ensure
    that all SQLModel models registered with the metadata have their tables
    created in the target database. In a production system you would use
    alembic or another migration tool instead of auto-creating tables.
    """

    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Yield a new database session within a context manager.

    This function is designed to be used as a dependency in FastAPI routes:

    ```python
    @app.get("/datasets")
    def read_datasets(*, session: Session = Depends(get_session)):
        ...
    ```

    It will open a session at the beginning of the request and commit/close
    it automatically when the request finishes.
    """

    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()