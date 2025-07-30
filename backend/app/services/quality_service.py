import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import json

from app.schemas.quality import (
    QualityMetrics,
    QualityCheck,
    QualityCheckCreate,
    QualityCheckResult,
    QualityRule,
    AnomalyDetectionResult,
    QualityCheckStatus,
    SeverityLevel
)
from app.core.config import settings
from app.utils.spark_utils import SparkManager
from app.ml.anomaly_detection.ensemble_detector import EnsembleAnomalyDetector
from app.spark_jobs.quality_checks.base_check import QualityCheckExecutor

logger = logging.getLogger(__name__)


class QualityService:
    """Core service for data quality monitoring and management"""
    
    def __init__(self):
        self.spark_manager = SparkManager()
        self.anomaly_detector = EnsembleAnomalyDetector()
        self.quality_executor = QualityCheckExecutor()
        self._streaming_monitor_active = False
        self._streaming_task = None
    
    async def get_quality_overview(
        self,
        dataset_id: Optional[str] = None,
        time_range: str = "24h",
        db = None
    ) -> QualityMetrics:
        """Get comprehensive quality metrics overview"""
        try:
            # Parse time range
            time_delta = self._parse_time_range(time_range)
            since = datetime.utcnow() - time_delta
            
            # Get quality metrics from database
            query_filters = {"created_at__gte": since}
            if dataset_id:
                query_filters["dataset_id"] = dataset_id
            
            # Simulate database queries (replace with actual DB operations)
            total_checks = await self._count_quality_checks(query_filters, db)
            passed_checks = await self._count_quality_checks({**query_filters, "status": "passed"}, db)
            failed_checks = await self._count_quality_checks({**query_filters, "status": "failed"}, db)
            anomalies = await self._count_anomalies(query_filters, db)
            active_alerts = await self._count_active_alerts(query_filters, db)
            dataset_count = await self._count_monitored_datasets(query_filters, db)
            
            # Calculate quality score
            quality_score = passed_checks / max(total_checks, 1)
            
            return QualityMetrics(
                dataset_count=dataset_count,
                total_checks=total_checks,
                passed_checks=passed_checks,
                failed_checks=failed_checks,
                quality_score=quality_score,
                anomalies_detected=anomalies,
                active_alerts=active_alerts,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to get quality overview: {e}")
            raise
    
    async def list_quality_checks(
        self,
        dataset_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        db = None
    ) -> List[QualityCheck]:
        """List quality checks with filtering"""
        try:
            # Build query filters
            filters = {}
            if dataset_id:
                filters["dataset_id"] = dataset_id
            if status:
                filters["status"] = status
            
            # Simulate database query (replace with actual implementation)
            checks = await self._query_quality_checks(filters, limit, offset, db)
            return checks
            
        except Exception as e:
            logger.error(f"Failed to list quality checks: {e}")
            raise
    
    async def create_quality_check(
        self,
        check_data: QualityCheckCreate,
        db = None
    ) -> QualityCheck:
        """Create a new quality check"""
        try:
            # Create quality check record
            check = QualityCheck(
                **check_data.dict(),
                status=QualityCheckStatus.PENDING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save to database (simulated)
            saved_check = await self._save_quality_check(check, db)
            
            logger.info(f"Created quality check {saved_check.id} for dataset {check_data.dataset_id}")
            return saved_check
            
        except Exception as e:
            logger.error(f"Failed to create quality check: {e}")
            raise
    
    async def execute_quality_check(
        self,
        check_id: UUID,
        db = None
    ) -> QualityCheckResult:
        """Execute a specific quality check"""
        try:
            # Get quality check
            check = await self._get_quality_check_by_id(check_id, db)
            if not check:
                raise ValueError(f"Quality check {check_id} not found")
            
            # Update status to running
            await self._update_check_status(check_id, QualityCheckStatus.RUNNING, db)
            
            # Execute the check using Spark
            start_time = datetime.utcnow()
            result = await self.quality_executor.execute_check(check)
            execution_duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Create result record
            check_result = QualityCheckResult(
                check_id=check_id,
                dataset_id=check.dataset_id,
                execution_time=start_time,
                status=QualityCheckStatus.COMPLETED if result["passed"] else QualityCheckStatus.FAILED,
                passed=result["passed"],
                score=result["score"],
                metrics=result["metrics"],
                errors=result.get("errors"),
                execution_duration=execution_duration,
                row_count=result.get("row_count")
            )
            
            # Save result
            await self._save_check_result(check_result, db)
            
            # Update check last run time
            await self._update_check_last_run(check_id, start_time, db)
            
            logger.info(f"Executed quality check {check_id}, result: {result['passed']}")
            return check_result
            
        except Exception as e:
            logger.error(f"Failed to execute quality check {check_id}: {e}")
            # Update status to failed
            await self._update_check_status(check_id, QualityCheckStatus.FAILED, db)
            raise
    
    async def get_anomalies(
        self,
        dataset_id: Optional[str] = None,
        severity: Optional[str] = None,
        time_range: str = "24h",
        limit: int = 100,
        offset: int = 0,
        db = None
    ) -> List[AnomalyDetectionResult]:
        """Get detected anomalies with filtering"""
        try:
            time_delta = self._parse_time_range(time_range)
            since = datetime.utcnow() - time_delta
            
            filters = {"detected_at__gte": since}
            if dataset_id:
                filters["dataset_id"] = dataset_id
            if severity:
                filters["severity"] = severity
            
            anomalies = await self._query_anomalies(filters, limit, offset, db)
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to get anomalies: {e}")
            raise
    
    async def detect_anomalies(
        self,
        dataset_id: str,
        db = None
    ) -> List[AnomalyDetectionResult]:
        """Trigger anomaly detection for a dataset"""
        try:
            logger.info(f"Starting anomaly detection for dataset {dataset_id}")
            
            # Load dataset using Spark
            dataset = await self.spark_manager.load_dataset(dataset_id)
            
            # Run anomaly detection
            anomalies = await self.anomaly_detector.detect_anomalies(dataset)
            
            # Convert to result objects
            results = []
            for anomaly in anomalies:
                result = AnomalyDetectionResult(
                    dataset_id=dataset_id,
                    column_name=anomaly.get("column_name"),
                    anomaly_type=anomaly["type"],
                    severity=SeverityLevel(anomaly["severity"]),
                    confidence=anomaly["confidence"],
                    description=anomaly["description"],
                    metadata=anomaly.get("metadata", {})
                )
                results.append(result)
                
                # Save to database
                await self._save_anomaly_result(result, db)
            
            logger.info(f"Detected {len(results)} anomalies for dataset {dataset_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies for dataset {dataset_id}: {e}")
            raise
    
    async def start_streaming_monitor(self):
        """Start real-time streaming quality monitor"""
        if self._streaming_monitor_active:
            logger.warning("Streaming monitor already active")
            return
        
        try:
            self._streaming_monitor_active = True
            self._streaming_task = asyncio.create_task(self._streaming_monitor_loop())
            logger.info("Started streaming quality monitor")
            
        except Exception as e:
            logger.error(f"Failed to start streaming monitor: {e}")
            self._streaming_monitor_active = False
            raise
    
    async def stop_streaming_monitor(self):
        """Stop real-time streaming quality monitor"""
        self._streaming_monitor_active = False
        if self._streaming_task:
            self._streaming_task.cancel()
            try:
                await self._streaming_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped streaming quality monitor")
    
    async def get_real_time_status(self) -> Dict[str, Any]:
        """Get real-time monitoring status"""
        return {
            "streaming_active": self._streaming_monitor_active,
            "monitored_streams": await self._get_monitored_streams(),
            "last_check": datetime.utcnow().isoformat(),
            "performance_metrics": await self._get_performance_metrics()
        }
    
    # Helper methods (simulated database operations)
    
    def _parse_time_range(self, time_range: str) -> timedelta:
        """Parse time range string to timedelta"""
        units = {"h": "hours", "d": "days", "w": "weeks"}
        if time_range[-1] in units:
            value = int(time_range[:-1])
            unit = units[time_range[-1]]
            return timedelta(**{unit: value})
        raise ValueError(f"Invalid time range format: {time_range}")
    
    async def _streaming_monitor_loop(self):
        """Main streaming monitor loop"""
        while self._streaming_monitor_active:
            try:
                # Monitor streaming data quality
                await self._process_streaming_quality_checks()
                await asyncio.sleep(1)  # Check every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in streaming monitor: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _process_streaming_quality_checks(self):
        """Process real-time quality checks on streaming data"""
        # Implementation for real-time quality monitoring
        pass
    
    # Simulated database operations (replace with actual implementations)
    
    async def _count_quality_checks(self, filters: Dict, db) -> int:
        """Count quality checks with filters"""
        # Simulate database count operation
        return 150  # Mock value
    
    async def _count_anomalies(self, filters: Dict, db) -> int:
        """Count anomalies with filters"""
        return 12  # Mock value
    
    async def _count_active_alerts(self, filters: Dict, db) -> int:
        """Count active alerts"""
        return 3  # Mock value
    
    async def _count_monitored_datasets(self, filters: Dict, db) -> int:
        """Count monitored datasets"""
        return 25  # Mock value
    
    async def _query_quality_checks(self, filters: Dict, limit: int, offset: int, db) -> List[QualityCheck]:
        """Query quality checks from database"""
        # Mock implementation
        return []
    
    async def _save_quality_check(self, check: QualityCheck, db) -> QualityCheck:
        """Save quality check to database"""
        return check
    
    async def _get_quality_check_by_id(self, check_id: UUID, db) -> Optional[QualityCheck]:
        """Get quality check by ID"""
        return None
    
    async def _update_check_status(self, check_id: UUID, status: QualityCheckStatus, db):
        """Update quality check status"""
        pass
    
    async def _save_check_result(self, result: QualityCheckResult, db):
        """Save quality check result"""
        pass
    
    async def _update_check_last_run(self, check_id: UUID, last_run: datetime, db):
        """Update quality check last run time"""
        pass
    
    async def _query_anomalies(self, filters: Dict, limit: int, offset: int, db) -> List[AnomalyDetectionResult]:
        """Query anomalies from database"""
        return []
    
    async def _save_anomaly_result(self, result: AnomalyDetectionResult, db):
        """Save anomaly detection result"""
        pass
    
    async def _get_monitored_streams(self) -> List[str]:
        """Get list of monitored streams"""
        return ["stream1", "stream2"]
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            "throughput": "1000 records/sec",
            "latency": "50ms",
            "error_rate": "0.1%"
        }
