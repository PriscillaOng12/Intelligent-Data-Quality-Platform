from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class QualityCheckType(str, Enum):
    """Quality check types"""
    COMPLETENESS = "completeness"
    UNIQUENESS = "uniqueness"
    VALIDITY = "validity"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    CUSTOM = "custom"


class QualityCheckStatus(str, Enum):
    """Quality check execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SeverityLevel(str, Enum):
    """Severity levels for quality issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class QualityMetrics(BaseModel):
    """Overall quality metrics response"""
    dataset_count: int = Field(..., description="Total number of datasets monitored")
    total_checks: int = Field(..., description="Total quality checks executed")
    passed_checks: int = Field(..., description="Number of passed checks")
    failed_checks: int = Field(..., description="Number of failed checks")
    quality_score: float = Field(..., ge=0, le=1, description="Overall quality score")
    anomalies_detected: int = Field(..., description="Number of anomalies detected")
    active_alerts: int = Field(..., description="Number of active alerts")
    last_updated: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class QualityRule(BaseModel):
    """Quality rule definition"""
    id: Optional[UUID] = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    dataset_id: str = Field(..., description="Target dataset ID")
    column_name: Optional[str] = Field(None, description="Target column (if applicable)")
    rule_type: QualityCheckType = Field(..., description="Type of quality rule")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Rule parameters")
    threshold: Optional[float] = Field(None, ge=0, le=1, description="Quality threshold")
    is_active: bool = Field(True, description="Whether rule is active")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('parameters')
    def validate_parameters(cls, v, values):
        """Validate parameters based on rule type"""
        rule_type = values.get('rule_type')
        if rule_type == QualityCheckType.COMPLETENESS:
            # Completeness rules require minimal parameters
            pass
        elif rule_type == QualityCheckType.UNIQUENESS:
            # Uniqueness rules might specify columns to check
            pass
        elif rule_type == QualityCheckType.VALIDITY:
            # Validity rules need pattern or format specifications
            if 'pattern' not in v and 'format' not in v:
                raise ValueError("Validity rules require 'pattern' or 'format' parameter")
        return v
    
    class Config:
        from_attributes = True


class QualityCheckCreate(BaseModel):
    """Schema for creating quality checks"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    dataset_id: str = Field(..., description="Target dataset ID")
    check_type: QualityCheckType = Field(..., description="Type of quality check")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    schedule: Optional[str] = Field(None, description="Cron expression for scheduling")
    enabled: bool = Field(True, description="Whether check is enabled")


class QualityCheck(QualityCheckCreate):
    """Complete quality check schema"""
    id: UUID = Field(default_factory=uuid4)
    status: QualityCheckStatus = Field(QualityCheckStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class QualityCheckResult(BaseModel):
    """Quality check execution result"""
    id: UUID = Field(default_factory=uuid4)
    check_id: UUID = Field(..., description="Associated quality check ID")
    dataset_id: str = Field(..., description="Target dataset ID")
    execution_time: datetime = Field(default_factory=datetime.utcnow)
    status: QualityCheckStatus = Field(..., description="Execution status")
    passed: Optional[bool] = Field(None, description="Whether check passed")
    score: Optional[float] = Field(None, ge=0, le=1, description="Quality score")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Detailed metrics")
    errors: Optional[List[str]] = Field(None, description="Error messages if failed")
    execution_duration: Optional[float] = Field(None, description="Execution time in seconds")
    row_count: Optional[int] = Field(None, description="Number of rows processed")
    
    class Config:
        from_attributes = True


class AnomalyDetectionResult(BaseModel):
    """Anomaly detection result"""
    id: UUID = Field(default_factory=uuid4)
    dataset_id: str = Field(..., description="Dataset where anomaly was detected")
    column_name: Optional[str] = Field(None, description="Column with anomaly")
    anomaly_type: str = Field(..., description="Type of anomaly detected")
    severity: SeverityLevel = Field(..., description="Severity of the anomaly")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    description: str = Field(..., description="Human-readable description")
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        from_attributes = True


class StatisticalProfile(BaseModel):
    """Statistical profile for a column"""
    column_name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Data type")
    null_count: int = Field(..., description="Number of null values")
    null_percentage: float = Field(..., ge=0, le=1, description="Percentage of null values")
    unique_count: Optional[int] = Field(None, description="Number of unique values")
    min_value: Optional[Union[str, int, float]] = None
    max_value: Optional[Union[str, int, float]] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    std_deviation: Optional[float] = None
    percentiles: Optional[Dict[str, float]] = None
    most_frequent: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True


class DatasetProfile(BaseModel):
    """Complete dataset statistical profile"""
    dataset_id: str = Field(..., description="Dataset identifier")
    row_count: int = Field(..., description="Total number of rows")
    column_count: int = Field(..., description="Total number of columns")
    size_bytes: Optional[int] = Field(None, description="Dataset size in bytes")
    columns: List[StatisticalProfile] = Field(..., description="Column profiles")
    profiled_at: datetime = Field(default_factory=datetime.utcnow)
    quality_score: Optional[float] = Field(None, ge=0, le=1)
    
    class Config:
        from_attributes = True


class QualityTrend(BaseModel):
    """Quality trend data point"""
    timestamp: datetime = Field(..., description="Timestamp of measurement")
    metric_name: str = Field(..., description="Name of the quality metric")
    value: float = Field(..., description="Metric value")
    dataset_id: str = Field(..., description="Associated dataset")
    
    class Config:
        from_attributes = True


class QualityReport(BaseModel):
    """Comprehensive quality report"""
    report_id: UUID = Field(default_factory=uuid4)
    dataset_id: str = Field(..., description="Target dataset")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    time_period: str = Field(..., description="Reporting period")
    overall_score: float = Field(..., ge=0, le=1)
    check_results: List[QualityCheckResult] = Field(..., description="Quality check results")
    anomalies: List[AnomalyDetectionResult] = Field(..., description="Detected anomalies")
    trends: List[QualityTrend] = Field(..., description="Quality trends")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    
    class Config:
        from_attributes = True
