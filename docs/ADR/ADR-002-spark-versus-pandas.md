<!-- markdownlint-disable MD041 -->
# ADR‑002: Spark vs Pandas for Quality Checks

## Status

Accepted – 2025‑08‑11

## Context

Data quality checks need to operate over potentially large datasets. The
original requirement specified Apache Spark and Delta Lake as the processing
engine and storage layer. For local development and demo mode, however, we do
not always have a Spark runtime available. We needed to decide whether to
depend on Spark exclusively or provide a fallback implementation.

## Decision

The quality job is designed with an abstraction layer (`spark_checks.py`) that
invokes rule evaluation functions. In production, this module can call
Spark DataFrame operations against Delta tables. In demo mode, we implement
the same API using **pandas** to run checks in process on small CSV files.

## Consequences

- Developers can run the entire platform locally without installing Spark.
- The rule engine lives in `services/rule_engine.py` and can be reused by
  both the pandas and Spark implementations.
- The semantics of Spark operations (null handling, distinct counting) must be
  carefully mirrored in pandas to avoid drift between environments.
- When scaling to large datasets in production, we will need to implement
  distributed checks and integrate with Delta Lake as originally intended.