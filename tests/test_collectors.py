"""
Unit tests for Fabric Data Collectors

Tests the individual collector classes without external dependencies.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# Setup path and import test utilities
sys.path.insert(0, str(Path(__file__).parent))
from test_utils import TestConfig, MockData, TestHelpers

# Setup project path for imports - ensure we're in the right directory
project_root = Path(__file__).parent.parent
os.chdir(str(project_root))
TestHelpers.setup_sys_path()

# Import framework components with graceful error handling
FRAMEWORK_AVAILABLE = True
framework_import_error = None

try:
    from fabricla_connector.collectors import (
        PipelineDataCollector,
        DatasetRefreshCollector,
        CapacityUtilizationCollector,
        UserActivityCollector,
        OneLakeStorageCollector,
        SparkJobCollector,
        NotebookCollector
    )
    from fabricla_connector.utils import parse_iso, iso_now
    
    from fabricla_connector.mappers import (
        PipelineRunMapper,
        ActivityRunMapper,
        DatasetRefreshMapper,
        CapacityMetricMapper,
        UserActivityMapper
    )
except ImportError as e:
    FRAMEWORK_AVAILABLE = False
    framework_import_error = str(e)
    print(f"Warning: Could not import framework components: {e}")
    print("Run tests from project root or ensure package is installed")
    
    # Create mock classes for testing structure
    class MockCollector:
        def __init__(self, *args, **kwargs):
            pass
        def collect_data(self, *args, **kwargs):
            return []
    
    class MockMapper:
        @staticmethod
        def map(*args, **kwargs):
            return {}
    
    def parse_iso(date_str):
        return datetime.now()
    
    def iso_now():
        return datetime.now().isoformat()
    
    # Assign mock classes
    PipelineDataCollector = MockCollector
    DatasetRefreshCollector = MockCollector
    CapacityUtilizationCollector = MockCollector
    UserActivityCollector = MockCollector
    OneLakeStorageCollector = MockCollector
    SparkJobCollector = MockCollector
    NotebookCollector = MockCollector
    
    PipelineRunMapper = MockMapper
    ActivityRunMapper = MockMapper
    DatasetRefreshMapper = MockMapper
    CapacityMetricMapper = MockMapper
    UserActivityMapper = MockMapper

class TestPipelineDataCollector(unittest.TestCase):
    """Test PipelineDataCollector class."""
    
    def setUp(self):
        """Setup test environment."""
        self.workspace_id = TestConfig.WORKSPACE_ID
        self.pipeline_id = TestConfig.PIPELINE_ID
        self.mock_token = TestHelpers.mock_fabric_token()
        
    @unittest.skipIf(not FRAMEWORK_AVAILABLE, f"Framework not available: {framework_import_error}")
    @patch('fabricla_connector.collectors.get_fabric_token')
    @patch('fabricla_connector.collectors.requests.get')
    def test_collect_pipeline_runs_success(self, mock_get, mock_token):
        """Test successful pipeline run collection."""
        # Setup mocks
        mock_token.return_value = self.mock_token
        mock_response = TestHelpers.mock_api_response({
            "value": [MockData.PIPELINE_RUN]
        })
        mock_get.return_value = mock_response
        
        # Create collector and collect data
        collector = PipelineDataCollector(
            workspace_id=self.workspace_id,
            lookback_hours=24,
            token=self.mock_token
        )
        
        # Test collection
        runs = list(collector.collect_pipeline_runs([self.pipeline_id]))
        
        # Verify results
        self.assertEqual(len(runs), 1)
        run = runs[0]
        self.assertEqual(run['WorkspaceId'], self.workspace_id)
        self.assertEqual(run['PipelineId'], self.pipeline_id)
        self.assertEqual(run['Status'], 'Succeeded')
        self.assertIn('TimeGenerated', run)
        
    @unittest.skipIf(not FRAMEWORK_AVAILABLE, f"Framework not available: {framework_import_error}")
    @patch('fabricla_connector.collectors.get_fabric_token')
    @patch('fabricla_connector.collectors.requests.get')
    def test_collect_activity_runs_success(self, mock_get, mock_token):
        """Test successful activity run collection."""
        # Setup mocks
        mock_token.return_value = self.mock_token
        mock_response = TestHelpers.mock_api_response({
            "value": [MockData.ACTIVITY_RUN]
        })
        mock_get.return_value = mock_response
        
        # Create collector and collect data
        collector = PipelineDataCollector(
            workspace_id=self.workspace_id,
            lookback_hours=24,
            token=self.mock_token
        )
        
        # Test collection
        activities = list(collector.collect_activity_runs([{
            'pipeline_id': self.pipeline_id,
            'run_id': 'test-run-id'
        }]))
        
        # Verify results
        self.assertEqual(len(activities), 1)
        activity = activities[0]
        self.assertEqual(activity['WorkspaceId'], self.workspace_id)
        self.assertEqual(activity['ActivityName'], 'Copy Data')
        self.assertEqual(activity['ActivityType'], 'Copy')
        self.assertEqual(activity['Status'], 'Succeeded')

class TestDatasetRefreshCollector(unittest.TestCase):
    """Test DatasetRefreshCollector class."""
    
    def setUp(self):
        """Setup test environment."""
        self.workspace_id = TestConfig.WORKSPACE_ID
        self.dataset_id = TestConfig.DATASET_ID
        self.mock_token = TestHelpers.mock_fabric_token()
        
    @unittest.skipIf(not FRAMEWORK_AVAILABLE, f"Framework not available: {framework_import_error}")
    @patch('fabricla_connector.collectors.get_fabric_token')
    @patch('fabricla_connector.collectors.list_workspace_datasets')
    @patch('fabricla_connector.collectors.get_dataset_refresh_history')
    def test_collect_dataset_refreshes(self, mock_refreshes, mock_datasets, mock_token):
        """Test dataset refresh collection."""
        # Setup mocks
        mock_token.return_value = self.mock_token
        mock_datasets.return_value = [{
            'id': self.dataset_id,
            'displayName': 'Test Dataset'
        }]
        mock_refreshes.return_value = [MockData.DATASET_REFRESH]
        
        # Create collector and collect data
        collector = DatasetRefreshCollector(
            workspace_id=self.workspace_id,
            lookback_hours=24,
            token=self.mock_token
        )
        
        # Test collection
        refreshes = list(collector.collect_dataset_refreshes())
        
        # Verify results
        self.assertEqual(len(refreshes), 1)
        refresh = refreshes[0]
        self.assertEqual(refresh['WorkspaceId'], self.workspace_id)
        self.assertEqual(refresh['DatasetId'], self.dataset_id)
        self.assertEqual(refresh['Status'], 'Completed')
        self.assertEqual(refresh['RefreshType'], 'Full')

class TestCapacityUtilizationCollector(unittest.TestCase):
    """Test CapacityUtilizationCollector class."""
    
    def setUp(self):
        """Setup test environment."""
        self.capacity_id = TestConfig.CAPACITY_ID
        self.mock_token = TestHelpers.mock_fabric_token()
        
    @unittest.skipIf(not FRAMEWORK_AVAILABLE, f"Framework not available: {framework_import_error}")
    @patch('fabricla_connector.collectors.get_fabric_token')
    @patch('fabricla_connector.collectors.get_capacity_utilization')
    def test_collect_capacity_metrics(self, mock_utilization, mock_token):
        """Test capacity metrics collection."""
        # Setup mocks
        mock_token.return_value = self.mock_token
        mock_utilization.return_value = MockData.CAPACITY_METRICS['value']
        
        # Create collector and collect data
        collector = CapacityUtilizationCollector(
            capacity_id=self.capacity_id,
            lookback_hours=24,
            token=self.mock_token
        )
        
        # Test collection
        metrics = list(collector.collect_capacity_metrics())
        
        # Verify results
        self.assertEqual(len(metrics), 1)
        metric = metrics[0]
        self.assertEqual(metric['WorkloadType'], 'PowerBI')
        self.assertEqual(metric['CpuPercentage'], 45.5)
        self.assertEqual(metric['MemoryPercentage'], 60.2)

class TestUserActivityCollector(unittest.TestCase):
    """Test UserActivityCollector class."""
    
    def setUp(self):
        """Setup test environment."""
        self.workspace_id = TestConfig.WORKSPACE_ID
        self.mock_token = TestHelpers.mock_fabric_token()
        
    @unittest.skipIf(not FRAMEWORK_AVAILABLE, f"Framework not available: {framework_import_error}")
    @patch('fabricla_connector.collectors.get_fabric_token')
    @patch('fabricla_connector.collectors.get_user_activity')
    def test_collect_user_activities(self, mock_activity, mock_token):
        """Test user activity collection."""
        # Setup mocks
        mock_token.return_value = self.mock_token
        mock_activity.return_value = MockData.USER_ACTIVITY['value']
        
        # Create collector and collect data
        collector = UserActivityCollector(
            workspace_id=self.workspace_id,
            lookback_hours=24,
            token=self.mock_token
        )
        
        # Test collection
        activities = list(collector.collect_user_activities())
        
        # Verify results
        self.assertEqual(len(activities), 1)
        activity = activities[0]
        self.assertEqual(activity['WorkspaceId'], self.workspace_id)
        self.assertEqual(activity['UserId'], 'test-user-id')
        self.assertEqual(activity['ActivityType'], 'DatasetRefresh')

class TestDataMappers(unittest.TestCase):
    """Test data mapping functions."""
    
    def setUp(self):
        """Setup test environment."""
        self.workspace_id = TestConfig.WORKSPACE_ID
        
    def test_map_pipeline_run(self):
        """Test pipeline run mapping."""
        from fabricla_connector.collectors import map_pipeline_run
        
        mapped = map_pipeline_run(
            workspace_id=self.workspace_id,
            pipeline_id='test-pipeline',
            pipeline_name='Test Pipeline',
            run=MockData.PIPELINE_RUN
        )
        
        # Verify mapping
        self.assertEqual(mapped['WorkspaceId'], self.workspace_id)
        self.assertEqual(mapped['PipelineId'], 'test-pipeline')
        self.assertEqual(mapped['PipelineName'], 'Test Pipeline')
        self.assertEqual(mapped['Status'], 'Succeeded')
        self.assertEqual(mapped['InvokeType'], 'Manual')
        
    def test_map_activity_run(self):
        """Test activity run mapping."""
        from fabricla_connector.collectors import map_activity_run
        
        mapped = map_activity_run(
            workspace_id=self.workspace_id,
            pipeline_id='test-pipeline',
            pipeline_run_id='test-run',
            activity=MockData.ACTIVITY_RUN
        )
        
        # Verify mapping
        self.assertEqual(mapped['WorkspaceId'], self.workspace_id)
        self.assertEqual(mapped['ActivityName'], 'Copy Data')
        self.assertEqual(mapped['ActivityType'], 'Copy')
        self.assertEqual(mapped['DataRead'], 1024000)
        self.assertEqual(mapped['DataWritten'], 1024000)
        
    def test_map_dataset_refresh(self):
        """Test dataset refresh mapping."""
        from fabricla_connector.collectors import map_dataset_refresh
        
        mapped = map_dataset_refresh(
            workspace_id=self.workspace_id,
            dataset_id='test-dataset',
            dataset_name='Test Dataset',
            refresh=MockData.DATASET_REFRESH
        )
        
        # Verify mapping
        self.assertEqual(mapped['WorkspaceId'], self.workspace_id)
        self.assertEqual(mapped['DatasetId'], 'test-dataset')
        self.assertEqual(mapped['RefreshType'], 'Full')
        self.assertEqual(mapped['Status'], 'Completed')

def run_collector_tests():
    """Run all collector tests."""
    print("=" * 60)
    print("Running Fabric LA Connector - Collector Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestPipelineDataCollector,
        TestDatasetRefreshCollector,
        TestCapacityUtilizationCollector,
        TestUserActivityCollector,
        TestDataMappers
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
        print("✅ All collector tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_collector_tests()
    sys.exit(0 if success else 1)