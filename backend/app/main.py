from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager
import asyncio

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.api import api_router
from app.core.database import engine, create_tables
from app.services.quality_service import QualityService
from app.services.alert_service import AlertService


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Intelligent Data Quality Platform...")
    
    # Create database tables
    await create_tables()
    
    # Initialize services
    quality_service = QualityService()
    alert_service = AlertService()
    
    # Start background tasks
    asyncio.create_task(quality_service.start_streaming_monitor())
    asyncio.create_task(alert_service.start_alert_processor())
    
    logger.info("Platform startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down platform...")
    await quality_service.stop_streaming_monitor()
    await alert_service.stop_alert_processor()
    logger.info("Platform shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Intelligent Data Quality Platform",
    description="Enterprise-grade data quality monitoring with ML-powered insights",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status_code": 500}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint with platform information"""
    return {
        "message": "Intelligent Data Quality Platform API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_url": "/health"
    }


# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4,
        log_level="debug" if settings.DEBUG else "info"
    )
