<!-- markdownlint-disable MD041 -->
# Observability

Observability is essential for understanding the behaviour of a data quality
platform. This document describes the metrics emitted by the backend and the
quality job, how they are collected and visualised, and how to extend the
system with additional metrics and dashboards.

## Metrics overview

The platform uses the [`prometheus_client`](https://github.com/prometheus/client_python)
library to expose metrics. Metrics are partitioned into two domains:

### API metrics

| Metric name                      | Type      | Labels                         | Description                                   |
|---------------------------------|-----------|--------------------------------|------------------------------------------------|
| `http_requests_total`           | Counter   | `method`, `endpoint`, `status` | Counts every HTTP request by method, endpoint and status code. |
| `http_request_duration_seconds` | Histogram | `method`, `endpoint`           | Measures request latency in seconds.           |
| `http_request_errors_total`     | Counter   | `method`, `endpoint`, `status` | Counts non‑200 responses (4xx/5xx).           |

### Job metrics

| Metric name               | Type      | Labels                     | Description                                                   |
|---------------------------|-----------|----------------------------|---------------------------------------------------------------|
| `checks_run_total`        | Counter   | `dataset`, `rule_type`     | Number of checks executed.                                   |
| `check_duration_seconds`  | Histogram | `dataset`, `rule_type`     | Duration of a check execution in seconds.                    |
| `incidents_total`         | Counter   | `dataset`, `rule_type`, `severity` | Number of incidents raised grouped by dataset and severity. |

The `/metrics` endpoint on the backend exposes these metrics in Prometheus
text exposition format. Prometheus scrapes this endpoint at the interval
specified in `infra/prometheus/prometheus.yml`.

## Grafana dashboards

A sample Grafana dashboard is provisioned in
`infra/grafana/dashboards/data_quality_overview.json`. It includes panels
covering:

- API latency percentiles (`http_request_duration_seconds` p50/p95/p99)
- Error rate over time (`http_request_errors_total`)
- Checks executed per dataset (`checks_run_total`)
- Incidents by severity (`incidents_total`)
- Freshness SLA breaches (derived from job metrics)

The dashboard is automatically imported when Grafana starts via the
provisioning configuration in `infra/grafana/provisioning/`. A screenshot of
the main dashboard is shown below:

![Grafana dashboard](images/grafana_dashboard_screenshot.png)

## Adding a new metric

To add a new metric to the backend or job:

1. **Define** the metric in `backend/app/telemetry/metrics.py`. Choose the
   appropriate Prometheus metric type (Counter, Gauge, Histogram, Summary)
   and add meaningful labels.
2. **Instrument** the code path that should update the metric. For
   example, if you add a gauge to track the number of active sessions,
   increment and decrement it in the login and logout handlers.
3. **Update** the Grafana dashboard JSON to include a new panel that queries
   the metric. Save the updated JSON back into
   `infra/grafana/dashboards/data_quality_overview.json` so that it is
   provisioned on startup.

Refer to the [Prometheus documentation](https://prometheus.io/docs/introduction/overview/)
and [Grafana documentation](https://grafana.com/docs/grafana/latest/) for
additional guidance.