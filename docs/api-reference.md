# API Reference

Complete documentation for the Intelligent Data Quality Platform REST API.

## Why I Designed the API This Way

When I started building this, I tried to cram everything into a few giant endpoints. Big mistake - debugging became a nightmare and adding new features meant breaking existing ones. So I redesigned it following REST principles I learned from reading the Stripe and GitHub API docs (they're honestly works of art).

**Key decisions I made:**
- **Consistent response format** - Every response follows the same structure so frontend code is predictable
- **Proper HTTP status codes** - Took time to learn these properly instead of returning 200 for everything
- **Pagination everywhere** - Learned this the hard way when my dataset list crashed the browser with 10,000+ items
- **Detailed error messages** - Nothing worse than getting "Error 400" with no context

## Base URL & Authentication

```
Local Development: http://localhost:8000/v1
Demo Environment: https://api.dataquality-demo.com/v1
```

I built JWT-based authentication because sessions don't work well with distributed systems (learned that lesson when I tried to scale horizontally). Every request needs an auth header:

```http
Authorization: Bearer <your-jwt-token>
```

### Getting Your First Token

```http
POST /auth/login
Content-Type: application/json

{
  "email": "your.email@university.edu",
  "password": "your_password"
}
```

**What you get back:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "def50200a54b..."
}
```

**Pro tip I learned:** Access tokens expire in 1 hour, refresh tokens in 7 days. Always implement refresh logic or you'll have angry users getting logged out mid-task.

---

## Core Endpoints

### Datasets API

This is where everything starts - you need datasets before you can check their quality.

#### Get All Your Datasets
```http
GET /datasets?page=1&limit=20&owner=your_user_id&status=active
```

I added filtering because scrolling through hundreds of test datasets gets old fast:
- `owner` - See only your datasets (or your team's)
- `status` - Filter by active/inactive/error states
- `search` - Full-text search across names and descriptions

**Response structure I settled on:**
```json
{
  "data": [
    {
      "id": "dataset_123",
      "name": "customer_transactions",
      "description": "Daily customer transaction data from Stripe",
      "owner": "data_team",
      "schema": {
        "columns": [
          {
            "name": "customer_id", 
            "type": "string", 
            "nullable": false,
            "constraints": ["unique", "not_empty"]
          },
          {
            "name": "amount", 
            "type": "decimal", 
            "nullable": false,
            "min_value": 0.01
          }
        ]
      },
      "status": "active",
      "quality_score": 97.5,
      "row_count": 1500000,
      "last_quality_check": "2024-01-20T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8,
    "has_next": true
  }
}
```

#### Create a New Dataset
```http
POST /datasets
Content-Type: application/json

{
  "name": "user_events",
  "description": "User interaction events from our web app",
  "source_type": "kafka",
  "source_config": {
    "topic": "user_events",
    "bootstrap_servers": "localhost:9092"
  },
  "schema": {
    "columns": [
      {"name": "user_id", "type": "string", "nullable": false},
      {"name": "event_type", "type": "string", "nullable": false},
      {"name": "timestamp", "type": "timestamp", "nullable": false}
    ]
  },
  "quality_rules": [
    {
      "type": "not_null",
      "column": "user_id",
      "severity": "critical"
    },
    {
      "type": "enum_check",
      "column": "event_type",
      "allowed_values": ["click", "view", "purchase"],
      "severity": "high"
    }
  ]
}
```

**What I learned building this:** Validate the schema upfront! I used to accept any schema and fail later during processing. Now I validate column types and constraints immediately.

---

### Quality Checks API

The heart of the system - where the actual data quality magic happens.

#### Run Quality Checks
```http
POST /quality-checks/run
Content-Type: application/json

{
  "dataset_id": "dataset_123",
  "check_types": ["completeness", "uniqueness", "validity"],
  "columns": ["customer_id", "email", "phone"],
  "async": true,
  "sample_size": 100000
}
```

**Why async by default:** Quality checks on large datasets can take minutes. Nobody wants to wait for an HTTP request that long. You get back a job ID and poll for results.

**Response:**
```json
{
  "job_id": "job_789",
  "status": "running",
  "estimated_completion": "2024-01-20T14:35:00Z",
  "progress_url": "/jobs/job_789/status",
  "cancel_url": "/jobs/job_789/cancel"
}
```

#### Get Quality Check Results
```http
GET /quality-checks/results/{job_id}
```

**What a completed check looks like:**
```json
{
  "job_id": "job_789",
  "dataset_id": "dataset_123",
  "status": "completed",
  "overall_score": 94.2,
  "execution_time_seconds": 45,
  "sample_size": 100000,
  "rule_results": [
    {
      "rule_type": "completeness",
      "column": "customer_id",
      "passed": true,
      "score": 100.0,
      "details": {
        "null_count": 0,
        "total_count": 100000,
        "null_percentage": 0.0
      }
    },
    {
      "rule_type": "uniqueness",
      "column": "customer_id", 
      "passed": true,
      "score": 100.0,
      "details": {
        "unique_count": 100000,
        "total_count": 100000,
        "duplicate_count": 0
      }
    },
    {
      "rule_type": "validity",
      "column": "email",
      "passed": false,
      "score": 87.3,
      "details": {
        "valid_count": 87300,
        "invalid_count": 12700,
        "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
        "sample_invalid": ["not-an-email", "missing@", "@nodomain"]
      }
    }
  ],
  "anomalies_detected": [
    {
      "column": "transaction_amount",
      "anomaly_type": "statistical_outlier",
      "confidence": 0.97,
      "description": "Unusually high transaction amounts detected",
      "sample_values": [25000.00, 30000.00, 45000.00]
    }
  ]
}
```

---

### Alerts API

Smart alerting was the hardest part to get right. My first version created 500+ alerts per day. Not helpful.

#### Get Your Alerts
```http
GET /alerts?status=open&severity=critical&assigned_to=me&limit=25
```

**Response with smart prioritization:**
```json
{
  "data": [
    {
      "id": "alert_101",
      "title": "Critical Data Quality Issue in customer_transactions",
      "description": "Customer ID completeness dropped from 100% to 95.2% in last hour",
      "severity": "critical",
      "priority_score": 95,
      "status": "open",
      "created_at": "2024-01-20T14:30:00Z",
      "dataset_id": "dataset_123",
      "affected_columns": ["customer_id"],
      "business_impact": {
        "downstream_systems": ["fraud_detection", "analytics_pipeline"],
        "estimated_affected_records": 7200,
        "potential_revenue_impact": "high"
      },
      "suggested_actions": [
        "Check upstream data source for schema changes",
        "Validate ETL pipeline configuration",
        "Review recent code deployments"
      ],
      "assignee": "data_team",
      "escalation_path": ["data_engineer", "senior_engineer", "data_platform_lead"]
    }
  ],
  "summary": {
    "total_open": 12,
    "critical": 3,
    "high": 5,
    "medium": 4,
    "avg_resolution_time_hours": 2.3
  }
}
```

#### Create Manual Alert
```http
POST /alerts
Content-Type: application/json

{
  "dataset_id": "dataset_123",
  "title": "Investigating unusual data patterns",
  "description": "Saw some weird spikes in user activity, investigating manually",
  "severity": "medium",
  "tags": ["manual_investigation", "user_behavior"]
}
```

---

### Real-Time Features

#### WebSocket for Live Updates
```javascript
// Frontend WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws/quality-updates');

ws.onmessage = function(event) {
  const update = JSON.parse(event.data);
  
  if (update.type === 'quality_check_completed') {
    // Update dashboard with new results
    updateQualityScore(update.dataset_id, update.score);
  } else if (update.type === 'alert_created') {
    // Show notification for new alert
    showNotification(update.alert);
  }
};
```

**Why WebSockets:** Polling sucks for real-time updates. WebSockets let me push updates immediately when quality checks complete or alerts are generated.

---

## Error Handling (Learning from My Mistakes)

### HTTP Status Codes I Used
- `200 OK` - Everything worked
- `201 Created` - New resource created successfully  
- `400 Bad Request` - You sent invalid data (with details on what's wrong)
- `401 Unauthorized` - Bad or missing auth token
- `403 Forbidden` - Valid token but insufficient permissions
- `404 Not Found` - Resource doesn't exist
- `422 Unprocessable Entity` - Valid JSON but business logic errors
- `429 Too Many Requests` - Rate limit hit
- `500 Internal Server Error` - I messed up (hopefully rare!)

### Error Response Format
Every error follows this structure:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid parameters",
    "details": [
      {
        "field": "dataset_id",
        "message": "Dataset ID must be a valid UUID",
        "received": "invalid-id-123"
      },
      {
        "field": "check_types",
        "message": "At least one check type is required",
        "allowed_values": ["completeness", "uniqueness", "validity", "consistency"]
      }
    ],
    "request_id": "req_abc123",
    "timestamp": "2024-01-20T14:30:00Z",
    "docs_url": "https://docs.dataquality-platform.com/api/errors#validation_error"
  }
}
```

**What I learned:** Always include enough context for developers to fix their request without guessing.

---

## Rate Limiting (Because Runaway Scripts Are Real)

- **Standard API calls:** 1000 requests per hour per API key
- **Quality check executions:** 50 per hour (these are expensive!)
- **Bulk operations:** 10 per hour

**Headers you'll see:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1642687200
```

**When you hit the limit:**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please wait before trying again.",
    "retry_after": 3600
  }
}
```

---

## Client Libraries I Built

### Python SDK (My Daily Driver)
```python
from dataquality_client import DataQualityClient

client = DataQualityClient(
    base_url="http://localhost:8000/v1",
    api_key="your_api_key"
)

# Simple quality check
result = client.quality_checks.run(
    dataset_id="dataset_123",
    check_types=["completeness", "uniqueness"]
)

# Wait for completion
final_result = client.quality_checks.wait_for_completion(result.job_id)
print(f"Overall score: {final_result.overall_score}")

# Get recent alerts
alerts = client.alerts.list(status="open", limit=10)
for alert in alerts:
    print(f"{alert.severity}: {alert.title}")
```

### JavaScript SDK (For Frontend Integration)
```javascript
import { DataQualityClient } from '@dataquality/client';

const client = new DataQualityClient({
  baseUrl: 'http://localhost:8000/v1',
  apiKey: 'your_api_key'
});

// Async quality check with progress tracking
const job = await client.qualityChecks.run({
  datasetId: 'dataset_123',
  checkTypes: ['completeness', 'uniqueness']
});

// Subscribe to progress updates
job.onProgress((progress) => {
  console.log(`Progress: ${progress.percentage}%`);
});

const result = await job.wait();
console.log(`Quality score: ${result.overallScore}`);
```

---

## What I'd Improve Next

**If I had more time:**
1. **GraphQL endpoint** - For complex queries with nested data
2. **Bulk operations** - Upload multiple datasets at once
3. **Custom rule engine** - Let users define their own quality rules
4. **Data lineage API** - Track dependencies between datasets
5. **Cost estimation** - Preview compute costs before running checks
6. **Webhook retries** - More robust webhook delivery with exponential backoff

**Performance optimizations:**
- Response caching with Redis
- Database query optimization
- API response compression
- Connection pooling improvements

This API evolved a lot as I learned what developers actually need vs. what I thought they'd want. The key was making it easy to get started but powerful enough for complex use cases.

---
