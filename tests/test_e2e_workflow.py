"""
End-to-End Workflow Test

This test mimics the notebook workflow patterns for complete integration testing.
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Setup path and import test utilities
sys.path.insert(0, str(Path(__file__).parent))
from test_utils import TestConfig, MockData, TestHelpers, MockIngestionClient

class NotebookWorkflowTest:
    """Test that mimics the notebook workflow patterns."""
    
    def __init__(self):
        self.config = TestConfig.get_config_dict()
        self.workspace_id = TestConfig.WORKSPACE_ID
        self.results = {}
        
    def run_complete_workflow_test(self) -> bool:
        """Run complete workflow test similar to notebooks."""
        print("🚀 Starting End-to-End Workflow Test")
        print("=" * 60)
        
        try:
            # Step 1: Environment Setup (like notebook cell 1)
            self._test_environment_setup()
            
            # Step 2: Configuration Loading (like notebook cell 2)
            self._test_configuration_loading()
            
            # Step 3: Pipeline Monitoring (like notebook cell 3)
            self._test_pipeline_monitoring_workflow()
            
            # Step 4: Dataset Monitoring (like notebook cell 4)
            self._test_dataset_monitoring_workflow()
            
            # Step 5: Capacity Monitoring (like notebook cell 5)
            self._test_capacity_monitoring_workflow()
            
            # Step 6: User Activity Monitoring (like notebook cell 6)
            self._test_user_activity_workflow()
            
            # Step 7: Data Ingestion (like notebook cell 7)
            self._test_data_ingestion_workflow()
            
            # Step 8: Verification and Reporting (like notebook cell 8)
            self._test_verification_and_reporting()
            
            print("\n✅ All workflow steps completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Workflow test failed: {str(e)}")
            return False
    
    def _test_environment_setup(self):
        """Test environment setup (mimics notebook imports and path setup)."""
        print("\n📦 Step 1: Environment Setup")
        
        # Test imports (simulate notebook imports)
        TestHelpers.setup_sys_path()
        
        # Test configuration availability (check both old and new variable names)
        required_vars = [
            'FABRIC_WORKSPACE_ID',
            ('DCR_ENDPOINT_HOST', 'AZURE_MONITOR_DCE_ENDPOINT'),
            ('DCR_IMMUTABLE_ID', 'AZURE_MONITOR_DCR_IMMUTABLE_ID')
        ]
        
        missing_vars = []
        for var in required_vars:
            if isinstance(var, tuple):
                # Check if either variable name exists
                if not any(os.getenv(v) for v in var):
                    missing_vars.append(f"{var[0]} or {var[1]}")
            else:
                if not os.getenv(var):
                    missing_vars.append(var)
        
        if missing_vars:
            raise Exception(f"Missing environment variables: {', '.join(missing_vars)}")
        
        print(f"   ✅ Environment variables loaded")
        print(f"   ✅ Python path configured")
        print(f"   ✅ Workspace ID: {self.workspace_id}")
        
    def _test_configuration_loading(self):
        """Test configuration loading (mimics notebook configuration cell)."""
        print("\n⚙️ Step 2: Configuration Loading")
        
        # Load configuration like in notebooks
        self.config = TestConfig.get_config_dict()
        
        # Verify critical configuration (check both old and new variable names)
        assert self.config['FABRIC_WORKSPACE_ID'], "Workspace ID not configured"
        dce_endpoint = self.config.get('DCR_ENDPOINT_HOST') or self.config.get('AZURE_MONITOR_DCE_ENDPOINT')
        dcr_id = self.config.get('DCR_IMMUTABLE_ID') or self.config.get('AZURE_MONITOR_DCR_IMMUTABLE_ID')
        assert dce_endpoint, "DCE endpoint not configured"
        assert dcr_id, "DCR ID not configured"
        
        # Set monitoring parameters (like in notebooks)
        self.lookback_hours = TestConfig.LOOKBACK_HOURS
        self.batch_size = TestConfig.BATCH_SIZE
        
        print(f"   ✅ Configuration loaded successfully")
        print(f"   ✅ Lookback hours: {self.lookback_hours}")
        print(f"   ✅ Batch size: {self.batch_size}")
        
        self.results['config'] = self.config
        
    def _test_pipeline_monitoring_workflow(self):
        """Test pipeline monitoring workflow (mimics notebook pipeline cells)."""
        print("\n🏭 Step 3: Pipeline Monitoring Workflow")
        
        # Simulate pipeline data collection (like in notebooks)
        pipeline_ids = [TestConfig.PIPELINE_ID]
        collected_runs = []
        collected_activities = []
        
        print(f"   📋 Collecting data for {len(pipeline_ids)} pipelines...")
        
        for pipeline_id in pipeline_ids:
            # Simulate pipeline run collection
            run_data = {
                "TimeGenerated": datetime.now().isoformat() + "Z",
                "WorkspaceId": self.workspace_id,
                "PipelineId": pipeline_id,
                "PipelineName": f"Test Pipeline {pipeline_id}",
                "RunId": f"run-{pipeline_id}-{int(time.time())}",
                "Status": "Succeeded",
                "StartTime": (datetime.now() - timedelta(minutes=10)).isoformat() + "Z",
                "EndTime": datetime.now().isoformat() + "Z",
                "DurationMs": 600000,  # 10 minutes
                "InvokeType": "Manual",
                "JobType": "Pipeline"
            }
            collected_runs.append(run_data)
            
            # Simulate activity run collection
            activity_data = {
                "TimeGenerated": datetime.now().isoformat() + "Z",
                "WorkspaceId": self.workspace_id,
                "PipelineId": pipeline_id,
                "ActivityName": "Copy Data Activity",
                "ActivityType": "Copy",
                "RunId": run_data["RunId"],
                "Status": "Succeeded",
                "StartTimeUtc": run_data["StartTime"],
                "EndTimeUtc": run_data["EndTime"],
                "DurationMs": 480000,  # 8 minutes
                "DataRead": 1024000,   # 1MB
                "DataWritten": 1024000, # 1MB
                "RecordsProcessed": 5000
            }
            collected_activities.append(activity_data)
        
        print(f"   ✅ Collected {len(collected_runs)} pipeline runs")
        print(f"   ✅ Collected {len(collected_activities)} activity runs")
        
        # Validate data structure (like in notebooks)
        assert all('TimeGenerated' in run for run in collected_runs), "Missing TimeGenerated in pipeline runs"
        assert all('WorkspaceId' in run for run in collected_runs), "Missing WorkspaceId in pipeline runs"
        
        self.results['pipeline_runs'] = collected_runs
        self.results['activity_runs'] = collected_activities
        
    def _test_dataset_monitoring_workflow(self):
        """Test dataset monitoring workflow (mimics notebook dataset cells)."""
        print("\n📊 Step 4: Dataset Monitoring Workflow")
        
        # Simulate dataset data collection
        dataset_ids = [TestConfig.DATASET_ID]
        collected_refreshes = []
        collected_metadata = []
        
        print(f"   📋 Collecting data for {len(dataset_ids)} datasets...")
        
        for dataset_id in dataset_ids:
            # Simulate dataset refresh collection
            refresh_data = {
                "TimeGenerated": datetime.now().isoformat() + "Z",
                "WorkspaceId": self.workspace_id,
                "DatasetId": dataset_id,
                "DatasetName": f"Test Dataset {dataset_id}",
                "RefreshId": f"refresh-{dataset_id}-{int(time.time())}",
                "RefreshType": "Full",
                "Status": "Completed",
                "StartTime": (datetime.now() - timedelta(minutes=15)).isoformat() + "Z",
                "EndTime": datetime.now().isoformat() + "Z",
                "DurationMs": 900000,  # 15 minutes
                "ServicePrincipalId": "test-sp-id",
                "RequestId": f"req-{int(time.time())}"
            }
            collected_refreshes.append(refresh_data)
            
            # Simulate dataset metadata collection
            metadata_data = {
                "TimeGenerated": datetime.now().isoformat() + "Z",
                "WorkspaceId": self.workspace_id,
                "DatasetId": dataset_id,
                "DatasetName": f"Test Dataset {dataset_id}",
                "Description": "Test dataset for monitoring",
                "Type": "SemanticModel",
                "CreatedDate": "2024-01-01T00:00:00Z",
                "ModifiedDate": datetime.now().isoformat() + "Z",
                "CreatedBy": "test@contoso.com",
                "ModifiedBy": "test@contoso.com"
            }
            collected_metadata.append(metadata_data)
        
        print(f"   ✅ Collected {len(collected_refreshes)} dataset refreshes")
        print(f"   ✅ Collected {len(collected_metadata)} dataset metadata records")
        
        self.results['dataset_refreshes'] = collected_refreshes
        self.results['dataset_metadata'] = collected_metadata
        
    def _test_capacity_monitoring_workflow(self):
        """Test capacity monitoring workflow (mimics notebook capacity cells)."""
        print("\n⚡ Step 5: Capacity Monitoring Workflow")
        
        # Simulate capacity metrics collection
        capacity_id = TestConfig.CAPACITY_ID
        collected_metrics = []
        
        print(f"   📋 Collecting capacity metrics for {capacity_id}...")
        
        # Generate hourly metrics for the last 24 hours
        for hour_offset in range(24):
            metric_time = datetime.now() - timedelta(hours=hour_offset)
            
            metric_data = {
                "TimeGenerated": metric_time.isoformat() + "Z",
                "CapacityId": capacity_id,
                "WorkloadType": "PowerBI",
                "CpuPercentage": 30.0 + (hour_offset * 1.5),  # Simulate varying load
                "MemoryPercentage": 40.0 + (hour_offset * 1.2),
                "ActiveRequests": max(0, 20 - hour_offset),
                "QueuedRequests": max(0, hour_offset - 10)
            }
            collected_metrics.append(metric_data)
        
        print(f"   ✅ Collected {len(collected_metrics)} capacity metrics")
        
        # Calculate summary statistics (like in notebooks)
        cpu_values = [m['CpuPercentage'] for m in collected_metrics]
        memory_values = [m['MemoryPercentage'] for m in collected_metrics]
        
        print(f"   📈 CPU Usage: {min(cpu_values):.1f}% - {max(cpu_values):.1f}% (avg: {sum(cpu_values)/len(cpu_values):.1f}%)")
        print(f"   📈 Memory Usage: {min(memory_values):.1f}% - {max(memory_values):.1f}% (avg: {sum(memory_values)/len(memory_values):.1f}%)")
        
        self.results['capacity_metrics'] = collected_metrics
        
    def _test_user_activity_workflow(self):
        """Test user activity monitoring workflow (mimics notebook user activity cells)."""
        print("\n👥 Step 6: User Activity Monitoring Workflow")
        
        # Simulate user activity collection
        collected_activities = []
        
        print(f"   📋 Collecting user activities...")
        
        # Generate various user activities
        activity_types = ["DatasetRefresh", "ReportView", "DashboardView", "DataflowRun", "NotebookRun"]
        users = ["user1@contoso.com", "user2@contoso.com", "user3@contoso.com"]
        
        for i, activity_type in enumerate(activity_types):
            for j, user_email in enumerate(users):
                activity_data = {
                    "TimeGenerated": datetime.now().isoformat() + "Z",
                    "WorkspaceId": self.workspace_id,
                    "ActivityId": f"activity-{i}-{j}-{int(time.time())}",
                    "UserId": f"user-{j}",
                    "UserEmail": user_email,
                    "ActivityType": activity_type,
                    "CreationTime": (datetime.now() - timedelta(minutes=i*10)).isoformat() + "Z",
                    "ItemName": f"Test {activity_type} Item {i}",
                    "WorkspaceName": "Test Workspace",
                    "ItemType": activity_type.replace("View", "").replace("Run", ""),
                    "ObjectId": f"obj-{i}-{j}"
                }
                collected_activities.append(activity_data)
        
        print(f"   ✅ Collected {len(collected_activities)} user activities")
        
        # Generate activity summary (like in notebooks)
        activity_summary = {}
        for activity in collected_activities:
            activity_type = activity['ActivityType']
            activity_summary[activity_type] = activity_summary.get(activity_type, 0) + 1
        
        print(f"   📊 Activity Summary:")
        for activity_type, count in activity_summary.items():
            print(f"      {activity_type}: {count}")
        
        self.results['user_activities'] = collected_activities
        
    def _test_data_ingestion_workflow(self):
        """Test data ingestion workflow (mimics notebook ingestion cells)."""
        print("\n📤 Step 7: Data Ingestion Workflow")
        
        # Collect all data for ingestion
        all_data = []
        data_types = {}
        
        for key, data_list in self.results.items():
            if isinstance(data_list, list) and data_list:
                all_data.extend(data_list)
                data_types[key] = len(data_list)
        
        print(f"   📊 Data Summary:")
        total_records = 0
        for data_type, count in data_types.items():
            print(f"      {data_type}: {count} records")
            total_records += count
        
        print(f"   📊 Total Records: {total_records}")
        
        # Simulate ingestion process (like in notebooks)
        mock_ingestion_client = MockIngestionClient()
        
        # Test batch processing
        batch_size = self.batch_size
        batches_processed = 0
        
        for i in range(0, len(all_data), batch_size):
            batch = all_data[i:i + batch_size]
            
            # Simulate ingestion call
            mock_ingestion_client.upload(
                rule_id=TestConfig.DCR_IMMUTABLE_ID,
                stream_name=TestConfig.STREAM_NAME,
                logs=batch
            )
            
            batches_processed += 1
            print(f"   📦 Processed batch {batches_processed} ({len(batch)} records)")
        
        print(f"   ✅ Data ingestion completed")
        print(f"   📊 Batches processed: {batches_processed}")
        print(f"   📊 Total records ingested: {len(mock_ingestion_client.get_uploaded_data())}")
        
        self.results['ingestion_summary'] = {
            'total_records': total_records,
            'batches_processed': batches_processed,
            'records_ingested': len(mock_ingestion_client.get_uploaded_data())
        }
        
    def _test_verification_and_reporting(self):
        """Test verification and reporting (mimics notebook final cells)."""
        print("\n✅ Step 8: Verification and Reporting")
        
        # Verify all data was collected
        expected_data_types = [
            'config', 'pipeline_runs', 'activity_runs', 
            'dataset_refreshes', 'dataset_metadata',
            'capacity_metrics', 'user_activities', 'ingestion_summary'
        ]
        
        print(f"   🔍 Verifying data collection...")
        for data_type in expected_data_types:
            if data_type in self.results:
                print(f"      ✅ {data_type}: Available")
            else:
                print(f"      ❌ {data_type}: Missing")
                raise Exception(f"Missing required data type: {data_type}")
        
        # Generate final report (like notebook summary)
        print(f"\n   📋 Final Workflow Report:")
        print(f"      Workspace ID: {self.workspace_id}")
        print(f"      Lookback Hours: {self.lookback_hours}")
        print(f"      Pipeline Runs: {len(self.results.get('pipeline_runs', []))}")
        print(f"      Activity Runs: {len(self.results.get('activity_runs', []))}")
        print(f"      Dataset Refreshes: {len(self.results.get('dataset_refreshes', []))}")
        print(f"      Capacity Metrics: {len(self.results.get('capacity_metrics', []))}")
        print(f"      User Activities: {len(self.results.get('user_activities', []))}")
        print(f"      Total Records Ingested: {self.results['ingestion_summary']['records_ingested']}")
        
        # Verify ingestion completeness
        expected_total = (
            len(self.results.get('pipeline_runs', [])) +
            len(self.results.get('activity_runs', [])) +
            len(self.results.get('dataset_refreshes', [])) +
            len(self.results.get('dataset_metadata', [])) +
            len(self.results.get('capacity_metrics', [])) +
            len(self.results.get('user_activities', []))
        )
        
        actual_total = self.results['ingestion_summary']['records_ingested']
        
        if expected_total == actual_total:
            print(f"   ✅ Data integrity verified: {expected_total} records collected and ingested")
        else:
            raise Exception(f"Data integrity check failed: Expected {expected_total}, got {actual_total}")
        
        print(f"   🎉 Workflow completed successfully!")

def run_notebook_workflow_test():
    """Run the complete notebook workflow test."""
    test = NotebookWorkflowTest()
    return test.run_complete_workflow_test()

if __name__ == "__main__":
    success = run_notebook_workflow_test()
    sys.exit(0 if success else 1)