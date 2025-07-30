import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import json

from app.schemas.alerts import (
    Alert,
    AlertCreate,
    AlertRule,
    AlertStatus,
    AlertSeverity,
    NotificationChannel
)
from app.services.notification_service import NotificationService
from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertService:
    """Service for managing data quality alerts and notifications"""
    
    def __init__(self):
        self.notification_service = NotificationService()
        self._alert_processor_active = False
        self._alert_processor_task = None
        self._alert_queue = asyncio.Queue()
    
    async def create_alert(
        self,
        alert_data: AlertCreate,
        db = None
    ) -> Alert:
        """Create a new alert"""
        try:
            alert = Alert(
                **alert_data.dict(),
                id=uuid4(),
                status=AlertStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save to database
            saved_alert = await self._save_alert(alert, db)
            
            # Add to processing queue
            await self._alert_queue.put(saved_alert)
            
            logger.info(f"Created alert {saved_alert.id} for dataset {alert_data.dataset_id}")
            return saved_alert
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            raise
    
    async def list_alerts(
        self,
        dataset_id: Optional[str] = None,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        limit: int = 100,
        offset: int = 0,
        db = None
    ) -> List[Alert]:
        """List alerts with filtering"""
        try:
            filters = {}
            if dataset_id:
                filters["dataset_id"] = dataset_id
            if status:
                filters["status"] = status
            if severity:
                filters["severity"] = severity
            
            alerts = await self._query_alerts(filters, limit, offset, db)
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to list alerts: {e}")
            raise
    
    async def update_alert_status(
        self,
        alert_id: UUID,
        status: AlertStatus,
        resolved_by: Optional[str] = None,
        resolution_notes: Optional[str] = None,
        db = None
    ) -> Alert:
        """Update alert status"""
        try:
            alert = await self._get_alert_by_id(alert_id, db)
            if not alert:
                raise ValueError(f"Alert {alert_id} not found")
            
            alert.status = status
            alert.updated_at = datetime.utcnow()
            
            if status == AlertStatus.RESOLVED:
                alert.resolved_at = datetime.utcnow()
                alert.resolved_by = resolved_by
                alert.resolution_notes = resolution_notes
            
            updated_alert = await self._save_alert(alert, db)
            
            logger.info(f"Updated alert {alert_id} status to {status}")
            return updated_alert
            
        except Exception as e:
            logger.error(f"Failed to update alert status: {e}")
            raise
    
    async def create_alert_rule(
        self,
        rule_data: AlertRule,
        db = None
    ) -> AlertRule:
        """Create a new alert rule"""
        try:
            rule = AlertRule(
                **rule_data.dict(),
                id=uuid4(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            saved_rule = await self._save_alert_rule(rule, db)
            
            logger.info(f"Created alert rule {saved_rule.id}")
            return saved_rule
            
        except Exception as e:
            logger.error(f"Failed to create alert rule: {e}")
            raise
    
    async def evaluate_alert_rules(
        self,
        dataset_id: str,
        quality_metrics: Dict[str, Any],
        db = None
    ) -> List[Alert]:
        """Evaluate alert rules against quality metrics"""
        try:
            # Get active rules for dataset
            rules = await self._get_alert_rules_for_dataset(dataset_id, db)
            
            triggered_alerts = []
            
            for rule in rules:
                if await self._should_trigger_alert(rule, quality_metrics):
                    alert_data = AlertCreate(
                        title=f"Quality Alert: {rule.name}",
                        description=f"Alert rule '{rule.name}' triggered for dataset {dataset_id}",
                        dataset_id=dataset_id,
                        severity=rule.severity,
                        rule_id=rule.id,
                        metadata={
                            "rule_name": rule.name,
                            "triggered_condition": rule.condition,
                            "current_metrics": quality_metrics
                        }
                    )
                    
                    alert = await self.create_alert(alert_data, db)
                    triggered_alerts.append(alert)
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"Failed to evaluate alert rules: {e}")
            raise
    
    async def start_alert_processor(self):
        """Start background alert processing"""
        if self._alert_processor_active:
            logger.warning("Alert processor already active")
            return
        
        try:
            self._alert_processor_active = True
            self._alert_processor_task = asyncio.create_task(self._alert_processor_loop())
            logger.info("Started alert processor")
            
        except Exception as e:
            logger.error(f"Failed to start alert processor: {e}")
            self._alert_processor_active = False
            raise
    
    async def stop_alert_processor(self):
        """Stop background alert processing"""
        self._alert_processor_active = False
        if self._alert_processor_task:
            self._alert_processor_task.cancel()
            try:
                await self._alert_processor_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped alert processor")
    
    async def get_alert_statistics(
        self,
        time_range: str = "24h",
        db = None
    ) -> Dict[str, Any]:
        """Get alert statistics"""
        try:
            time_delta = self._parse_time_range(time_range)
            since = datetime.utcnow() - time_delta
            
            stats = {
                "total_alerts": await self._count_alerts({"created_at__gte": since}, db),
                "active_alerts": await self._count_alerts({"status": AlertStatus.ACTIVE, "created_at__gte": since}, db),
                "resolved_alerts": await self._count_alerts({"status": AlertStatus.RESOLVED, "created_at__gte": since}, db),
                "critical_alerts": await self._count_alerts({"severity": AlertSeverity.CRITICAL, "created_at__gte": since}, db),
                "by_severity": await self._count_alerts_by_severity(since, db),
                "by_dataset": await self._count_alerts_by_dataset(since, db),
                "resolution_time": await self._calculate_avg_resolution_time(since, db)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get alert statistics: {e}")
            raise
    
    # Helper methods
    
    async def _alert_processor_loop(self):
        """Main alert processing loop"""
        while self._alert_processor_active:
            try:
                # Process alerts from queue
                try:
                    alert = await asyncio.wait_for(self._alert_queue.get(), timeout=1.0)
                    await self._process_alert(alert)
                except asyncio.TimeoutError:
                    continue
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert processor: {e}")
                await asyncio.sleep(1)
    
    async def _process_alert(self, alert: Alert):
        """Process individual alert"""
        try:
            # Send notifications based on alert severity and rules
            await self.notification_service.send_alert_notification(alert)
            
            # Update alert as processed
            await self._mark_alert_processed(alert.id)
            
            logger.info(f"Processed alert {alert.id}")
            
        except Exception as e:
            logger.error(f"Failed to process alert {alert.id}: {e}")
    
    async def _should_trigger_alert(
        self,
        rule: AlertRule,
        metrics: Dict[str, Any]
    ) -> bool:
        """Check if alert rule should be triggered"""
        try:
            condition = rule.condition
            
            # Simple condition evaluation (extend as needed)
            if condition["type"] == "threshold":
                metric_name = condition["metric"]
                operator = condition["operator"]
                threshold = condition["threshold"]
                
                current_value = metrics.get(metric_name)
                if current_value is None:
                    return False
                
                if operator == "lt":
                    return current_value < threshold
                elif operator == "gt":
                    return current_value > threshold
                elif operator == "eq":
                    return current_value == threshold
                elif operator == "ne":
                    return current_value != threshold
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to evaluate alert condition: {e}")
            return False
    
    def _parse_time_range(self, time_range: str) -> timedelta:
        """Parse time range string to timedelta"""
        units = {"h": "hours", "d": "days", "w": "weeks"}
        if time_range[-1] in units:
            value = int(time_range[:-1])
            unit = units[time_range[-1]]
            return timedelta(**{unit: value})
        raise ValueError(f"Invalid time range format: {time_range}")
    
    # Simulated database operations
    
    async def _save_alert(self, alert: Alert, db) -> Alert:
        """Save alert to database"""
        return alert
    
    async def _query_alerts(self, filters: Dict, limit: int, offset: int, db) -> List[Alert]:
        """Query alerts from database"""
        return []
    
    async def _get_alert_by_id(self, alert_id: UUID, db) -> Optional[Alert]:
        """Get alert by ID"""
        return None
    
    async def _save_alert_rule(self, rule: AlertRule, db) -> AlertRule:
        """Save alert rule to database"""
        return rule
    
    async def _get_alert_rules_for_dataset(self, dataset_id: str, db) -> List[AlertRule]:
        """Get alert rules for dataset"""
        return []
    
    async def _count_alerts(self, filters: Dict, db) -> int:
        """Count alerts with filters"""
        return 0
    
    async def _count_alerts_by_severity(self, since: datetime, db) -> Dict[str, int]:
        """Count alerts by severity"""
        return {"critical": 2, "high": 5, "medium": 8, "low": 3}
    
    async def _count_alerts_by_dataset(self, since: datetime, db) -> Dict[str, int]:
        """Count alerts by dataset"""
        return {"dataset1": 5, "dataset2": 8, "dataset3": 3}
    
    async def _calculate_avg_resolution_time(self, since: datetime, db) -> float:
        """Calculate average resolution time in minutes"""
        return 45.5  # Mock value
    
    async def _mark_alert_processed(self, alert_id: UUID):
        """Mark alert as processed"""
        pass
