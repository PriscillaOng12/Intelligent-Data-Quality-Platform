<!-- markdownlint-disable MD041 -->
# Intelligent Data Quality Platform

The **Intelligent Data Quality Platform (IDQP)** is an end‑to‑end solution for
monitoring, evaluating and improving the quality of data flowing through your
pipelines. It provides a modular architecture consisting of a FastAPI
backend, a React front‑end, a Spark-based quality job, streaming via Kafka,
persistent storage in Postgres/Delta Lake and rich observability powered by
Prometheus and Grafana.

## Features

- **Comprehensive quality checks:** completeness, freshness, uniqueness,
  schema drift, distribution drift and outlier rate.
- **Rule management and alerting:** define rules via API or UI, store them in
  Postgres and trigger incidents when thresholds are violated.
- **Real‑time streaming support:** ingest events via Kafka/Redpanda or run in
  mock mode for demos.
- **Rich observability:** automatic Prometheus metrics and prebuilt Grafana
  dashboards covering API latencies, job durations and incident rates.
- **Secure by design:** JWT authentication with access/refresh tokens,
  role‑based access control (Owner/Maintainer/Reviewer/Viewer), rate limiting
  on sensitive endpoints and CORS configuration.
- **Production ready:** pinned dependencies, tests with ≥80 % coverage, CI
  pipelines for quality gates and container image scanning.
- **Demo mode:** one‑command start via `make demo` which seeds the database,
  generates synthetic data and exposes a running UI populated with sample
  incidents.

## Stack

| Layer        | Technology                                |
|--------------|--------------------------------------------|
| API backend  | Python 3.11, FastAPI, SQLModel, Uvicorn    |
| Data storage | Postgres, Delta Lake (via local Pandas)    |
| Streaming    | Kafka/Redpanda (optional in mock mode)     |
| Job engine   | Spark (simulated locally with Pandas)      |
| Front‑end    | React 18, Vite, TypeScript, Recharts       |
| Observability| Prometheus, Grafana                        |

## Quick start

The platform can be run entirely locally using Docker. Clone the repository,
ensure you have `docker` and `make` installed, then run:

```bash
make demo
```

This command performs the following actions:

1. Builds and starts all services defined in `infra/docker-compose.yml`.
2. Seeds Postgres with demo users, a sample dataset and a completeness rule.
3. Launches the FastAPI backend on <http://localhost:8000> and the React
   front‑end on <http://localhost:5173>.
4. Starts a synthetic data generator that appends data into Delta tables and
   triggers the quality job.
5. Exposes Prometheus at <http://localhost:9090> and Grafana at
   <http://localhost:3000> with preprovisioned dashboards.

After a few seconds you can navigate to the **Incidents** page in the UI to
inspect the automatically generated incident triggered by the completeness rule.

## API reference

The backend exposes a versioned REST API. The key endpoints are summarised
below. Full OpenAPI documentation is available at `/docs` when the backend is
running.

| Method | Endpoint                       | Description                                   |
|-------:|---------------------------------|-----------------------------------------------|
| POST   | `/auth/login`                  | Authenticate and obtain JWT tokens            |
| POST   | `/auth/refresh`                | Refresh your access token using a refresh token|
| GET    | `/datasets`                    | List all datasets                             |
| POST   | `/datasets`                    | Create a new dataset (Owner/Maintainer)       |
| GET    | `/rules`                       | List rules, optionally by dataset             |
| POST   | `/rules`                       | Create a new rule (Owner/Maintainer)          |
| GET    | `/incidents`                   | List incidents with filtering and pagination  |
| POST   | `/incidents/{id}/acknowledge`  | Acknowledge an incident                      |
| GET    | `/metrics`                     | Prometheus metrics endpoint                   |
| GET    | `/health`                      | Liveness probe                                |

## Architecture

The following Mermaid diagram illustrates the high‑level architecture of the
platform. The user interacts with the React front‑end which communicates with
the FastAPI backend. The backend writes to Postgres, pushes events onto
Kafka/Redpanda and exposes Prometheus metrics. A scheduled Spark job reads
datasets from Delta Lake, evaluates rules and persists incidents back to
Postgres. Grafana dashboards visualise metrics scraped from Prometheus.

```mermaid
%%{init: { 'theme': 'neutral' }}%%
```

The actual diagram lives in [`docs/images/architecture.mmd`](images/architecture.mmd). To view it
rendered, paste the contents of that file into any Mermaid live editor or
GitHub readme viewer.

## Contributing

Please use conventional commit messages. Run `make check` before pushing
changes. Pull requests that increase test coverage and improve documentation
are very welcome!