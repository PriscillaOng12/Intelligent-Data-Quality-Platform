"""Structured logging configuration using structlog.

The backend emits JSON logs enriched with contextual information like the
request id and user. These logs are easy to parse and can be shipped to
observability pipelines. To enable tracing of requests, the `request_id`
middleware in `main.py` injects a unique ID per request.
"""

import logging
import sys
from typing import Any, Dict

import structlog


def configure_logging() -> None:
    """Configure the logging and structlog frameworks to emit JSON logs."""

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Return a structlog logger bound to a specific name."""

    return structlog.get_logger(name)