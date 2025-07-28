<!-- markdownlint-disable MD041 -->
# ADR‑001: Use FastAPI and SQLModel for the Backend

## Status

Accepted – 2025‑08‑11

## Context

We needed to choose a web framework and ORM for the backend API. The
requirements included strong typing, good developer experience, automatic
OpenAPI generation, performance, and ease of testing. Additionally, we wanted
to minimise boilerplate when defining request/response schemas and database
models.

## Decision

We chose **FastAPI** for the web framework and **SQLModel** (built on
SQLAlchemy) for the ORM. FastAPI provides asynchronous request handling,
automatic OpenAPI documentation, dependency injection and first‑class
type annotations. SQLModel allows us to define our database models using
modern Python type hints and serves both as ORM models and Pydantic models.

## Consequences

- API routes benefit from automatic data validation and clear type signatures.
- The learning curve for developers coming from Django/Flask is minimal.
- We rely on a relatively young library (SQLModel) which may lack advanced
  features; migrations will require Alembic.
- Performance is sufficient for our use case; for extremely high throughput we
  could consider frameworks like Fastify (Node) or an async ORM like Tortoise.