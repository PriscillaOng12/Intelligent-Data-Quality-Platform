"""Aggregate API routers for FastAPI application."""

from fastapi import APIRouter

from . import auth, datasets, incidents, rules, health


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(rules.router, prefix="/rules", tags=["rules"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(health.router, tags=["health"])