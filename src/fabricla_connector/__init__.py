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
from . import collectors
from . import ingestion
from . import config
from . import api
from . import utils

# Import key classes and functions for direct access
from .collectors import (
    PipelineDataCollector,
    DatasetRefreshCollector, 
    CapacityUtilizationCollector,
    UserActivityCollector
)

from .ingestion import post_rows_to_dcr, FabricIngestion

from .config import (
    get_config,
    get_ingestion_config,
    get_fabric_config,
    validate_config,
    print_config_status,
    is_running_in_fabric
)

from .api import get_fabric_token, get_credentials_fabric_aware

from .workflows import (
    collect_and_ingest_pipeline_data,
    collect_and_ingest_dataset_refreshes,
    collect_and_ingest_capacity_utilization,
    collect_and_ingest_user_activity,
    run_full_monitoring_cycle_enhanced,
    collect_and_ingest_pipeline_data_enhanced,
    validate_and_test_configuration
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
    
    # Compatibility aliases
    "main_pipeline_workflow",
    "main_dataset_workflow",
    "main_capacity_workflow",
    "main_activity_workflow"
]
