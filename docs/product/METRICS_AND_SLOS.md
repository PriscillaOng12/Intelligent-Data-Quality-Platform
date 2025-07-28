<!-- markdownlint-disable MD041 -->
# Metrics and SLOs

This document defines the key metrics and service‑level objectives (SLOs) for
the Intelligent Data Quality Platform. They are divided into platform SLOs
(measuring the reliability of the service itself) and product metrics
(measuring the value delivered to data stakeholders).

## Platform SLOs

| SLI                    | SLO                                   | Measurement & target                          |
|------------------------|---------------------------------------|-----------------------------------------------|
| API availability       | 99.9 % per month                      | Successful responses / total requests (HTTP 2xx / all) ≥ 0.999. |
| API latency (p95)      | ≤ 300 ms                              | Measure `http_request_duration_seconds` for the `/datasets`, `/incidents` endpoints; 95th percentile ≤ 0.3 s over 1 minute windows. |
| Job completion latency | ≤ 5 minutes                           | Time between scheduled start and finish of quality job runs should not exceed 5 minutes 95 % of the time. |
| Metrics freshness      | ≤ 60 seconds                          | Prometheus scrape interval ensures that dashboard panels reflect data within one minute of being emitted. |

Violations of these SLOs should trigger alerts (e.g. via Alertmanager) to the
on‑call team.

## Product metrics

| Metric                | Description                                                              |
|-----------------------|--------------------------------------------------------------------------|
| MTTD (Mean Time To Detect) | Average time between a data quality issue occurring and an incident being recorded. Lower is better. |
| MTTR (Mean Time To Resolve) | Average time between an incident being raised and the user acknowledging or closing it. |
| Coverage              | Proportion of mission‑critical datasets that have at least one active rule. |
| False positive rate   | Percentage of incidents that are acknowledged as non‑issues.              |
| Incident volume       | Number of incidents generated per day, split by severity and dataset.      |

These metrics should be tracked over time and reviewed during retrospectives.

## Measuring and reporting

All platform metrics are collected automatically via Prometheus. Product
metrics are derived from database records (incidents, acknowledgements) and
can be computed via scheduled reports or dashboards. The notebook
`03_anomaly_offline_eval.ipynb` and the accompanying report demonstrate how to
compute precision, recall and F‑scores for anomaly detectors offline; similar
analyses can be adapted to compute MTTD/MTTR from historic data.