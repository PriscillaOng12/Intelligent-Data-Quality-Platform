"""Data quality orchestration service.

This service coordinates loading datasets, evaluating rules via the
`rule_engine` and persisting the results to the database. It also updates
Prometheus metrics counters for observability.
"""

import json
from pathlib import Path
from typing import Dict, List

import pandas as pd
from sqlmodel import Session, select

from app.db.models import CheckRun, Dataset, Incident, Rule
from app.services.rule_engine import evaluate_rule
from app.telemetry.metrics import record_check, record_incident


class QualityService:
    """Facade for running data quality checks on a dataset."""

    data_dir: Path = Path(__file__).resolve().parents[3] / "data" / "samples"

    def __init__(self, session: Session) -> None:
        self.session = session

    def load_dataset(self, dataset: Dataset) -> pd.DataFrame:
        """Load a dataset into a pandas DataFrame.

        The current implementation expects a CSV file under `data/samples`
        whose name matches the dataset's name. A real system would support
        reading from Delta or other storage.
        """

        file_path = self.data_dir / f"{dataset.name}.csv"
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file {file_path} not found")
        return pd.read_csv(file_path)

    def run_checks_for_dataset(self, dataset: Dataset) -> None:
        """Run all enabled rules for a given dataset and persist results."""

        df = self.load_dataset(dataset)
        statement = select(Rule).where(Rule.dataset_id == dataset.id, Rule.enabled == True)
        rules: List[Rule] = list(self.session.exec(statement))
        metrics: Dict[str, float] = {}
        for rule in rules:
            metric_value, passed, description = evaluate_rule(df, rule)
            metrics[f"{rule.id}:{rule.rule_type}"] = metric_value
            # Record Prometheus metrics
            record_check(dataset.name, rule.rule_type, 0.0)  # duration is trivial here
            if not passed:
                record_incident(dataset.name, rule.rule_type, rule.severity)
                incident = Incident(
                    dataset_id=dataset.id,
                    rule_id=rule.id,
                    metric_value=metric_value,
                    passed=passed,
                    severity=rule.severity,
                    description=description,
                )
                self.session.add(incident)
        # Persist CheckRun
        check_run = CheckRun(dataset_id=dataset.id, metrics=metrics)
        self.session.add(check_run)
        self.session.commit()