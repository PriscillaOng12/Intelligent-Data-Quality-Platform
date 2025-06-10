"""Database models using SQLModel.

The data quality platform persists all state using SQLModel/SQLAlchemy. These
classes represent the main entities of the system, including users, datasets,
rules for data quality checks, the results of those checks and the incidents
raised when rules are violated.

For brevity, relationships are kept simple; foreign keys are defined but
explicit relationship attributes are omitted unless used. SQLModel supports
declarative relationships if needed.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Application user with role-based access control."""

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    full_name: str
    password_hash: str
    role: str = Field(default="Viewer")  # Owner, Maintainer, Reviewer, Viewer
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Dataset(SQLModel, table=True):
    """A logical grouping of data for which quality checks can be defined."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    owner_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Rule(SQLModel, table=True):
    """A data quality rule defines a metric and threshold to evaluate."""

    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="dataset.id")
    rule_type: str  # completeness, freshness, uniqueness, schema_drift, distribution_drift, outlier_rate
    params: Dict[str, Any] = Field(sa_column_kwargs={"type_": "JSON"})
    threshold: float
    severity: str  # info, warning, critical
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Incident(SQLModel, table=True):
    """Represents a rule violation detected by a quality check."""

    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="dataset.id")
    rule_id: int = Field(foreign_key="rule.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metric_value: float
    passed: bool = Field(default=False)
    severity: str
    description: str
    acknowledged: bool = Field(default=False)


class CheckRun(SQLModel, table=True):
    """Capture metrics from a single run of quality checks for a dataset."""

    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="dataset.id")
    run_at: datetime = Field(default_factory=datetime.utcnow)
    metrics: Dict[str, Any] = Field(sa_column_kwargs={"type_": "JSON"})


class SchemaVersion(SQLModel, table=True):
    """Persist snapshots of dataset schemas for drift detection."""

    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="dataset.id")
    version: int
    schema: Dict[str, Any] = Field(sa_column_kwargs={"type_": "JSON"})
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Acknowledgement(SQLModel, table=True):
    """Track when incidents are acknowledged by users."""

    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.id")
    user_id: int = Field(foreign_key="user.id")
    comment: Optional[str] = None
    acknowledged_at: datetime = Field(default_factory=datetime.utcnow)