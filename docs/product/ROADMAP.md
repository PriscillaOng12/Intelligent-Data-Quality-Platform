<!-- markdownlint-disable MD041 -->
# Roadmap

The roadmap outlines the near‑term and longer‑term plans for the Intelligent
Data Quality Platform. Dates are illustrative relative to project kick‑off.

## 30‑day goals (Month 1)

- **Usability improvements:** refine the UI based on initial feedback;
  add loading indicators and empty states.
- **Distribution drift check:** implement PSI calculation for numeric and
  categorical columns and integrate it into the rule engine.
- **Outlier detection:** support configurable z‑score and IQR methods as
  first‑class rule types.
- **Alert channels:** integrate with Slack via webhook for incident
  notifications; configurable per rule.
- **Improved seeding:** allow multiple synthetic datasets with different
  patterns (missing values, duplicates, outliers).

## 60‑day goals (Month 2)

- **Streaming integration:** replace the pandas mock with a Redpanda/Kafka
  consumer producing structured events into Delta; ensure idempotent
  processing.
- **Schema drift:** enforce schema registration and automatically run schema
  compatibility checks on ingestion; support optional blocking mode.
- **RBAC enhancements:** granular permissions at the dataset level; allow
  dataset owners to delegate rule creation to maintainers.
- **OpenLineage stub:** record lineage events when incidents are created and
  expose a lineage graph in the UI.
- **Performance testing:** load test the backend and job; document scaling
  guidelines (e.g. horizontal pod autoscaling, partitioning strategies).

## 90‑day goals (Month 3)

- **Multi‑tenant support:** isolate datasets by tenant; provide admin APIs to
  create/manage tenants and assign users.
- **Data contracts:** allow producers to declare data contracts specifying
  expected schema, freshness and distribution; validate contracts on ingest.
- **Granular acknowledgements:** enable per‑row acknowledgements and auto‑close
  incidents when data is repaired.
- **SLO tracking:** expose service SLOs (availability, latency) via the API
  and integrate with Alertmanager to create pager alerts when thresholds are
  breached.
- **Pluggable rule engine:** allow users to write custom rules in Python that
  run in a sandboxed environment.

## Future ideas

- Integrate with dbt to automatically import tests as rules.
- Provide a Python SDK for interacting with the API and running checks.
- Support nested rules and complex boolean logic (AND/OR grouping).
- Explore ML‑based anomaly detection models as first‑class rule types.