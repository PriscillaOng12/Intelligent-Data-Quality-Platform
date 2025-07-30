from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from app.schemas.alerts import (
    Alert,
    AlertCreate,
    AlertRule,
    AlertStatus,
    AlertSeverity,
    AlertSummary
)
from app.services.alert_service import AlertService
from app.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

# Alert service instance
alert_service = AlertService()


@router.get("/", response_model=List[Alert])
async def list_alerts(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    status: Optional[AlertStatus] = Query(None, description="Filter by status"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db = Depends(get_db)
):
    """List alerts with filtering and pagination"""
    try:
        alerts = await alert_service.list_alerts(
            dataset_id=dataset_id,
            status=status,
            severity=severity,
            limit=limit,
            offset=offset,
            db=db
        )
        return alerts
    except Exception as e:
        logger.error(f"Failed to list alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.post("/", response_model=Alert)
async def create_alert(
    alert: AlertCreate,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """Create a new alert"""
    try:
        new_alert = await alert_service.create_alert(alert, db)
        return new_alert
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert")


@router.get("/{alert_id}", response_model=Alert)
async def get_alert(
    alert_id: UUID,
    db = Depends(get_db)
):
    """Get specific alert by ID"""
    try:
        alert = await alert_service._get_alert_by_id(alert_id, db)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alert
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert")


@router.patch("/{alert_id}/status")
async def update_alert_status(
    alert_id: UUID,
    status: AlertStatus,
    resolved_by: Optional[str] = None,
    resolution_notes: Optional[str] = None,
    db = Depends(get_db)
):
    """Update alert status"""
    try:
        updated_alert = await alert_service.update_alert_status(
            alert_id=alert_id,
            status=status,
            resolved_by=resolved_by,
            resolution_notes=resolution_notes,
            db=db
        )
        return updated_alert
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update alert status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update alert status")


@router.get("/statistics/summary", response_model=Dict[str, Any])
async def get_alert_statistics(
    time_range: str = Query("24h", description="Time range (1h, 24h, 7d, 30d)"),
    db = Depends(get_db)
):
    """Get alert statistics and summary"""
    try:
        stats = await alert_service.get_alert_statistics(time_range=time_range, db=db)
        return stats
    except Exception as e:
        logger.error(f"Failed to get alert statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert statistics")


@router.get("/rules/", response_model=List[AlertRule])
async def list_alert_rules(
    dataset_id: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db = Depends(get_db)
):
    """List alert rules"""
    try:
        # This would be implemented in alert_service
        rules = []  # Mock empty list
        return rules
    except Exception as e:
        logger.error(f"Failed to list alert rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert rules")


@router.post("/rules/", response_model=AlertRule)
async def create_alert_rule(
    rule: AlertRule,
    db = Depends(get_db)
):
    """Create a new alert rule"""
    try:
        new_rule = await alert_service.create_alert_rule(rule, db)
        return new_rule
    except Exception as e:
        logger.error(f"Failed to create alert rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert rule")


@router.post("/evaluate/{dataset_id}")
async def evaluate_alert_rules(
    dataset_id: str,
    quality_metrics: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """Evaluate alert rules for a dataset"""
    try:
        background_tasks.add_task(
            alert_service.evaluate_alert_rules,
            dataset_id,
            quality_metrics,
            db
        )
        return {"status": "evaluation_scheduled", "dataset_id": dataset_id}
    except Exception as e:
        logger.error(f"Failed to evaluate alert rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to evaluate alert rules")
