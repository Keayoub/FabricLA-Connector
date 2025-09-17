"""
Configuration for test environment

Shared configuration and fixtures for Fabric LA Connector tests.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock, MagicMock

# Load environment variables from tests/.env
from dotenv import load_dotenv

# Load test environment variables
test_env_path = Path(__file__).parent / '.env'
load_dotenv(test_env_path)

# Import pytest after loading environment
try:
    import pytest
except ImportError:
    # For environments where pytest is not installed
    pytest = None

# Test configuration constants from environment
TEST_WORKSPACE_ID = os.getenv("FABRIC_WORKSPACE_ID", "fb53fbfb-d8e9-4797-b2f5-ba80bb9a7388")
TEST_ENVIRONMENT_ID = os.getenv("FABRIC_ENVIRONMENT_ID", "7dfeb1c0-bb2f-4ecd-81cf-2d876c90cfae")
TEST_CAPACITY_ID = os.getenv("FABRIC_CAPACITY_ID", "test-capacity-id")
TEST_PIPELINE_ID = os.getenv("TEST_PIPELINE_ID", "test-pipeline-id")
TEST_DATAFLOW_ID = os.getenv("TEST_DATAFLOW_ID", "test-dataflow-id")
TEST_DATASET_ID = os.getenv("TEST_DATASET_ID", "test-dataset-id")

# Azure Monitor configuration from environment
AZURE_MONITOR_DCE_ENDPOINT = os.getenv("AZURE_MONITOR_DCE_ENDPOINT", "https://test-dce.eastus-1.ingest.monitor.azure.com")
AZURE_MONITOR_DCR_IMMUTABLE_ID = os.getenv("AZURE_MONITOR_DCR_IMMUTABLE_ID", "dcr-test-immutable-id")
AZURE_MONITOR_STREAM_NAME = os.getenv("AZURE_MONITOR_STREAM_NAME", "Custom-FabricTest_CL")
LOG_ANALYTICS_TABLE = os.getenv("LOG_ANALYTICS_TABLE", "FabricTest_CL")

# Test settings
TEST_LOOKBACK_HOURS = int(os.getenv("TEST_LOOKBACK_HOURS", "24"))
TEST_BATCH_SIZE = int(os.getenv("TEST_BATCH_SIZE", "100"))
USE_MOCK_API = os.getenv("USE_MOCK_API", "true").lower() == "true"

# Mock API responses
MOCK_PIPELINE_RUN = {
    "id": "test-run-id",
    "status": "Succeeded",
    "startTimeUtc": "2024-01-15T10:00:00Z",
    "endTimeUtc": "2024-01-15T10:05:00Z",
    "invokeType": "Manual",
    "jobType": "Pipeline",
    "rootActivityRunId": "test-root-activity-id"
}

MOCK_ACTIVITY_RUN = {
    "activityName": "Copy Data",
    "activityType": "Copy",
    "status": "Succeeded",
    "startTimeUtc": "2024-01-15T10:01:00Z",
    "endTimeUtc": "2024-01-15T10:04:00Z",
    "durationInMs": 180000,
    "output": {
        "dataRead": 1024000,
        "dataWritten": 1024000,
        "recordsProcessed": 1000
    }
}

MOCK_DATAFLOW_RUN = {
    "id": "test-dataflow-run-id",
    "status": "Succeeded",
    "startTimeUtc": "2024-01-15T10:00:00Z",
    "endTimeUtc": "2024-01-15T10:10:00Z",
    "invokeType": "Scheduled",
    "jobType": "Dataflow"
}

MOCK_DATASET_REFRESH = {
    "id": "test-refresh-id",
    "refreshType": "Full",
    "status": "Completed",
    "startTime": "2024-01-15T10:00:00Z",
    "endTime": "2024-01-15T10:03:00Z",
    "servicePrincipalId": "test-sp-id",
    "requestId": "test-request-id"
}

MOCK_CAPACITY_METRICS = {
    "value": [
        {
            "workloadType": "PowerBI",
            "cpuPercentage": 45.5,
            "memoryPercentage": 60.2,
            "activeRequests": 12,
            "queuedRequests": 3,
            "timeGenerated": "2024-01-15T10:00:00Z"
        }
    ]
}

MOCK_USER_ACTIVITY = {
    "value": [
        {
            "id": "test-activity-id",
            "userId": "test-user-id",
            "userEmail": "test@contoso.com",
            "activityType": "DatasetRefresh",
            "creationTime": "2024-01-15T10:00:00Z",
            "itemName": "Test Dataset",
            "workspaceName": "Test Workspace",
            "itemType": "Dataset",
            "objectId": "test-object-id"
        }
    ]
}

@pytest.fixture
def mock_config():
    """Mock configuration for tests."""
    return {
        "FABRIC_WORKSPACE_ID": TEST_WORKSPACE_ID,
        "AZURE_MONITOR_DCE_ENDPOINT": "https://test-dce.monitor.azure.com",
        "AZURE_MONITOR_DCR_IMMUTABLE_ID": "dcr-test-immutable-id",
        "AZURE_MONITOR_STREAM_NAME": "Custom-FabricTest_CL",
        "LOG_ANALYTICS_TABLE": "FabricTest_CL"
    }

@pytest.fixture
def mock_fabric_token():
    """Mock Fabric authentication token."""
    return "test-fabric-token"

@pytest.fixture
def mock_api_client(mock_fabric_token):
    """Mock Fabric API client."""
    client = Mock()
    client.token = mock_fabric_token
    client.headers = {
        'Authorization': f'Bearer {mock_fabric_token}',
        'Content-Type': 'application/json'
    }
    return client

@pytest.fixture
def mock_requests_response():
    """Mock requests response."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"value": []}
    return response

@pytest.fixture
def test_time_window():
    """Test time window for lookback operations."""
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    return {
        "start_time": start_time,
        "end_time": end_time,
        "lookback_hours": 24
    }

class MockIngestionClient:
    """Mock Azure Monitor Ingestion client for testing."""
    
    def __init__(self):
        self.uploaded_data = []
        self.upload_call_count = 0
        
    def upload(self, rule_id: str, stream_name: str, logs: list, **kwargs):
        """Mock upload method."""
        self.upload_call_count += 1
        self.uploaded_data.extend(logs)
        return Mock(status=204)
    
    def get_uploaded_data(self):
        """Get all uploaded data for verification."""
        return self.uploaded_data
    
    def reset(self):
        """Reset mock state."""
        self.uploaded_data = []
        self.upload_call_count = 0

@pytest.fixture
def mock_ingestion_client():
    """Mock ingestion client fixture."""
    return MockIngestionClient()