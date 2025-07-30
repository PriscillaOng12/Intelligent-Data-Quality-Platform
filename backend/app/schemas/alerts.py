from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class AlertStatus(str, Enum):
    """Alert status enumeration"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


class AlertCreate(BaseModel):
    """Schema for creating alerts"""
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=1000)
    dataset_id: str = Field(..., description="Associated dataset ID")
    severity: AlertSeverity = Field(..., description="Alert severity")
    rule_id: Optional[UUID] = Field(None, description="Associated alert rule ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        from_attributes = True


class Alert(AlertCreate):
    """Complete alert schema"""
    id: UUID = Field(default_factory=uuid4)
    status: AlertStatus = Field(AlertStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class AlertRule(BaseModel):
    """Alert rule definition"""
    id: Optional[UUID] = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    dataset_id: Optional[str] = Field(None, description="Target dataset (if specific)")
    condition: Dict[str, Any] = Field(..., description="Alert condition definition")
    severity: AlertSeverity = Field(..., description="Alert severity when triggered")
    notification_channels: List[NotificationChannel] = Field(default_factory=list)
    notification_settings: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = Field(True, description="Whether rule is active")
    cooldown_minutes: int = Field(5, ge=0, description="Cooldown period in minutes")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('condition')
    def validate_condition(cls, v):
        """Validate alert condition structure"""
        required_fields = ['type', 'metric']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Condition must include '{field}' field")
        
        condition_type = v.get('type')
        if condition_type == 'threshold':
            if 'operator' not in v or 'threshold' not in v:
                raise ValueError("Threshold conditions require 'operator' and 'threshold' fields")
            
            valid_operators = ['lt', 'gt', 'eq', 'ne', 'lte', 'gte']
            if v['operator'] not in valid_operators:
                raise ValueError(f"Invalid operator. Must be one of {valid_operators}")
        
        return v
    
    class Config:
        from_attributes = True


class NotificationTemplate(BaseModel):
    """Notification template"""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    channel: NotificationChannel = Field(..., description="Target notification channel")
    template_type: str = Field(..., description="Type of template (alert, report, etc.)")
    subject_template: str = Field(..., description="Subject/title template")
    body_template: str = Field(..., description="Message body template")
    variables: List[str] = Field(default_factory=list, description="Available template variables")
    is_active: bool = Field(True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NotificationLog(BaseModel):
    """Notification delivery log"""
    id: UUID = Field(default_factory=uuid4)
    alert_id: UUID = Field(..., description="Associated alert ID")
    channel: NotificationChannel = Field(..., description="Notification channel used")
    recipient: str = Field(..., description="Notification recipient")
    subject: str = Field(..., description="Notification subject/title")
    message: str = Field(..., description="Notification message")
    status: str = Field(..., description="Delivery status")
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class AlertSummary(BaseModel):
    """Alert summary for dashboards"""
    total_active: int = Field(..., description="Total active alerts")
    total_resolved: int = Field(..., description="Total resolved alerts")
    by_severity: Dict[str, int] = Field(..., description="Alert counts by severity")
    by_dataset: Dict[str, int] = Field(..., description="Alert counts by dataset")
    recent_alerts: List[Alert] = Field(..., description="Recent alerts")
    avg_resolution_time: Optional[float] = Field(None, description="Average resolution time in minutes")
    
    class Config:
        from_attributes = True


class EscalationRule(BaseModel):
    """Alert escalation rule"""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    alert_rule_id: UUID = Field(..., description="Associated alert rule")
    escalation_delay_minutes: int = Field(..., ge=1, description="Minutes before escalation")
    escalation_channels: List[NotificationChannel] = Field(..., description="Escalation notification channels")
    escalation_recipients: List[str] = Field(..., description="Escalation recipients")
    max_escalations: int = Field(3, ge=1, description="Maximum number of escalations")
    is_active: bool = Field(True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
