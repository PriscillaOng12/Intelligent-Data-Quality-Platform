# API Reference

Complete documentation for the Intelligent Data Quality Platform REST API.

## Base URL
```
Production: https://api.dataquality-platform.com/v1
Development: http://localhost:8000/v1
```

## Authentication

### Bearer Token Authentication
All API requests require a valid JWT token in the Authorization header:
```http
Authorization: Bearer <your-jwt-token>
```

### Getting a Token
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@company.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "def50200a54b..."
}
```

---

## Datasets API

### List Datasets
```http
GET /datasets?page=1&limit=20&owner=user123&status=active
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20, max: 100)
- `owner` (string): Filter by dataset owner
- `status` (string): Filter by status (active, inactive, error)
- `search` (string): Search by name or description

**Response:**
```json
{
  "data": [
    {
      "id": "dataset_123",
      "name": "customer_transactions",
      "description": "Daily customer transaction data",
      "owner": "data_team",
      "schema": {
        "columns": [
          {"name": "customer_id", "type": "string", "nullable": false},
          {"name": "amount", "type": "decimal", "nullable": false},
          {"name": "timestamp", "type": "timestamp", "nullable": false}
        ]
      },
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-20T14:45:00Z",
      "last_quality_check": "2024-01-20T14:30:00Z",
      "quality_score": 97.5,
      "row_count": 1500000,
      "size_bytes": 256000000
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

### Get Dataset Details
```http
GET /datasets/{dataset_id}
```

**Response:**
```json
{
  "id": "dataset_123",
  "name": "customer_transactions",
  "description": "Daily customer transaction data",
  "owner": "data_team",
  "tags": ["finance", "customer", "production"],
  "schema": {
    "columns": [
      {
        "name": "customer_id",
        "type": "string",
        "nullable": false,
        "constraints": ["unique", "not_empty"]
      }
    ]
  },
  "quality_metrics": {
    "completeness": 99.2,
    "uniqueness": 100.0,
    "validity": 98.7,
    "consistency": 97.8,
    "overall_score": 97.5
  },
  "lineage": {
    "upstream": ["raw_transactions", "customer_master"],
    "downstream": ["analytics_mart", "ml_features"]
  }
}
```

### Create Dataset
```http
POST /datasets
Content-Type: application/json

{
  "name": "new_dataset",
  "description": "Description of the new dataset",
  "owner": "data_team",
  "source_type": "kafka",
  "source_config": {
    "topic": "customer_events",
    "bootstrap_servers": "kafka:9092"
  },
  "schema": {
    "columns": [
      {"name": "id", "type": "string", "nullable": false},
      {"name": "event_type", "type": "string", "nullable": false}
    ]
  },
  "quality_rules": [
    {
      "type": "not_null",
      "column": "id",
      "severity": "critical"
    }
  ]
}
```

---

## Quality Checks API

### List Quality Checks
```http
GET /quality-checks?dataset_id=dataset_123&status=failed&limit=50
```

**Query Parameters:**
- `dataset_id` (string): Filter by dataset
- `status` (string): passed, failed, warning, running
- `check_type` (string): completeness, uniqueness, validity, custom
- `start_date` (ISO datetime): Filter from date
- `end_date` (ISO datetime): Filter to date

**Response:**
```json
{
  "data": [
    {
      "id": "check_456",
      "dataset_id": "dataset_123",
      "check_type": "completeness",
      "column": "customer_id",
      "rule": "not_null",
      "status": "failed",
      "result": {
        "expected": 100.0,
        "actual": 98.5,
        "threshold": 99.0,
        "failed_rows": 2250,
        "total_rows": 150000
      },
      "severity": "critical",
      "executed_at": "2024-01-20T14:30:00Z",
      "execution_time_ms": 1250
    }
  ]
}
```

### Run Quality Check
```http
POST /quality-checks/run
Content-Type: application/json

{
  "dataset_id": "dataset_123",
  "check_types": ["completeness", "uniqueness"],
  "columns": ["customer_id", "email"],
  "async": true
}
```

**Response:**
```json
{
  "job_id": "job_789",
  "status": "running",
  "estimated_completion": "2024-01-20T14:35:00Z",
  "progress_url": "/jobs/job_789/status"
}
```

---

## Alerts API

### List Alerts
```http
GET /alerts?status=open&severity=critical&limit=25
```

**Response:**
```json
{
  "data": [
    {
      "id": "alert_101",
      "dataset_id": "dataset_123",
      "title": "Critical Data Quality Issue",
      "description": "Customer ID completeness dropped below 99%",
      "severity": "critical",
      "status": "open",
      "created_at": "2024-01-20T14:30:00Z",
      "updated_at": "2024-01-20T14:30:00Z",
      "assignee": "data_team",
      "tags": ["data_quality", "customer_data"],
      "related_checks": ["check_456"],
      "impact_assessment": {
        "affected_rows": 2250,
        "downstream_datasets": 5,
        "estimated_business_impact": "high"
      }
    }
  ]
}
```

### Create Alert
```http
POST /alerts
Content-Type: application/json

{
  "dataset_id": "dataset_123",
  "title": "Custom Alert",
  "description": "Manual alert for investigation",
  "severity": "medium",
  "assignee": "data_engineer",
  "tags": ["manual", "investigation"]
}
```

### Update Alert Status
```http
PATCH /alerts/{alert_id}
Content-Type: application/json

{
  "status": "resolved",
  "resolution_notes": "Fixed upstream data source configuration",
  "resolved_by": "john.doe"
}
```

---

## Data Lineage API

### Get Lineage Graph
```http
GET /lineage/{dataset_id}?depth=3&direction=both
```

**Query Parameters:**
- `depth` (int): How many levels to traverse (default: 2, max: 5)
- `direction` (string): upstream, downstream, both (default: both)
- `include_metrics` (bool): Include quality metrics for each node

**Response:**
```json
{
  "center_node": {
    "id": "dataset_123",
    "name": "customer_transactions",
    "type": "dataset"
  },
  "nodes": [
    {
      "id": "raw_transactions",
      "name": "Raw Transaction Stream",
      "type": "source",
      "quality_score": 85.2
    },
    {
      "id": "analytics_mart",
      "name": "Customer Analytics Mart",
      "type": "target",
      "quality_score": 97.8
    }
  ],
  "edges": [
    {
      "source": "raw_transactions",
      "target": "dataset_123",
      "type": "data_flow",
      "transformation": "ETL Pipeline v2.1",
      "last_updated": "2024-01-20T14:00:00Z"
    }
  ]
}
```

### Impact Analysis
```http
GET /lineage/{dataset_id}/impact?change_type=schema_change
```

**Response:**
```json
{
  "impact_summary": {
    "affected_datasets": 12,
    "affected_pipelines": 5,
    "affected_dashboards": 8,
    "estimated_fix_time": "4 hours"
  },
  "affected_assets": [
    {
      "id": "analytics_mart",
      "name": "Customer Analytics Mart",
      "type": "dataset",
      "impact_level": "high",
      "required_actions": ["Update schema", "Reprocess last 7 days"]
    }
  ]
}
```

---

## Metrics API

### Get Quality Metrics
```http
GET /metrics/quality?dataset_id=dataset_123&timeframe=7d&aggregation=daily
```

**Query Parameters:**
- `dataset_id` (string): Target dataset
- `timeframe` (string): 1h, 1d, 7d, 30d, 90d
- `aggregation` (string): hourly, daily, weekly
- `metrics` (array): completeness, uniqueness, validity, consistency

**Response:**
```json
{
  "dataset_id": "dataset_123",
  "timeframe": "7d",
  "metrics": [
    {
      "date": "2024-01-20",
      "completeness": 99.2,
      "uniqueness": 100.0,
      "validity": 98.7,
      "consistency": 97.8,
      "overall_score": 97.5,
      "row_count": 150000
    }
  ],
  "trends": {
    "completeness": {"direction": "up", "change_percent": 1.2},
    "overall_score": {"direction": "stable", "change_percent": 0.1}
  }
}
```

### Get Performance Metrics
```http
GET /metrics/performance?component=spark&timeframe=1d
```

**Response:**
```json
{
  "component": "spark",
  "metrics": [
    {
      "timestamp": "2024-01-20T14:00:00Z",
      "cpu_usage": 75.2,
      "memory_usage": 68.5,
      "active_jobs": 12,
      "completed_jobs": 1450,
      "failed_jobs": 2,
      "avg_job_duration_ms": 15000
    }
  ]
}
```

---

## Anomaly Detection API

### Get Anomalies
```http
GET /anomalies?dataset_id=dataset_123&severity=high&timeframe=24h
```

**Response:**
```json
{
  "data": [
    {
      "id": "anomaly_201",
      "dataset_id": "dataset_123",
      "column": "transaction_amount",
      "anomaly_type": "statistical_outlier",
      "severity": "high",
      "confidence": 0.95,
      "detected_at": "2024-01-20T14:15:00Z",
      "details": {
        "method": "isolation_forest",
        "anomaly_score": 0.85,
        "expected_range": [10, 5000],
        "actual_value": 25000,
        "context": "99.5% of values are below $5000"
      },
      "suggested_actions": [
        "Verify transaction legitimacy",
        "Check for data entry errors",
        "Review fraud detection rules"
      ]
    }
  ]
}
```

### Configure Anomaly Detection
```http
POST /anomalies/configure
Content-Type: application/json

{
  "dataset_id": "dataset_123",
  "column": "transaction_amount",
  "method": "isolation_forest",
  "sensitivity": 0.1,
  "training_data_days": 30,
  "retraining_frequency": "weekly",
  "alert_threshold": 0.8
}
```

---

## Jobs API

### List Jobs
```http
GET /jobs?status=running&job_type=quality_check
```

### Get Job Status
```http
GET /jobs/{job_id}
```

**Response:**
```json
{
  "id": "job_789",
  "type": "quality_check",
  "status": "completed",
  "progress": 100,
  "started_at": "2024-01-20T14:30:00Z",
  "completed_at": "2024-01-20T14:32:15Z",
  "duration_ms": 135000,
  "result": {
    "checks_run": 25,
    "checks_passed": 23,
    "checks_failed": 2,
    "alerts_generated": 1
  }
}
```

---

## Error Handling

### HTTP Status Codes
- `200 OK` - Success
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation errors
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid parameters",
    "details": [
      {
        "field": "dataset_id",
        "message": "Dataset ID is required"
      }
    ],
    "request_id": "req_abc123",
    "timestamp": "2024-01-20T14:30:00Z"
  }
}
```

---

## Rate Limiting

- **Rate Limit:** 1000 requests per hour per API key
- **Burst Limit:** 100 requests per minute
- **Headers:**
  - `X-RateLimit-Limit`: Total requests allowed
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: When the rate limit resets

---

## SDK Examples

### Python SDK
```python
from dataquality_client import DataQualityClient

client = DataQualityClient(
    base_url="https://api.dataquality-platform.com/v1",
    api_key="your_api_key"
)

# Get datasets
datasets = client.datasets.list(owner="data_team", status="active")

# Run quality check
job = client.quality_checks.run(
    dataset_id="dataset_123",
    check_types=["completeness", "uniqueness"]
)

# Get anomalies
anomalies = client.anomalies.list(
    dataset_id="dataset_123",
    severity="high",
    timeframe="24h"
)
```

### JavaScript SDK
```javascript
import { DataQualityClient } from '@dataquality/client';

const client = new DataQualityClient({
  baseUrl: 'https://api.dataquality-platform.com/v1',
  apiKey: 'your_api_key'
});

// Get quality metrics
const metrics = await client.metrics.getQuality({
  datasetId: 'dataset_123',
  timeframe: '7d'
});

// Create alert
const alert = await client.alerts.create({
  datasetId: 'dataset_123',
  title: 'Data Quality Issue',
  severity: 'high'
});
```

---

## Webhooks

### Configuring Webhooks
```http
POST /webhooks
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["quality_check.failed", "anomaly.detected"],
  "secret": "webhook_secret_key",
  "active": true
}
```

### Webhook Events
- `quality_check.started`
- `quality_check.completed`
- `quality_check.failed`
- `anomaly.detected`
- `alert.created`
- `alert.resolved`
- `dataset.created`
- `dataset.updated`

### Webhook Payload Example
```json
{
  "event": "quality_check.failed",
  "timestamp": "2024-01-20T14:30:00Z",
  "data": {
    "check_id": "check_456",
    "dataset_id": "dataset_123",
    "check_type": "completeness",
    "status": "failed",
    "result": {
      "expected": 100.0,
      "actual": 98.5
    }
  }
}
```

---

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:
- **Interactive Docs:** http://localhost:8000/docs
- **OpenAPI JSON:** http://localhost:8000/openapi.json
- **ReDoc:** http://localhost:8000/redoc

For integration with tools like Postman, Insomnia, or code generators, import the OpenAPI specification directly.
