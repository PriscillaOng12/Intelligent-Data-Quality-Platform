from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from uuid import UUID

from app.schemas.quality import (
    QualityMetrics,
    QualityCheck,
    QualityCheckCreate,
    QualityCheckResult,
    QualityRule,
    AnomalyDetectionResult
)
from app.services.quality_service import QualityService
from app.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Quality service instance
quality_service = QualityService()


@router.get("/metrics/overview", response_model=QualityMetrics)
async def get_quality_overview(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    time_range: Optional[str] = Query("24h", description="Time range (1h, 24h, 7d, 30d)"),
    db = Depends(get_db)
):
    """Get overall quality metrics overview"""
    try:
        metrics = await quality_service.get_quality_overview(
            dataset_id=dataset_id,
            time_range=time_range,
            db=db
        )
        return metrics
    except Exception as e:
        logger.error(f"Failed to get quality overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quality metrics")


@router.get("/checks", response_model=List[QualityCheck])
async def list_quality_checks(
    dataset_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db = Depends(get_db)
):
    """List quality checks with filtering and pagination"""
    try:
        checks = await quality_service.list_quality_checks(
            dataset_id=dataset_id,
            status=status,
            limit=limit,
            offset=offset,
            db=db
        )
        return checks
    except Exception as e:
        logger.error(f"Failed to list quality checks: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quality checks")


@router.post("/checks", response_model=QualityCheck)
async def create_quality_check(
    check: QualityCheckCreate,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """Create a new quality check"""
    try:
        new_check = await quality_service.create_quality_check(check, db)
        
        # Schedule quality check execution in background
        background_tasks.add_task(
            quality_service.execute_quality_check,
            new_check.id,
            db
        )
        
        return new_check
    except Exception as e:
        logger.error(f"Failed to create quality check: {e}")
        raise HTTPException(status_code=500, detail="Failed to create quality check")


@router.get("/checks/{check_id}", response_model=QualityCheck)
async def get_quality_check(
    check_id: UUID,
    db = Depends(get_db)
):
    """Get specific quality check by ID"""
    try:
        check = await quality_service.get_quality_check(check_id, db)
        if not check:
            raise HTTPException(status_code=404, detail="Quality check not found")
        return check
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quality check {check_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quality check")


@router.post("/checks/{check_id}/execute", response_model=QualityCheckResult)
async def execute_quality_check(
    check_id: UUID,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """Execute a specific quality check"""
    try:
        # Add execution to background tasks
        background_tasks.add_task(
            quality_service.execute_quality_check,
            check_id,
            db
        )
        
        return {"status": "scheduled", "check_id": check_id}
    except Exception as e:
        logger.error(f"Failed to execute quality check {check_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute quality check")


@router.get("/checks/{check_id}/results", response_model=List[QualityCheckResult])
async def get_quality_check_results(
    check_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db = Depends(get_db)
):
    """Get results for a specific quality check"""
    try:
        results = await quality_service.get_quality_check_results(
            check_id=check_id,
            limit=limit,
            offset=offset,
            db=db
        )
        return results
    except Exception as e:
        logger.error(f"Failed to get results for quality check {check_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quality check results")


@router.get("/anomalies", response_model=List[AnomalyDetectionResult])
async def get_anomalies(
    dataset_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high, critical)"),
    time_range: Optional[str] = Query("24h"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db = Depends(get_db)
):
    """Get detected anomalies"""
    try:
        anomalies = await quality_service.get_anomalies(
            dataset_id=dataset_id,
            severity=severity,
            time_range=time_range,
            limit=limit,
            offset=offset,
            db=db
        )
        return anomalies
    except Exception as e:
        logger.error(f"Failed to get anomalies: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve anomalies")


@router.post("/anomalies/detect", response_model=Dict[str, Any])
async def detect_anomalies(
    dataset_id: str,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """Trigger anomaly detection for a dataset"""
    try:
        # Schedule anomaly detection in background
        background_tasks.add_task(
            quality_service.detect_anomalies,
            dataset_id,
            db
        )
        
        return {"status": "scheduled", "dataset_id": dataset_id}
    except Exception as e:
        logger.error(f"Failed to trigger anomaly detection for dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger anomaly detection")


@router.get("/rules", response_model=List[QualityRule])
async def list_quality_rules(
    dataset_id: Optional[str] = Query(None),
    rule_type: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db = Depends(get_db)
):
    """List quality rules"""
    try:
        rules = await quality_service.list_quality_rules(
            dataset_id=dataset_id,
            rule_type=rule_type,
            active=active,
            limit=limit,
            offset=offset,
            db=db
        )
        return rules
    except Exception as e:
        logger.error(f"Failed to list quality rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quality rules")


@router.post("/rules", response_model=QualityRule)
async def create_quality_rule(
    rule: QualityRule,
    db = Depends(get_db)
):
    """Create a new quality rule"""
    try:
        new_rule = await quality_service.create_quality_rule(rule, db)
        return new_rule
    except Exception as e:
        logger.error(f"Failed to create quality rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create quality rule")


@router.get("/trends/{dataset_id}")
async def get_quality_trends(
    dataset_id: str,
    metric: str = Query(..., description="Quality metric to analyze"),
    time_range: str = Query("7d", description="Time range for trend analysis"),
    db = Depends(get_db)
):
    """Get quality trends for a dataset"""
    try:
        trends = await quality_service.get_quality_trends(
            dataset_id=dataset_id,
            metric=metric,
            time_range=time_range,
            db=db
        )
        return trends
    except Exception as e:
        logger.error(f"Failed to get quality trends for dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quality trends")


@router.get("/real-time/status")
async def get_real_time_status():
    """Get real-time quality monitoring status"""
    try:
        status = await quality_service.get_real_time_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get real-time status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get real-time status")
