"""Rule evaluation logic.

This module contains the core functions that compute data quality metrics and
determine whether a rule passes or fails. The implementation here uses
pandas to operate on small datasets loaded into memory. In a production
system, the `spark_checks.py` job would replace these functions with
distributed Spark operations against Delta tables.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from app.db.models import Rule


def evaluate_rule(df: pd.DataFrame, rule: Rule) -> Tuple[float, bool, str]:
    """Evaluate a data quality rule against a DataFrame.

    Returns a tuple of `(metric_value, passed, description)`.
    """

    rule_type = rule.rule_type.lower()
    params: Dict[str, Any] = rule.params or {}

    if rule_type == "completeness":
        column = params.get("column")
        if column not in df.columns:
            return 1.0, False, f"Column '{column}' missing"
        null_ratio = df[column].isna().mean()
        passed = null_ratio <= rule.threshold
        return null_ratio, passed, f"Null ratio for {column}: {null_ratio:.3f}"

    if rule_type == "freshness":
        column = params.get("timestamp_column")
        if column not in df.columns:
            return float("inf"), False, f"Timestamp column '{column}' missing"
        # Assume column is datetime-like
        max_ts = pd.to_datetime(df[column]).max()
        now = datetime.now(timezone.utc)
        age_minutes = (now - max_ts).total_seconds() / 60.0
        passed = age_minutes <= rule.threshold
        return age_minutes, passed, f"Max age {age_minutes:.1f} minutes"

    if rule_type == "uniqueness":
        keys = params.get("primary_key")
        if isinstance(keys, str):
            keys = [keys]
        if not keys or any(k not in df.columns for k in keys):
            return 1.0, False, "Primary key column(s) missing"
        duplicates = df.duplicated(subset=keys).mean()
        passed = duplicates <= rule.threshold
        return duplicates, passed, f"Duplicate ratio for {keys}: {duplicates:.3f}"

    if rule_type == "schema_drift":
        # Schema drift detection is handled in the job via schema_registry
        return 0.0, True, "Schema drift check not implemented in rule engine"

    if rule_type == "distribution_drift":
        # Simplistic distribution drift: compare mean to reference mean
        column = params.get("column")
        reference_mean = params.get("reference_mean")
        if column not in df.columns or reference_mean is None:
            return 0.0, True, "Distribution drift check incomplete"
        mean = df[column].mean()
        drift = abs(mean - reference_mean)
        passed = drift <= rule.threshold
        return drift, passed, f"Mean drift for {column}: {drift:.3f}"

    if rule_type == "outlier_rate":
        column = params.get("column")
        if column not in df.columns:
            return 1.0, False, f"Column '{column}' missing"
        vals = df[column].dropna()
        if vals.empty:
            return 0.0, True, "No data to compute outliers"
        z_scores = np.abs((vals - vals.mean()) / vals.std(ddof=0))
        outlier_rate = (z_scores > 3).mean()
        passed = outlier_rate <= rule.threshold
        return outlier_rate, passed, f"Outlier rate for {column}: {outlier_rate:.3f}"

    return 0.0, True, f"Unknown rule type '{rule_type}'"