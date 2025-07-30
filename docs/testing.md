# Testing Strategy

## Overview

This document outlines the comprehensive testing strategy for the Intelligent Data Quality Platform, including unit tests, integration tests, performance tests, and end-to-end testing approaches.

## Testing Pyramid

```
    /\
   /  \  E2E Tests (5%)
  /____\
 /      \  Integration Tests (25%)
/________\
\        /  Unit Tests (70%)
 \______/
```

## Unit Testing

### Backend Unit Tests

#### Quality Service Tests

```python
# tests/test_quality_service.py
import pytest
import pandas as pd
from unittest.mock import Mock, patch
from app.services.quality_service import QualityService
from app.models.quality import QualityCheck, QualityRule

class TestQualityService:
    
    @pytest.fixture
    def quality_service(self):
        return QualityService()
    
    @pytest.fixture
    def sample_dataframe(self):
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', None, 'David', 'Eve'],
            'age': [25, 30, 35, None, 45],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com', 'david@test.com', 'eve@test.com']
        })
    
    def test_null_check_validation(self, quality_service, sample_dataframe):
        """Test null value detection"""
        rule = QualityRule(
            rule_type="null_check",
            column="name",
            threshold=0.1  # Allow 10% null values
        )
        
        result = quality_service.execute_rule(sample_dataframe, rule)
        
        assert result.passed is False  # 20% null values exceed threshold
        assert result.null_percentage == 0.2
        assert "name" in result.failed_columns
    
    def test_uniqueness_validation(self, quality_service, sample_dataframe):
        """Test uniqueness constraint validation"""
        rule = QualityRule(
            rule_type="uniqueness_check",
            column="id",
            threshold=1.0  # 100% unique values required
        )
        
        result = quality_service.execute_rule(sample_dataframe, rule)
        
        assert result.passed is True
        assert result.uniqueness_ratio == 1.0
    
    def test_pattern_validation(self, quality_service, sample_dataframe):
        """Test pattern matching validation"""
        rule = QualityRule(
            rule_type="pattern_check",
            column="email",
            pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        
        result = quality_service.execute_rule(sample_dataframe, rule)
        
        assert result.passed is True
        assert result.pattern_match_ratio == 1.0
    
    @patch('app.services.quality_service.get_spark_session')
    def test_spark_integration(self, mock_spark, quality_service):
        """Test Spark DataFrame processing"""
        mock_spark_session = Mock()
        mock_spark.return_value = mock_spark_session
        
        # Mock Spark DataFrame
        mock_df = Mock()
        mock_df.count.return_value = 1000
        mock_df.select.return_value.distinct.return_value.count.return_value = 950
        
        result = quality_service.check_data_quality_spark(mock_df, [])
        
        assert mock_spark_session.called
        assert result is not None
    
    def test_anomaly_detection_integration(self, quality_service, sample_dataframe):
        """Test anomaly detection integration"""
        with patch('app.ml.anomaly_detection.EnsembleAnomalyDetector') as mock_detector:
            mock_instance = Mock()
            mock_instance.detect_anomalies.return_value = [0, 0, 1, 0, 0]  # One anomaly
            mock_detector.return_value = mock_instance
            
            anomalies = quality_service.detect_anomalies(sample_dataframe)
            
            assert len(anomalies) == 1
            assert anomalies[0]['row_index'] == 2
```

#### Alert Service Tests

```python
# tests/test_alert_service.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.alert_service import AlertService
from app.models.alert import Alert, AlertSeverity, AlertStatus

class TestAlertService:
    
    @pytest.fixture
    def alert_service(self):
        return AlertService()
    
    @pytest.fixture
    def sample_alert(self):
        return Alert(
            title="Data Quality Issue",
            message="High null percentage detected",
            severity=AlertSeverity.HIGH,
            dataset_id="test-dataset",
            rule_id="null-check-1"
        )
    
    @pytest.mark.asyncio
    async def test_create_alert(self, alert_service, sample_alert):
        """Test alert creation"""
        with patch.object(alert_service, 'db_session') as mock_db:
            mock_db.add = Mock()
            mock_db.commit = AsyncMock()
            
            result = await alert_service.create_alert(sample_alert)
            
            assert result.id is not None
            assert result.status == AlertStatus.OPEN
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_priority_calculation(self, alert_service):
        """Test alert priority calculation"""
        high_priority_alert = Alert(
            severity=AlertSeverity.CRITICAL,
            dataset_id="important-dataset"
        )
        
        low_priority_alert = Alert(
            severity=AlertSeverity.LOW,
            dataset_id="test-dataset"
        )
        
        high_priority = await alert_service.calculate_priority(high_priority_alert)
        low_priority = await alert_service.calculate_priority(low_priority_alert)
        
        assert high_priority > low_priority
    
    @pytest.mark.asyncio
    async def test_notification_sending(self, alert_service, sample_alert):
        """Test notification delivery"""
        with patch.object(alert_service, 'notification_client') as mock_client:
            mock_client.send_email = AsyncMock()
            mock_client.send_slack = AsyncMock()
            
            await alert_service.send_notifications(sample_alert)
            
            mock_client.send_email.assert_called_once()
            mock_client.send_slack.assert_called_once()
    
    def test_alert_aggregation(self, alert_service):
        """Test alert aggregation logic"""
        alerts = [
            Alert(title="Issue 1", dataset_id="dataset-1", rule_id="rule-1"),
            Alert(title="Issue 2", dataset_id="dataset-1", rule_id="rule-1"),
            Alert(title="Issue 3", dataset_id="dataset-2", rule_id="rule-1"),
        ]
        
        aggregated = alert_service.aggregate_similar_alerts(alerts, time_window=300)
        
        assert len(aggregated) == 2  # Two groups: dataset-1 and dataset-2
        assert aggregated[0]['count'] == 2
        assert aggregated[1]['count'] == 1
```

#### ML Model Tests

```python
# tests/test_anomaly_detection.py
import pytest
import numpy as np
import pandas as pd
from app.ml.anomaly_detection.ensemble_detector import EnsembleAnomalyDetector

class TestAnomalyDetection:
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample data with known anomalies"""
        np.random.seed(42)
        normal_data = np.random.normal(0, 1, (1000, 5))
        
        # Add some anomalies
        anomalies = np.random.normal(5, 1, (50, 5))
        
        data = np.vstack([normal_data, anomalies])
        np.random.shuffle(data)
        
        return pd.DataFrame(data, columns=['feature_1', 'feature_2', 'feature_3', 'feature_4', 'feature_5'])
    
    def test_detector_initialization(self):
        """Test detector initialization"""
        detector = EnsembleAnomalyDetector()
        
        assert detector.isolation_forest is not None
        assert detector.local_outlier_factor is not None
        assert detector.one_class_svm is not None
    
    def test_anomaly_detection(self, sample_data):
        """Test anomaly detection accuracy"""
        detector = EnsembleAnomalyDetector()
        
        # Fit and predict
        detector.fit(sample_data)
        anomalies = detector.detect_anomalies(sample_data)
        
        # Check results
        assert len(anomalies) == len(sample_data)
        assert all(score >= 0 and score <= 1 for score in anomalies)
        
        # Should detect some anomalies (not too few, not too many)
        anomaly_count = sum(1 for score in anomalies if score > 0.5)
        assert 10 <= anomaly_count <= 200  # Reasonable range
    
    def test_feature_importance(self, sample_data):
        """Test feature importance calculation"""
        detector = EnsembleAnomalyDetector()
        detector.fit(sample_data)
        
        importance = detector.get_feature_importance()
        
        assert len(importance) == len(sample_data.columns)
        assert all(imp >= 0 for imp in importance.values())
        assert abs(sum(importance.values()) - 1.0) < 0.01  # Should sum to 1
    
    def test_model_persistence(self, sample_data, tmp_path):
        """Test model saving and loading"""
        detector = EnsembleAnomalyDetector()
        detector.fit(sample_data)
        
        # Save model
        model_path = tmp_path / "test_model.pkl"
        detector.save_model(str(model_path))
        
        # Load model
        new_detector = EnsembleAnomalyDetector()
        new_detector.load_model(str(model_path))
        
        # Compare predictions
        original_predictions = detector.detect_anomalies(sample_data[:10])
        loaded_predictions = new_detector.detect_anomalies(sample_data[:10])
        
        np.testing.assert_array_almost_equal(original_predictions, loaded_predictions)
```

### Frontend Unit Tests

```typescript
// tests/components/QualityDashboard.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import QualityDashboard from '../src/components/QualityDashboard';
import { mockQualityData } from './mocks/qualityData';

// Mock API calls
jest.mock('../src/api/qualityApi', () => ({
  fetchQualityMetrics: jest.fn(),
  fetchDatasetList: jest.fn(),
}));

describe('QualityDashboard', () => {
  let queryClient: QueryClient;
  
  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
  });
  
  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    );
  };
  
  test('renders dashboard with quality metrics', async () => {
    const mockApi = require('../src/api/qualityApi');
    mockApi.fetchQualityMetrics.mockResolvedValue(mockQualityData);
    
    renderWithProviders(<QualityDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Data Quality Overview')).toBeInTheDocument();
      expect(screen.getByText('Overall Score: 85%')).toBeInTheDocument();
    });
  });
  
  test('handles dataset selection', async () => {
    const mockApi = require('../src/api/qualityApi');
    mockApi.fetchDatasetList.mockResolvedValue([
      { id: '1', name: 'Dataset 1' },
      { id: '2', name: 'Dataset 2' },
    ]);
    
    renderWithProviders(<QualityDashboard />);
    
    const dropdown = await screen.findByLabelText('Select Dataset');
    fireEvent.click(dropdown);
    
    const option = await screen.findByText('Dataset 1');
    fireEvent.click(option);
    
    expect(mockApi.fetchQualityMetrics).toHaveBeenCalledWith('1');
  });
  
  test('displays error state correctly', async () => {
    const mockApi = require('../src/api/qualityApi');
    mockApi.fetchQualityMetrics.mockRejectedValue(new Error('API Error'));
    
    renderWithProviders(<QualityDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Error loading quality metrics')).toBeInTheDocument();
    });
  });
});
```

## Integration Testing

### API Integration Tests

```python
# tests/integration/test_api_integration.py
import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.core.database import get_test_db

class TestQualityAPI:
    
    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.fixture
    def test_dataset(self):
        return {
            "name": "Test Dataset",
            "description": "Integration test dataset",
            "source_type": "csv",
            "connection_params": {
                "file_path": "/test/data.csv"
            }
        }
    
    @pytest.mark.asyncio
    async def test_dataset_creation_workflow(self, client, test_dataset):
        """Test complete dataset creation workflow"""
        
        # 1. Create dataset
        response = await client.post("/api/v1/datasets/", json=test_dataset)
        assert response.status_code == 201
        dataset_id = response.json()["id"]
        
        # 2. Configure quality rules
        quality_rules = [
            {
                "rule_type": "null_check",
                "column": "name",
                "threshold": 0.1
            },
            {
                "rule_type": "uniqueness_check", 
                "column": "id",
                "threshold": 1.0
            }
        ]
        
        response = await client.post(
            f"/api/v1/datasets/{dataset_id}/quality-rules",
            json={"rules": quality_rules}
        )
        assert response.status_code == 201
        
        # 3. Execute quality check
        response = await client.post(f"/api/v1/quality/check/{dataset_id}")
        assert response.status_code == 202
        check_id = response.json()["check_id"]
        
        # 4. Wait for completion and get results
        await asyncio.sleep(2)  # Wait for processing
        
        response = await client.get(f"/api/v1/quality/results/{check_id}")
        assert response.status_code == 200
        
        results = response.json()
        assert results["status"] == "completed"
        assert "overall_score" in results
        assert "rule_results" in results
    
    @pytest.mark.asyncio
    async def test_alert_generation_workflow(self, client, test_dataset):
        """Test alert generation from quality issues"""
        
        # Create dataset with quality issues
        dataset_with_issues = {
            **test_dataset,
            "data": [
                {"id": 1, "name": "Alice", "age": 25},
                {"id": 2, "name": None, "age": 30},  # Null value
                {"id": 3, "name": None, "age": None}, # Multiple nulls
            ]
        }
        
        response = await client.post("/api/v1/datasets/", json=dataset_with_issues)
        dataset_id = response.json()["id"]
        
        # Run quality check
        response = await client.post(f"/api/v1/quality/check/{dataset_id}")
        check_id = response.json()["check_id"]
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Check for generated alerts
        response = await client.get(f"/api/v1/alerts/?dataset_id={dataset_id}")
        assert response.status_code == 200
        
        alerts = response.json()
        assert len(alerts) > 0
        assert any(alert["severity"] in ["HIGH", "CRITICAL"] for alert in alerts)
```

### Database Integration Tests

```python
# tests/integration/test_database_integration.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.models.quality import QualityCheck, QualityResult
from app.models.dataset import Dataset

class TestDatabaseIntegration:
    
    @pytest.fixture
    def db_session(self):
        # Create test database
        engine = create_engine("sqlite:///./test.db")
        Base.metadata.create_all(bind=engine)
        
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = TestingSessionLocal()
        
        yield session
        
        session.close()
        Base.metadata.drop_all(bind=engine)
    
    def test_quality_check_persistence(self, db_session):
        """Test quality check data persistence"""
        
        # Create test dataset
        dataset = Dataset(
            name="Test Dataset",
            description="Test description",
            source_type="csv"
        )
        db_session.add(dataset)
        db_session.commit()
        
        # Create quality check
        quality_check = QualityCheck(
            dataset_id=dataset.id,
            rules=[
                {"rule_type": "null_check", "column": "name"},
                {"rule_type": "uniqueness_check", "column": "id"}
            ]
        )
        db_session.add(quality_check)
        db_session.commit()
        
        # Create quality results
        result = QualityResult(
            check_id=quality_check.id,
            overall_score=0.85,
            rule_results={
                "null_check": {"passed": True, "score": 0.9},
                "uniqueness_check": {"passed": False, "score": 0.8}
            }
        )
        db_session.add(result)
        db_session.commit()
        
        # Verify persistence
        retrieved_result = db_session.query(QualityResult).filter_by(
            check_id=quality_check.id
        ).first()
        
        assert retrieved_result is not None
        assert retrieved_result.overall_score == 0.85
        assert len(retrieved_result.rule_results) == 2
    
    def test_transaction_rollback(self, db_session):
        """Test transaction rollback on errors"""
        
        try:
            # Start transaction
            dataset = Dataset(name="Test Dataset")
            db_session.add(dataset)
            
            # Cause an error (invalid foreign key)
            invalid_check = QualityCheck(
                dataset_id=999999,  # Non-existent dataset
                rules=[]
            )
            db_session.add(invalid_check)
            db_session.commit()
            
        except Exception:
            db_session.rollback()
        
        # Verify rollback
        count = db_session.query(Dataset).count()
        assert count == 0
```

## Performance Testing

### Load Testing with Locust

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between
import json
import random

class DataQualityUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Setup test data"""
        self.dataset_ids = []
        self.create_test_datasets()
    
    def create_test_datasets(self):
        """Create test datasets for load testing"""
        for i in range(5):
            dataset_data = {
                "name": f"Load Test Dataset {i}",
                "description": f"Dataset for load testing {i}",
                "source_type": "csv"
            }
            
            response = self.client.post("/api/v1/datasets/", json=dataset_data)
            if response.status_code == 201:
                self.dataset_ids.append(response.json()["id"])
    
    @task(3)
    def get_quality_metrics(self):
        """Test quality metrics endpoint performance"""
        if self.dataset_ids:
            dataset_id = random.choice(self.dataset_ids)
            self.client.get(f"/api/v1/quality/metrics/{dataset_id}")
    
    @task(2)
    def list_datasets(self):
        """Test dataset listing performance"""
        self.client.get("/api/v1/datasets/")
    
    @task(1)
    def run_quality_check(self):
        """Test quality check execution performance"""
        if self.dataset_ids:
            dataset_id = random.choice(self.dataset_ids)
            self.client.post(f"/api/v1/quality/check/{dataset_id}")
    
    @task(1)
    def get_alerts(self):
        """Test alert retrieval performance"""
        self.client.get("/api/v1/alerts/?limit=50")

# Run with: locust -f locustfile.py --host=http://localhost:8000
```

### Spark Performance Tests

```python
# tests/performance/test_spark_performance.py
import pytest
import time
from pyspark.sql import SparkSession
from app.utils.spark_utils import SparkDataProcessor

class TestSparkPerformance:
    
    @pytest.fixture(scope="class")
    def spark_session(self):
        spark = SparkSession.builder \
            .appName("PerformanceTest") \
            .config("spark.sql.adaptive.enabled", "true") \
            .getOrCreate()
        yield spark
        spark.stop()
    
    def test_large_dataset_processing(self, spark_session):
        """Test processing performance with large datasets"""
        
        # Generate large test dataset (1M rows)
        data_size = 1_000_000
        df = spark_session.range(data_size).selectExpr(
            "id",
            "rand() * 100 as value",
            "if(rand() < 0.1, null, concat('name_', id)) as name",
            "current_timestamp() as created_at"
        )
        
        processor = SparkDataProcessor(spark_session)
        
        start_time = time.time()
        
        # Run quality checks
        null_check_result = processor.check_null_percentage(df, "name")
        uniqueness_result = processor.check_uniqueness(df, "id")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Performance assertions
        assert processing_time < 30  # Should complete within 30 seconds
        assert null_check_result is not None
        assert uniqueness_result is not None
        
        # Log performance metrics
        print(f"Processed {data_size} rows in {processing_time:.2f} seconds")
        print(f"Throughput: {data_size / processing_time:.0f} rows/second")
    
    def test_memory_usage(self, spark_session):
        """Test memory usage with different dataset sizes"""
        
        sizes = [10_000, 100_000, 1_000_000]
        processor = SparkDataProcessor(spark_session)
        
        for size in sizes:
            df = spark_session.range(size).selectExpr(
                "id",
                "rand() * 100 as value"
            )
            
            # Cache DataFrame and force computation
            df.cache()
            df.count()
            
            # Get memory usage
            storage_level = df.storageLevel
            print(f"Dataset size: {size}, Storage level: {storage_level}")
            
            # Clean up
            df.unpersist()
```

## End-to-End Testing

### Browser Testing with Playwright

```typescript
// tests/e2e/quality-dashboard.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Quality Dashboard E2E', () => {
  
  test.beforeEach(async ({ page }) => {
    // Setup test data
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });
  
  test('should display quality metrics correctly', async ({ page }) => {
    // Navigate to dashboard
    await page.click('[data-testid="dashboard-nav"]');
    
    // Wait for data to load
    await page.waitForSelector('[data-testid="quality-score"]');
    
    // Verify quality score display
    const qualityScore = await page.textContent('[data-testid="quality-score"]');
    expect(qualityScore).toMatch(/\d+%/);
    
    // Verify charts are rendered
    await expect(page.locator('[data-testid="quality-trend-chart"]')).toBeVisible();
    await expect(page.locator('[data-testid="rule-breakdown-chart"]')).toBeVisible();
  });
  
  test('should filter data by dataset', async ({ page }) => {
    await page.click('[data-testid="dashboard-nav"]');
    
    // Open dataset filter
    await page.click('[data-testid="dataset-filter"]');
    await page.click('[data-testid="dataset-option-1"]');
    
    // Wait for filtered data to load
    await page.waitForLoadState('networkidle');
    
    // Verify URL contains filter parameter
    expect(page.url()).toContain('dataset=1');
    
    // Verify filtered data is displayed
    const datasetName = await page.textContent('[data-testid="selected-dataset"]');
    expect(datasetName).toContain('Dataset 1');
  });
  
  test('should navigate to alert details', async ({ page }) => {
    await page.click('[data-testid="alerts-nav"]');
    
    // Wait for alerts to load
    await page.waitForSelector('[data-testid="alert-item"]');
    
    // Click on first alert
    await page.click('[data-testid="alert-item"]:first-child');
    
    // Verify navigation to alert details
    await expect(page).toHaveURL(/\/alerts\/\d+/);
    
    // Verify alert details are displayed
    await expect(page.locator('[data-testid="alert-title"]')).toBeVisible();
    await expect(page.locator('[data-testid="alert-description"]')).toBeVisible();
  });
  
  test('should handle error states gracefully', async ({ page }) => {
    // Mock API error
    await page.route('/api/v1/quality/metrics/*', route => {
      route.fulfill({ status: 500, body: 'Internal Server Error' });
    });
    
    await page.reload();
    
    // Verify error message is displayed
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
    
    // Test retry functionality
    await page.unroute('/api/v1/quality/metrics/*');
    await page.click('[data-testid="retry-button"]');
    
    // Verify data loads successfully after retry
    await page.waitForSelector('[data-testid="quality-score"]');
  });
});
```

## Test Configuration

### pytest Configuration

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    --asyncio-mode=auto
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    e2e: End-to-end tests
    slow: Slow running tests
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

### Jest Configuration

```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.tsx',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  transform: {
    '^.+\\.tsx?$': 'ts-jest',
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
};
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=app --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
  
  integration-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run integration tests
      env:
        DATABASE_URL: postgresql://postgres:test@localhost/test_db
        REDIS_URL: redis://localhost:6379
      run: |
        pytest tests/integration/ -v
  
  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '16'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install frontend dependencies
      working-directory: ./frontend
      run: npm ci
    
    - name: Run frontend tests
      working-directory: ./frontend
      run: |
        npm run test:coverage
        npm run lint
        npm run type-check
  
  e2e-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Start services with Docker Compose
      run: |
        docker-compose -f docker-compose.test.yml up -d
        docker-compose -f docker-compose.test.yml exec -T backend python -m pytest tests/e2e/ -v
    
    - name: Cleanup
      if: always()
      run: docker-compose -f docker-compose.test.yml down
```

## Test Data Management

### Test Fixtures

```python
# tests/fixtures/data_fixtures.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class TestDataFactory:
    """Factory for generating test data"""
    
    @staticmethod
    def create_clean_dataset(rows=1000):
        """Create a clean dataset with no quality issues"""
        np.random.seed(42)
        
        return pd.DataFrame({
            'id': range(1, rows + 1),
            'name': [f'User_{i}' for i in range(1, rows + 1)],
            'email': [f'user{i}@example.com' for i in range(1, rows + 1)],
            'age': np.random.randint(18, 80, rows),
            'created_at': pd.date_range(
                start=datetime.now() - timedelta(days=365),
                periods=rows,
                freq='H'
            )
        })
    
    @staticmethod
    def create_dataset_with_nulls(rows=1000, null_percentage=0.1):
        """Create dataset with null values"""
        df = TestDataFactory.create_clean_dataset(rows)
        
        # Add null values
        null_count = int(rows * null_percentage)
        null_indices = np.random.choice(rows, null_count, replace=False)
        df.loc[null_indices, 'name'] = None
        
        return df
    
    @staticmethod
    def create_dataset_with_duplicates(rows=1000, duplicate_percentage=0.05):
        """Create dataset with duplicate values"""
        df = TestDataFactory.create_clean_dataset(rows)
        
        # Add duplicate IDs
        duplicate_count = int(rows * duplicate_percentage)
        duplicate_indices = np.random.choice(rows, duplicate_count, replace=False)
        df.loc[duplicate_indices, 'id'] = df.loc[duplicate_indices[0], 'id']
        
        return df
```

## Test Reporting

### Coverage Reports

```bash
#!/bin/bash
# scripts/run_tests.sh

echo "Running comprehensive test suite..."

# Backend tests with coverage
echo "Running backend tests..."
cd backend
pytest tests/ \
    --cov=app \
    --cov-report=html:htmlcov \
    --cov-report=term-missing \
    --cov-report=xml \
    --junitxml=test-results.xml

# Frontend tests with coverage
echo "Running frontend tests..."
cd ../frontend
npm run test:coverage

# E2E tests
echo "Running E2E tests..."
cd ..
docker-compose -f docker-compose.test.yml up -d
sleep 30  # Wait for services to start
npx playwright test
docker-compose -f docker-compose.test.yml down

# Generate combined coverage report
echo "Generating combined coverage report..."
python scripts/combine_coverage.py

echo "Test suite completed!"
echo "View backend coverage: backend/htmlcov/index.html"
echo "View frontend coverage: frontend/coverage/lcov-report/index.html"
echo "View E2E test results: playwright-report/index.html"
```

This comprehensive testing strategy ensures:

1. **High Code Coverage**: Unit tests cover core business logic
2. **Integration Reliability**: API and database integration tests
3. **Performance Validation**: Load testing and performance benchmarks
4. **User Experience**: End-to-end testing of complete workflows
5. **Continuous Quality**: Automated testing in CI/CD pipeline
6. **Test Data Management**: Structured test data creation and cleanup
7. **Comprehensive Reporting**: Coverage reports and test metrics

The testing strategy scales with the application and provides confidence in deploying enterprise-grade data quality monitoring platform.
