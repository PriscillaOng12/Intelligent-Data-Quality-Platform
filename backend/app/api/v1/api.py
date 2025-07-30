from fastapi import APIRouter

from app.api.v1.endpoints import quality, lineage, alerts, datasets, auth

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(quality.router, prefix="/quality", tags=["quality"])
api_router.include_router(lineage.router, prefix="/lineage", tags=["lineage"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])


@api_router.get("/health")
async def api_health():
    """API health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}
