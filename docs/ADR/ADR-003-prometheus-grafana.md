<!-- markdownlint-disable MD041 -->
# ADR‑003: Prometheus and Grafana for Observability

## Status

Accepted – 2025‑08‑11

## Context

The platform must expose health information and performance characteristics to
operations engineers. We needed a metrics collection and visualisation
solution that is open source, widely adopted, easy to run locally and in
Kubernetes, and integrates well with Python and Spark.

## Decision

We selected **Prometheus** for metrics scraping and storage, and **Grafana**
for dashboarding. The backend uses `prometheus_client` to expose metrics at
`/metrics`. Grafana is provisioned with dashboards that visualise API latency,
error rates, check durations and incident counts.

## Consequences

- Prometheus and Grafana run as part of the Docker Compose stack and require
  minimal configuration. They can be extended with alerting rules (Alertmanager)
  and additional data sources.
- Metrics are pulled by Prometheus; there is no need to push metrics from
  services unless we adopt a Pushgateway for batch jobs.
- Grafana dashboards are stored as JSON in the repository, enabling easy
  version control and updates via pull requests.
- Teams already familiar with alternative tools (e.g. Datadog, New Relic)
  will need to adapt; however the underlying concepts (counters, histograms,
  panels, alerts) remain the same.