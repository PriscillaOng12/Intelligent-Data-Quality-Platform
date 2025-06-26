"""Entry point for running data quality checks outside of the API.

This script can be invoked manually or scheduled via cron/Kubernetes. It will
load datasets and rules from the database, execute the quality checks using
the local `QualityService`, persist the results and update Prometheus
metrics. It supports running once or continuously in a loop.
"""

import argparse
import time

from sqlmodel import Session, select

from app.db.models import Dataset
from app.db.session import get_session
from app.services.quality_service import QualityService


def run_once(dataset_name: str | None = None) -> None:
    """Run quality checks once for all or a single dataset."""

    with get_session() as session:
        service = QualityService(session)
        if dataset_name:
            dataset = session.exec(select(Dataset).where(Dataset.name == dataset_name)).first()
            if not dataset:
                raise ValueError(f"Dataset {dataset_name} not found")
            service.run_checks_for_dataset(dataset)
        else:
            for dataset in session.exec(select(Dataset)).all():
                service.run_checks_for_dataset(dataset)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run data quality checks")
    parser.add_argument("--dataset", type=str, default=None, help="Name of a single dataset to check")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run checks once and exit (default is continuous every 60 seconds)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Interval in seconds between continuous runs",
    )
    args = parser.parse_args()
    if args.once:
        run_once(args.dataset)
    else:
        while True:
            run_once(args.dataset)
            time.sleep(args.interval)


if __name__ == "__main__":
    main()