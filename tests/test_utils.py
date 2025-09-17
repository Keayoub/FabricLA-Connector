"""
Test utilities and base classes for FabricLA Connector Framework

Provides shared utilities and base test classes without external dependencies.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock

# Load environment variables from tests/.env
from dotenv import load_dotenv

# Load test environment variables
test_env_path = Path(__file__).parent / '.env'
if test_env_path.exists():
    load_dotenv(test_env_path)

# Test configuration from environment
class TestConfig:
    """Test configuration loaded from environment variables."""
    
    # Fabric configuration
    WORKSPACE_ID = os.getenv("FABRIC_WORKSPACE_ID", "fb53fbfb-d8e9-4797-b2f5-ba80bb9a7388")
    ENVIRONMENT_ID = os.getenv("FABRIC_ENVIRONMENT_ID", "7dfeb1c0-bb2f-4ecd-81cf-2d876c90cfae")
    CAPACITY_ID = os.getenv("FABRIC_CAPACITY_ID", "test-capacity-id")
    
    # Test item IDs
    PIPELINE_ID = os.getenv("TEST_PIPELINE_ID", "test-pipeline-id")
    DATAFLOW_ID = os.getenv("TEST_DATAFLOW_ID", "test-dataflow-id")
    DATASET_ID = os.getenv("TEST_DATASET_ID", "test-dataset-id")
    NOTEBOOK_ID = os.getenv("TEST_NOTEBOOK_ID", "test-notebook-id")
    SPARK_JOB_ID = os.getenv("TEST_SPARK_JOB_ID", "test-spark-job-id")
    
    # Azure Monitor configuration (using actual .env variable names)
    DCE_HOST = os.getenv("DCR_ENDPOINT_HOST", "test-dce.eastus-1.ingest.monitor.azure.com")
    # Construct full DCE endpoint URL if not already a full URL
    if DCE_HOST and not DCE_HOST.startswith("https://"):
        DCE_ENDPOINT = f"https://{DCE_HOST}"
    else:
        DCE_ENDPOINT = DCE_HOST or "https://test-dce.eastus-1.ingest.monitor.azure.com"
    
    DCR_IMMUTABLE_ID = os.getenv("DCR_IMMUTABLE_ID", "dcr-test-immutable-id")
    STREAM_NAME = os.getenv("AZURE_MONITOR_STREAM_NAME", "Custom-FabricTest_CL")
    TABLE_NAME = os.getenv("LOG_ANALYTICS_TABLE", "FabricTest_CL")
    
    # Legacy/Alternative variable names (for compatibility)
    if not DCE_ENDPOINT or DCE_ENDPOINT == "https://test-dce.eastus-1.ingest.monitor.azure.com":
        DCE_ENDPOINT = os.getenv("AZURE_MONITOR_DCE_ENDPOINT", DCE_ENDPOINT)
    if not DCR_IMMUTABLE_ID or DCR_IMMUTABLE_ID == "dcr-test-immutable-id":
        DCR_IMMUTABLE_ID = os.getenv("AZURE_MONITOR_DCR_IMMUTABLE_ID", DCR_IMMUTABLE_ID)
    
    # Test settings
    LOOKBACK_HOURS = int(os.getenv("TEST_LOOKBACK_HOURS", "24"))
    BATCH_SIZE = int(os.getenv("TEST_BATCH_SIZE", "100"))
    USE_MOCK_API = os.getenv("USE_MOCK_API", "true").lower() == "true"
    MOCK_DELAY = float(os.getenv("MOCK_DELAY_SECONDS", "0.1"))
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get configuration as dictionary with both old and new variable names."""
        return {
            "FABRIC_WORKSPACE_ID": cls.WORKSPACE_ID,
            # Primary variable names (from .env file)
            "DCR_ENDPOINT_HOST": cls.DCE_HOST,
            "DCR_IMMUTABLE_ID": cls.DCR_IMMUTABLE_ID,
            # Legacy variable names (for compatibility)
            "AZURE_MONITOR_DCE_ENDPOINT": cls.DCE_ENDPOINT,
            "AZURE_MONITOR_DCR_IMMUTABLE_ID": cls.DCR_IMMUTABLE_ID,
            "AZURE_MONITOR_STREAM_NAME": cls.STREAM_NAME,
            "LOG_ANALYTICS_TABLE": cls.TABLE_NAME
        }

# Mock data for tests
class MockData:
    """Mock data responses for testing."""
    
    PIPELINE_RUN = {
        "id": "test-run-id",
        "status": "Succeeded",
        "startTimeUtc": "2024-01-15T10:00:00Z",
        "endTimeUtc": "2024-01-15T10:05:00Z",
        "invokeType": "Manual",
        "jobType": "Pipeline",
        "rootActivityRunId": "test-root-activity-id"
    }
    
    ACTIVITY_RUN = {
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
    
    DATAFLOW_RUN = {
        "id": "test-dataflow-run-id",
        "status": "Succeeded",
        "startTimeUtc": "2024-01-15T10:00:00Z",
        "endTimeUtc": "2024-01-15T10:10:00Z",
        "invokeType": "Scheduled",
        "jobType": "Dataflow"
    }
    
    DATASET_REFRESH = {
        "id": "test-refresh-id",
        "refreshType": "Full",
        "status": "Completed",
        "startTime": "2024-01-15T10:00:00Z",
        "endTime": "2024-01-15T10:03:00Z",
        "servicePrincipalId": "test-sp-id",
        "requestId": "test-request-id"
    }
    
    CAPACITY_METRICS = {
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
    
    USER_ACTIVITY = {
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

class MockIngestionClient:
    """Mock Azure Monitor Ingestion client for testing."""
    
    def __init__(self):
        self.uploaded_data = []
        self.upload_call_count = 0
        self.errors = []
        
    def upload(self, rule_id: str, stream_name: str, logs: list, **kwargs):
        """Mock upload method."""
        self.upload_call_count += 1
        self.uploaded_data.extend(logs)
        
        # Simulate upload response
        response = Mock()
        response.status = 204
        return response
    
    def upload_with_error(self, rule_id: str, stream_name: str, logs: list, **kwargs):
        """Mock upload method that simulates an error."""
        error = Exception("Simulated upload error")
        self.errors.append(error)
        raise error
    
    def get_uploaded_data(self) -> List[Dict]:
        """Get all uploaded data for verification."""
        return self.uploaded_data
    
    def reset(self):
        """Reset mock state."""
        self.uploaded_data = []
        self.upload_call_count = 0
        self.errors = []

class TestHelpers:
    """Helper methods for testing."""
    
    @staticmethod
    def create_time_window(hours_ago: int = 24) -> Dict[str, datetime]:
        """Create time window for testing."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_ago)
        return {
            "start_time": start_time,
            "end_time": end_time
        }
    
    @staticmethod
    def mock_api_response(data: Any, status_code: int = 200) -> Mock:
        """Create mock API response."""
        response = Mock()
        response.status_code = status_code
        response.json.return_value = data
        return response
    
    @staticmethod
    def mock_fabric_token() -> str:
        """Get mock Fabric token."""
        return "test-fabric-token-12345"
    
    @staticmethod
    def setup_sys_path():
        """Setup system path for imports."""
        project_root = Path(__file__).parent.parent
        src_path = project_root / 'src'
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))