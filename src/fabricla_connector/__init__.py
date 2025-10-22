"""
FabricLA-Connector: Microsoft Fabric to Log Analytics data collection and ingestion framework.

This package provides a comprehensive framework for collecting data from Microsoft Fabric 
workloads and ingesting it into Azure Monitor Log Analytics.

Main Features:
- Fabric-aware authentication (supports workspace identity, managed identity, client credentials)
- Data collectors for pipelines, datasets, capacity utilization, and user activity
- Robust ingestion with retry logic and chunking
- Environment detection (Fabric vs local)
- Configuration management with Key Vault integration

Quick Start:
```python
from fabricla_connector import workflows

# Collect and ingest pipeline data
result = workflows.collect_and_ingest_pipeline_data(
    workspace_id="your-workspace-id",
    lookback_hours=24
)

# Run full monitoring cycle
full_result = workflows.run_full_monitoring_cycle(
    workspace_id="your-workspace-id",
    capacity_id="your-capacity-id"
)
```

For advanced usage:
```python
from fabricla_connector.collectors import PipelineDataCollector
from fabricla_connector.ingestion import post_rows_to_dcr
from fabricla_connector.config import get_config, validate_config

# Advanced collector usage
collector = PipelineDataCollector("workspace-id", lookback_hours=48)
records = list(collector.collect_pipeline_runs())

# Direct ingestion
result = post_rows_to_dcr(
    records=records,
    dce_endpoint="your-dce-endpoint",
    dcr_immutable_id="your-dcr-id",
    stream_name="your-stream"
)
```
"""

# Import main modules for easy access
from . import workflows
from . import config
from . import utils
from . import monitoring_detection

# Import refactored subpackages
from .api import FabricAPIClient
from .collectors import (
    PipelineDataCollector,
    DatasetRefreshCollector, 
    CapacityUtilizationCollector,
    UserActivityCollector,
    # Spark collector functions
    collect_livy_sessions_workspace,
    collect_livy_sessions_notebook,
    collect_livy_sessions_sparkjob,
    collect_livy_sessions_lakehouse,
    collect_spark_logs,
    collect_spark_metrics,
    collect_spark_resource_usage,
    collect_resource_usage_for_active_sessions,
    collect_spark_applications_workspace,
    collect_spark_applications_item
)
from .mappers import (
    PipelineRunMapper,
    ActivityRunMapper,
    DataflowRunMapper,
    DatasetRefreshMapper,
    DatasetMetadataMapper,
    CapacityMetricMapper,
    UserActivityMapper,
    LivySessionMapper,
    SparkResourceMapper
)
from .ingestion import (
    post_rows_to_dcr,
    AzureMonitorIngestionClient,
    chunk_records,
    RetryPolicy
)

# Import modules for backward compatibility
from . import api
from . import collectors
from . import mappers
from . import ingestion

# Backward compatibility alias
FabricIngestion = AzureMonitorIngestionClient

from .config import (
    get_config,
    get_ingestion_config,
    get_fabric_config,
    get_monitoring_config,
    validate_config,
    print_config_status,
    is_running_in_fabric
)

# Import authentication functions (now re-exported from api package)
from .api import get_fabric_token, get_credentials_fabric_aware

from .workflows import (
    collect_and_ingest_pipeline_data,
    collect_and_ingest_dataset_refreshes,
    collect_and_ingest_capacity_utilization,
    collect_and_ingest_user_activity,
    collect_and_ingest_onelake_storage,
    collect_and_ingest_spark_jobs,
    collect_and_ingest_notebooks,
    collect_and_ingest_git_integration,
    # Spark Monitoring API workflows
    collect_and_ingest_spark_applications,
    collect_and_ingest_spark_item_applications,
    collect_and_ingest_spark_logs,
    collect_and_ingest_spark_metrics,
    comprehensive_spark_monitoring,
    run_operational_monitoring_cycle,
    run_full_monitoring_cycle_enhanced,
    collect_and_ingest_pipeline_data_enhanced,
    validate_and_test_configuration,
    # Intelligent workflows
    run_intelligent_monitoring_cycle,
    check_workspace_monitoring_status,
    get_collection_recommendations,
    run_full_monitoring_cycle_intelligent,
    run_complementary_monitoring_cycle,
    run_minimal_monitoring_cycle,
    # Phase 2: Security & Governance
    collect_and_ingest_access_permissions,
    collect_and_ingest_workspace_config,
    collect_and_ingest_data_lineage,
    collect_and_ingest_semantic_models,
    run_compliance_monitoring_cycle,
    # Phase 3: Advanced Workloads
    collect_and_ingest_real_time_intelligence,
    collect_and_ingest_mirroring,
    collect_and_ingest_ml_ai,
    run_advanced_workloads_monitoring_cycle,
    # Comprehensive monitoring
    run_comprehensive_monitoring_cycle
)

from .monitoring_detection import (
    get_monitoring_detector,
    get_monitoring_strategy,
    print_monitoring_status
)

# Version information
__version__ = "1.0.0"
__author__ = "Microsoft Fabric Team"
__description__ = "Microsoft Fabric to Log Analytics connector framework"

# Convenience aliases for backward compatibility
main_pipeline_workflow = workflows.main_pipeline_workflow
main_dataset_workflow = workflows.main_dataset_workflow
main_capacity_workflow = workflows.main_capacity_workflow
main_activity_workflow = workflows.main_activity_workflow

# Package metadata
__all__ = [
    # Modules
    "workflows",
    "collectors", 
    "ingestion",
    "config",
    "api",
    "utils",
    
    # Key classes
    "PipelineDataCollector",
    "DatasetRefreshCollector",
    "CapacityUtilizationCollector", 
    "UserActivityCollector",
    "FabricIngestion",
    
    # Key functions
    "get_fabric_token",
    "get_credentials_fabric_aware",
    "post_rows_to_dcr",
    "get_config",
    "get_ingestion_config",
    "get_fabric_config",
    "get_monitoring_config",
    "validate_config",
    "print_config_status",
    "is_running_in_fabric",
    
    # Workflow functions
    "collect_and_ingest_pipeline_data",
    "collect_and_ingest_dataset_refreshes", 
    "collect_and_ingest_capacity_utilization",
    "collect_and_ingest_user_activity",
    "run_full_monitoring_cycle_enhanced",
    "collect_and_ingest_pipeline_data_enhanced",
    "validate_and_test_configuration",
    
    # Intelligent monitoring functions
    "run_intelligent_monitoring_cycle",
    "check_workspace_monitoring_status",
    "get_collection_recommendations",
    "run_full_monitoring_cycle_intelligent",
    "run_complementary_monitoring_cycle", 
    "run_minimal_monitoring_cycle",
    "get_monitoring_detector",
    "get_monitoring_strategy",
    "print_monitoring_status",
    
    # Compatibility aliases
    "main_pipeline_workflow",
    "main_dataset_workflow",
    "main_capacity_workflow",
    "main_activity_workflow"
]
