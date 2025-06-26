"""Schema registry utilities.

This module provides helper functions to persist dataset schemas to the
database and compare current schemas against the most recent registered
version. It is used to detect breaking schema changes (schema drift).
"""

import json
from typing import Dict, Tuple

import pandas as pd
from sqlmodel import Session, select

from app.db.models import Dataset, SchemaVersion


def serialise_schema(df: pd.DataFrame) -> Dict[str, str]:
    """Return a serialisable representation of a pandas DataFrame schema."""

    return {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)}


def register_schema(session: Session, dataset: Dataset, df: pd.DataFrame) -> SchemaVersion:
    """Persist the schema of a dataset as a new version."""

    latest_version = session.exec(
        select(SchemaVersion).where(SchemaVersion.dataset_id == dataset.id).order_by(SchemaVersion.version.desc())
    ).first()
    next_version = (latest_version.version + 1) if latest_version else 1
    schema_dict = serialise_schema(df)
    schema_version = SchemaVersion(
        dataset_id=dataset.id,
        version=next_version,
        schema=schema_dict,
    )
    session.add(schema_version)
    session.commit()
    return schema_version


def compare_schema(session: Session, dataset: Dataset, df: pd.DataFrame) -> Tuple[bool, Dict[str, str]]:
    """Compare the current DataFrame schema against the latest stored schema.

    Returns a tuple `(is_compatible, diff)` where `diff` describes the
    differences found. For now, any change in columns or dtypes is considered
    incompatible.
    """

    latest_version = session.exec(
        select(SchemaVersion).where(SchemaVersion.dataset_id == dataset.id).order_by(SchemaVersion.version.desc())
    ).first()
    current_schema = serialise_schema(df)
    if latest_version is None:
        return True, {}
    stored_schema: Dict[str, str] = latest_version.schema
    diff = {}
    # Detect new or removed columns
    for col in current_schema.keys() - stored_schema.keys():
        diff[col] = f"Added column {col} of type {current_schema[col]}"
    for col in stored_schema.keys() - current_schema.keys():
        diff[col] = f"Removed column {col} (was type {stored_schema[col]})"
    # Detect type changes
    for col in current_schema.keys() & stored_schema.keys():
        if current_schema[col] != stored_schema[col]:
            diff[col] = f"Type changed from {stored_schema[col]} to {current_schema[col]}"
    is_compatible = len(diff) == 0
    return is_compatible, diff