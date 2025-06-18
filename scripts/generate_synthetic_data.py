"""Synthetic data generator for demo mode.

This script appends random data to the sample dataset at regular intervals.
It simulates batch or streaming ingestion by writing rows to a CSV file in
`data/samples`. Use the command line options to control the generation
frequency and characteristics of the data (e.g. proportion of nulls or
outliers).
"""

import argparse
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def generate_row(null_ratio: float, outlier_ratio: float) -> dict:
    """Generate a single data row with optional nulls and outliers."""

    value: float | None
    # Determine if this row should be null
    if random.random() < null_ratio:
        value = None
    else:
        # Generate a normal value or an outlier
        if random.random() < outlier_ratio:
            value = random.gauss(0, 1) * 8  # outlier scale
        else:
            value = random.gauss(5, 1)
    timestamp = datetime.now(timezone.utc).isoformat()
    return {"value": value, "timestamp": timestamp}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic data for the IDQP demo")
    parser.add_argument(
        "--dataset",
        type=str,
        default="sample_dataset",
        help="Name of the dataset (CSV file without extension) to append to",
    )
    parser.add_argument("--interval", type=float, default=5.0, help="Seconds between batch inserts")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of rows per batch")
    parser.add_argument("--null-ratio", type=float, default=0.05, help="Fraction of rows with null values")
    parser.add_argument("--outlier-ratio", type=float, default=0.02, help="Fraction of rows that are outliers")
    args = parser.parse_args()
    data_dir = Path(__file__).resolve().parents[1] / "data" / "samples"
    file_path = data_dir / f"{args.dataset}.csv"
    print(f"Appending synthetic data to {file_path} every {args.interval}s")
    # Ensure the file exists with headers
    if not file_path.exists():
        df = pd.DataFrame(columns=["value", "timestamp"])
        df.to_csv(file_path, index=False)
    while True:
        rows = [generate_row(args.null_ratio, args.outlier_ratio) for _ in range(args.batch_size)]
        df = pd.DataFrame(rows)
        df.to_csv(file_path, mode="a", header=False, index=False)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()