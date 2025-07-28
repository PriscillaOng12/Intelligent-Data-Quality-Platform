<!-- markdownlint-disable MD041 -->
# Runbook

This runbook outlines common operational procedures for the Intelligent Data
Quality Platform. It is intended for on‑call engineers and administrators.

## Service overview

The platform consists of a FastAPI backend, a scheduled quality job, a React
front‑end and supporting services (Postgres, Kafka/Redpanda, Prometheus and
Grafana). The backend exposes REST endpoints on port 8000 and metrics on
port 8000 under `/metrics`. The job can be run manually via `make spark-job`
or configured as a cron task in production.

## Daily checks

- Verify that the backend and database containers are healthy:

  ```bash
  docker compose -f infra/docker-compose.yml ps
  ```

- Confirm that Prometheus is scraping targets and Grafana dashboards are
  updating. Inspect the **API Latency** and **Incident Rate** panels for
  anomalies.

- Ensure that synthetic data generation (in demo mode) is writing to
  `data/delta` and that the job is ingesting it.

## Rotating secrets

1. Generate a new random secret for `SECRET_KEY`.
2. Update `.env` (or the secrets store in production) and restart the backend.
3. Invalidate existing tokens by updating the token version in the database or
   by changing the signing key prefix.

## Adding a new dataset

1. Place the source data in `data/delta/<dataset_name>` (Delta) or
   `data/samples/<dataset_name>.csv` for local testing.
2. Create the dataset via the API:

   ```bash
   curl -XPOST -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "new_dataset", "description": "..."}' \
     http://localhost:8000/datasets
   ```

3. Define rules for the dataset using the UI or `/rules` endpoint.
4. Run the job manually (`make spark-job`) or wait for the next scheduled run.

## Tuning thresholds

Adjusting rule thresholds impacts the sensitivity of quality checks. When tuning:

- Review historical metric distributions in the **Checks Run** dashboard.
- Start with loose thresholds to avoid false positives, then tighten them
  gradually.
- Document threshold changes in version control via pull requests.

## Handling high incident volume

If you observe a sudden spike in incidents:

1. Check the **Incidents by Severity** panel for context.
2. Use the **Incidents** page to filter by dataset and rule type.
3. Determine whether the spike is due to an actual data problem or a bad rule
   configuration (e.g. overly strict threshold).
4. Temporarily **mute** or disable the offending rule via the UI or API until
   the underlying cause is addressed.
5. Document your actions in the on‑call log and create a follow‑up task.

## Troubleshooting

- **Backend returns 500 errors** – Check the backend logs (`docker compose logs backend`) for stack traces. Inspect the database connection and apply migrations if needed.
- **Job does not write incidents** – Ensure that the dataset file exists and that rules are enabled. Run the job manually and monitor logs.
- **Metrics endpoint unreachable** – Verify that the backend is running on port 8000 and that `/metrics` is not behind authentication. Check firewall rules.
- **Grafana shows no data** – Confirm that Prometheus is scraping the backend and job; restart Prometheus if the scrape configuration changed.