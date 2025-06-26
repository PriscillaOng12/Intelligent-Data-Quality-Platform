"""Spark-like quality checks implemented for local execution.

The real platform would leverage Apache Spark and Delta Lake to perform
distributed checks against large datasets. This module provides a fallback
implementation using pandas so that the checks can be exercised locally in
demo and test modes. The API mirrors what the Spark job exposes to keep
clients agnostic of the execution engine.
"""

from typing import Dict, List, Tuple

import pandas as pd

from app.db.models import Dataset, Rule
from app.services.rule_engine import evaluate_rule


def run_checks(
    df: pd.DataFrame, dataset: Dataset, rules: List[Rule]
) -> List[Tuple[Rule, float, bool, str]]:
    """Execute all rules against a DataFrame and return results.

    Each result in the returned list is a tuple `(rule, metric_value, passed, description)`.
    """

    results: List[Tuple[Rule, float, bool, str]] = []
    for rule in rules:
        metric_value, passed, description = evaluate_rule(df, rule)
        results.append((rule, metric_value, passed, description))
    return results