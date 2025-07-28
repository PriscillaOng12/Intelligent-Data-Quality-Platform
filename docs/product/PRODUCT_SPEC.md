<!-- markdownlint-disable MD041 -->
# Product Requirements Document (PRD)

## Problem statement

Data quality issues—missing values, stale records, duplicate entries,
unexpected schema changes—can wreak havoc downstream, causing dashboards to
display incorrect information, ML models to degrade and analysts to spend
hours debugging. Traditional data quality tools are either heavyweight
enterprise platforms or limited to batch processing. There is a need for an
open source solution that provides intelligent, end‑to‑end data quality
monitoring for both streaming and batch pipelines.

## Users and personas

| Persona          | Goals & frustrations                                             |
|------------------|-----------------------------------------------------------------|
| Data Engineer    | Ensure reliable pipelines; wants automated checks and fast feedback when something breaks. |
| Data Scientist   | Needs trustworthy input data; frustrated by silent data drift.   |
| Product Manager | Monitors product metrics; concerned about data latency and accuracy; wants high‑level views. |
| SRE/On‑call      | Keeps the system running; needs actionable alerts and runbooks.  |

## Jobs to be done (JTBD)

1. When ingesting a new dataset, **define quality rules** quickly without writing code.
2. **Detect anomalies** in near real‑time and surface them to the right person with context.
3. Allow stakeholders to **acknowledge or mute** alerts and track incident lifecycle.
4. Provide **dashboards** that quantify the health of datasets over time.
5. Enable easy **extension** of rule types and integration points (e.g. streaming, lineage).

## Scope

The initial release (MVP) includes:

- CRUD APIs for users, datasets, rules and incidents.
- Completeness, freshness and uniqueness checks executed via a scheduled job.
- A React front‑end that visualises incidents and allows rule creation.
- JWT authentication, role‑based access control and basic rate limiting.
- Observability via Prometheus/Grafana.
- Demo mode with synthetic data generation and one‑command boot.

## Non‑goals

- Real‑time streaming ingestion with exactly‑once guarantees (future work).
- Automated remediation (e.g. backfilling data) beyond surfacing incidents.
- Full lineage integration via OpenLineage (stubbed for now).
- Supporting multi‑tenant isolation and billing.

## Competitive landscape

| Platform           | Strengths                               | Limitations                           |
|--------------------|-----------------------------------------|---------------------------------------|
| Great Expectations | Rich checks, Jupyter integrations       | Batch oriented, lacks UI              |
| Monte Carlo        | Enterprise‑grade, strong lineage        | Commercial, closed source             |
| Soda               | SQL‑centric, alerting integrations      | Limited streaming support             |
| IDQP (this)        | Full stack, open source, extensible     | MVP scope, limited rule coverage      |

## Success metrics

We will measure success using both leading and lagging indicators:

- **MTTD (Mean Time To Detect)**: average time between a data issue occurring and an incident being raised.
- **MTTR (Mean Time To Resolution)**: time between an incident being raised and acknowledged/muted.
- **Coverage**: percentage of critical datasets monitored by at least one rule.
- **False positive rate**: ratio of acknowledged incidents that are deemed non‑issues.

Refer to [Metrics & SLOs](METRICS_AND_SLOS.md) for more details.

## MVP vs production features

| Feature                            | MVP                               | Production                         |
|------------------------------------|-----------------------------------|-----------------------------------|
| Rule types                         | Completeness, freshness, uniqueness| Distribution drift, outlier rate, schema drift |
| Storage                            | Postgres, local Delta             | Multi‑region, scalable blob storage |
| Streaming                          | Mock mode via pandas             | Redpanda/Kafka with exactly‑once semantics |
| Alerting                           | Email/logging stub               | Slack, PagerDuty integrations      |
| Auth & RBAC                        | JWT, basic roles                 | SSO/SAML, fine‑grained ACLs        |

## Open questions

- How should we version and evolve rule definitions? Should rules be versioned along with schema?
- What is the right UX for building complex rules (e.g. nested conditions) in the UI?
- How can we integrate lineage information (e.g. via OpenLineage) to automatically assess downstream impact of incidents?