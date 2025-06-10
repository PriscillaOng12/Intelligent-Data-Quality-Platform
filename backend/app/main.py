"""FastAPI application entrypoint.

This module constructs the FastAPI app, configures global middleware for
CORS, logging and metrics, mounts the API routers and the Prometheus metrics
endpoint. The application is ready to be run with Uvicorn.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.base import BaseHTTPMiddleware
from prometheus_client import make_asgi_app

from app.api import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import init_db
from app.telemetry.metrics import metrics_middleware


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""

    configure_logging()
    init_db()
    app = FastAPI(
        title="Intelligent Data Quality Platform",
        version="0.1.0",
        description="API backend for the Intelligent Data Quality Platform",
    )
    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url, "http://localhost"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Metrics middleware
    app.add_middleware(BaseHTTPMiddleware, dispatch=metrics_middleware)
    # Include routers
    app.include_router(api_router)
    # Mount Prometheus metrics as a separate ASGI app
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    return app


app = create_app()