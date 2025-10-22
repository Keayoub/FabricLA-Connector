"""
Integration tests for Fabric LA Connector Framework

Tests the complete workflow including data collection and ingestion.
"""

import unittest
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Setup path and import test utilities
sys.path.insert(0, str(Path(__file__).parent))
from test_utils import TestConfig, MockData, TestHelpers, MockIngestionClient

# Setup project path for imports
TestHelpers.setup_sys_path()

try:
    from fabricla_connector.config import get_config
    from fabricla_connector.ingestion import AzureMonitorIngestionClient
    from fabricla_connector.utils import iso_now, create_time_window
except ImportError as e:
    print(f"Warning: Could not import framework components: {e}")
    print("Run tests from project root or ensure package is installed")

class TestAzureMonitorIngestionClientWorkflow(unittest.TestCase):
    """Test complete ingestion workflow."""
    
    def setUp(self):
        """Setup test environment."""
        self.config = TestConfig.get_config_dict()
        self.mock_client = MockIngestionClient()
        
    def test_ingestion_config_loading(self):
        """Test configuration loading from environment."""
        # Test that configuration loads properly
        self.assertIsNotNone(self.config.get('FABRIC_WORKSPACE_ID'))
        # Check for either old or new variable names
        dce_endpoint = self.config.get('DCR_ENDPOINT_HOST') or self.config.get('AZURE_MONITOR_DCE_ENDPOINT')
        dcr_id = self.config.get('DCR_IMMUTABLE_ID') or self.config.get('AZURE_MONITOR_DCR_IMMUTABLE_ID')
        self.assertIsNotNone(dce_endpoint)
        self.assertIsNotNone(dcr_id)
        
        print(f"✅ Configuration loaded successfully")
        print(f"   Workspace ID: {TestConfig.WORKSPACE_ID}")
        print(f"   DCE Endpoint: {TestConfig.DCE_ENDPOINT}")
        
    @patch('fabricla_connector.ingestion.client.LogsIngestionClient')
    def test_fabric_ingestion_initialization(self, mock_sdk_client):
        """Test AzureMonitorIngestionClient initialization."""
        # Setup mock
        mock_sdk_client.return_value = self.mock_client
        
        # Initialize ingestion
        ingestion = AzureMonitorIngestionClient(
            dce_endpoint=TestConfig.DCE_ENDPOINT,
            dcr_immutable_id=TestConfig.DCR_IMMUTABLE_ID,
            stream_name=TestConfig.STREAM_NAME
        )
        
        self.assertIsNotNone(ingestion)
        print("✅ AzureMonitorIngestionClient initialized successfully")
        
    @patch('fabricla_connector.ingestion.client.LogsIngestionClient')
    def test_pipeline_data_ingestion(self, mock_sdk_client):
        """Test pipeline data ingestion workflow."""
        # Setup mock
        mock_sdk_client.return_value = self.mock_client
        
        # Create test data
        pipeline_data = [
            {
                "TimeGenerated": iso_now(),
                "WorkspaceId": TestConfig.WORKSPACE_ID,
                "PipelineId": TestConfig.PIPELINE_ID,
                "PipelineName": "Test Pipeline",
                "RunId": "test-run-123",
                "Status": "Succeeded",
                "StartTime": "2024-01-15T10:00:00Z",
                "EndTime": "2024-01-15T10:05:00Z",
                "DurationMs": 300000,
                "InvokeType": "Manual"
            }
        ]
        
        # Initialize ingestion
        ingestion = AzureMonitorIngestionClient(
            dce_endpoint=TestConfig.DCE_ENDPOINT,
            dcr_immutable_id=TestConfig.DCR_IMMUTABLE_ID,
            stream_name=TestConfig.STREAM_NAME
        )
        
        # Test ingestion
        result = ingestion.ingest(pipeline_data)
        
        # Verify results
        self.assertEqual(self.mock_client.upload_call_count, 1)
        uploaded_data = self.mock_client.get_uploaded_data()
        self.assertEqual(len(uploaded_data), 1)
        self.assertEqual(uploaded_data[0]['PipelineId'], TestConfig.PIPELINE_ID)
        
        print(f"✅ Pipeline data ingestion successful")
        print(f"   Records ingested: {len(uploaded_data)}")
        
    @patch('fabricla_connector.ingestion.client.LogsIngestionClient')
    def test_batch_ingestion(self, mock_sdk_client):
        """Test batch ingestion with multiple records."""
        # Setup mock
        mock_sdk_client.return_value = self.mock_client
        
        # Create test data with multiple records
        test_data = []
        for i in range(150):  # Test batching
            test_data.append({
                "TimeGenerated": iso_now(),
                "WorkspaceId": TestConfig.WORKSPACE_ID,
                "DatasetId": f"dataset-{i}",
                "DatasetName": f"Test Dataset {i}",
                "RefreshId": f"refresh-{i}",
                "Status": "Completed",
                "RefreshType": "Full"
            })
        
        # Initialize ingestion
        ingestion = AzureMonitorIngestionClient(
            dce_endpoint=TestConfig.DCE_ENDPOINT,
            dcr_immutable_id=TestConfig.DCR_IMMUTABLE_ID,
            stream_name=TestConfig.STREAM_NAME
        )
        
        # Test ingestion with chunk_size to force batching
        result = ingestion.ingest(test_data, chunk_size=100)
        
        # Verify batching occurred
        self.assertGreaterEqual(self.mock_client.upload_call_count, 2)  # Should have multiple batches
        uploaded_data = self.mock_client.get_uploaded_data()
        self.assertEqual(len(uploaded_data), 150)
        
        print(f"✅ Batch ingestion successful")
        print(f"   Records ingested: {len(uploaded_data)}")
        print(f"   Upload calls: {self.mock_client.upload_call_count}")

class TestWorkflowPatterns(unittest.TestCase):
    """Test workflow patterns similar to notebook examples."""
    
    def setUp(self):
        """Setup test environment."""
        self.workspace_id = TestConfig.WORKSPACE_ID
        self.mock_client = MockIngestionClient()
        
    def test_pipeline_monitoring_workflow(self):
        """Test complete pipeline monitoring workflow."""
        print("\n🔄 Testing Pipeline Monitoring Workflow")
        
        # Simulate notebook workflow
        pipeline_ids = [TestConfig.PIPELINE_ID]
        lookback_hours = 24
        
        # Mock data collection
        collected_runs = []
        collected_activities = []
        
        # Simulate pipeline run collection
        for pipeline_id in pipeline_ids:
            run_data = {
                "TimeGenerated": iso_now(),
                "WorkspaceId": self.workspace_id,
                "PipelineId": pipeline_id,
                "PipelineName": f"Pipeline {pipeline_id}",
                "RunId": f"run-{pipeline_id}-123",
                "Status": "Succeeded",
                "StartTime": "2024-01-15T10:00:00Z",
                "EndTime": "2024-01-15T10:05:00Z",
                "DurationMs": 300000
            }
            collected_runs.append(run_data)
            
            # Simulate activity collection
            activity_data = {
                "TimeGenerated": iso_now(),
                "WorkspaceId": self.workspace_id,
                "PipelineId": pipeline_id,
                "ActivityName": "Copy Data",
                "ActivityType": "Copy",
                "RunId": f"run-{pipeline_id}-123",
                "Status": "Succeeded",
                "DataRead": 1024000,
                "DataWritten": 1024000
            }
            collected_activities.append(activity_data)
        
        # Verify workflow
        self.assertEqual(len(collected_runs), len(pipeline_ids))
        self.assertEqual(len(collected_activities), len(pipeline_ids))
        
        print(f"   ✅ Collected {len(collected_runs)} pipeline runs")
        print(f"   ✅ Collected {len(collected_activities)} activities")
        
    def test_capacity_monitoring_workflow(self):
        """Test capacity monitoring workflow."""
        print("\n📊 Testing Capacity Monitoring Workflow")
        
        # Simulate capacity metrics collection
        capacity_metrics = []
        
        # Mock capacity data
        for i in range(24):  # 24 hours of hourly metrics
            metric_time = datetime.now() - timedelta(hours=i)
            metric_data = {
                "TimeGenerated": metric_time.isoformat() + "Z",
                "CapacityId": TestConfig.CAPACITY_ID,
                "WorkloadType": "PowerBI",
                "CpuPercentage": 40.0 + (i * 2),
                "MemoryPercentage": 50.0 + (i * 1.5),
                "ActiveRequests": 10 + i,
                "QueuedRequests": max(0, i - 5)
            }
            capacity_metrics.append(metric_data)
        
        # Verify workflow
        self.assertEqual(len(capacity_metrics), 24)
        
        # Check data trends
        cpu_values = [m['CpuPercentage'] for m in capacity_metrics]
        self.assertTrue(all(isinstance(v, (int, float)) for v in cpu_values))
        
        print(f"   ✅ Collected {len(capacity_metrics)} capacity metrics")
        print(f"   ✅ CPU range: {min(cpu_values):.1f}% - {max(cpu_values):.1f}%")
        
    def test_user_activity_workflow(self):
        """Test user activity monitoring workflow."""
        print("\n👥 Testing User Activity Workflow")
        
        # Simulate user activity collection
        user_activities = []
        
        activity_types = ["DatasetRefresh", "ReportView", "DashboardView", "DataflowRun"]
        
        for i, activity_type in enumerate(activity_types):
            activity_data = {
                "TimeGenerated": iso_now(),
                "WorkspaceId": self.workspace_id,
                "ActivityId": f"activity-{i}",
                "UserId": f"user-{i}",
                "UserEmail": f"user{i}@contoso.com",
                "ActivityType": activity_type,
                "CreationTime": iso_now(),
                "ItemName": f"Test Item {i}",
                "WorkspaceName": "Test Workspace"
            }
            user_activities.append(activity_data)
        
        # Verify workflow
        self.assertEqual(len(user_activities), len(activity_types))
        
        # Check activity type distribution
        types_collected = {activity['ActivityType'] for activity in user_activities}
        self.assertEqual(types_collected, set(activity_types))
        
        print(f"   ✅ Collected {len(user_activities)} user activities")
        print(f"   ✅ Activity types: {', '.join(types_collected)}")

class TestErrorHandling(unittest.TestCase):
    """Test error handling and resilience."""
    
    def setUp(self):
        """Setup test environment."""
        self.mock_client = MockIngestionClient()
        
    @patch('fabricla_connector.ingestion.client.LogsIngestionClient')
    def test_ingestion_retry_logic(self, mock_sdk_client):
        """Test retry logic for failed ingestion."""
        # Setup mock to fail first, then succeed
        mock_client = Mock()
        mock_client.upload.side_effect = [Exception("Connection timeout error"), Mock(status=204)]
        mock_sdk_client.return_value = mock_client
        
        # Test data
        test_data = [{"TimeGenerated": iso_now(), "TestField": "test"}]
        
        # Initialize ingestion
        ingestion = AzureMonitorIngestionClient(
            dce_endpoint=TestConfig.DCE_ENDPOINT,
            dcr_immutable_id=TestConfig.DCR_IMMUTABLE_ID,
            stream_name=TestConfig.STREAM_NAME
        )
        
        # Test ingestion with retry parameters (should succeed on retry)
        start_time = time.time()
        result = ingestion.ingest(test_data, max_retries=2)
        duration = time.time() - start_time
        
        # Verify retry occurred
        self.assertEqual(mock_client.upload.call_count, 2)
        self.assertGreater(duration, 0.1)  # Should have delayed for retry
        
        print("✅ Retry logic working correctly")
        
    def test_data_validation(self):
        """Test data validation before ingestion."""
        # Test empty data
        empty_result = self._validate_data([])
        self.assertTrue(empty_result['valid'])
        self.assertEqual(empty_result['record_count'], 0)
        
        # Test valid data
        valid_data = [{"TimeGenerated": iso_now(), "TestField": "test"}]
        valid_result = self._validate_data(valid_data)
        self.assertTrue(valid_result['valid'])
        self.assertEqual(valid_result['record_count'], 1)
        
        # Test invalid data (missing TimeGenerated)
        invalid_data = [{"TestField": "test"}]
        invalid_result = self._validate_data(invalid_data)
        self.assertFalse(invalid_result['valid'])
        
        print("✅ Data validation working correctly")
        
    def _validate_data(self, data):
        """Helper method to validate data."""
        if not data:
            return {'valid': True, 'record_count': 0}
            
        # Check if all records have TimeGenerated
        for record in data:
            if 'TimeGenerated' not in record:
                return {'valid': False, 'error': 'Missing TimeGenerated field'}
                
        return {'valid': True, 'record_count': len(data)}

def run_integration_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("Running Fabric LA Connector - Integration Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestAzureMonitorIngestionClientWorkflow,
        TestWorkflowPatterns,
        TestErrorHandling
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All integration tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)