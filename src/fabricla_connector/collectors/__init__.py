"""
Data collectors for Microsoft Fabric workloads.

This package provides collector classes for gathering operational data from Fabric.
Each collector focuses on a specific workload type and yields records ready for ingestion.
"""
from .base import BaseCollector
from .pipeline import PipelineDataCollector
from .dataset import DatasetRefreshCollector
from .capacity import CapacityUtilizationCollector
from .user_activity import UserActivityCollector
from .permissions import AccessPermissionsCollector

# Import Spark collector functions
from .spark import (
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

# Legacy collector classes - these need to be implemented
# For now, they are None placeholders (legacy_collectors.py was removed)
OneLakeStorageCollector = None
SparkJobCollector = None
NotebookCollector = None
GitIntegrationCollector = None
DataLineageCollector = None
SemanticModelCollector = None
RealTimeIntelligenceCollector = None
MirroringCollector = None
MLAICollector = None

# Legacy mapper functions - use new mappers from mappers/ subpackage instead
# These are exported for backward compatibility
from ..mappers import (
    PipelineRunMapper,
    ActivityRunMapper,
    DataflowRunMapper,
    DatasetRefreshMapper,
    CapacityMetricMapper,
    UserActivityMapper
)

# Create wrapper functions that use new mapper classes
def map_pipeline_run(workspace_id, pipeline_id, pipeline_name, run):
    """Legacy wrapper for PipelineRunMapper"""
    return PipelineRunMapper.map(workspace_id, pipeline_id, pipeline_name, run)

def map_activity_run(workspace_id, pipeline_id, pipeline_run_id, activity):
    """Legacy wrapper for ActivityRunMapper"""
    return ActivityRunMapper.map(workspace_id, pipeline_id, pipeline_run_id, activity)

def map_dataflow_run(workspace_id, dataflow_id, dataflow_name, run):
    """Legacy wrapper for DataflowRunMapper"""
    return DataflowRunMapper.map(workspace_id, dataflow_id, dataflow_name, run)

def map_dataset_refresh(workspace_id, dataset_id, dataset_name, refresh):
    """Legacy wrapper for DatasetRefreshMapper"""
    return DatasetRefreshMapper.map(workspace_id, dataset_id, dataset_name, refresh)

def map_dataset_metadata(workspace_id, dataset):
    """Legacy wrapper - to be implemented"""
    return {"WorkspaceId": workspace_id, "DatasetId": dataset.get("id", "")}

def map_capacity_metric(capacity_id, metric):
    """Legacy wrapper for CapacityMetricMapper"""
    return CapacityMetricMapper.map(capacity_id, metric)

def map_user_activity(workspace_id, activity):
    """Legacy wrapper for UserActivityMapper"""
    return UserActivityMapper.map(workspace_id, activity)

__all__ = [
    # New refactored classes
    'BaseCollector',
    'PipelineDataCollector',
    'DatasetRefreshCollector',
    'CapacityUtilizationCollector',
    'UserActivityCollector',
    # Legacy collector classes
    'OneLakeStorageCollector',
    'SparkJobCollector',
    'NotebookCollector',
    'GitIntegrationCollector',
    'AccessPermissionsCollector',
    'DataLineageCollector',
    'SemanticModelCollector',
    'RealTimeIntelligenceCollector',
    'MirroringCollector',
    'MLAICollector',
    # Legacy mapper functions
    'map_pipeline_run',
    'map_activity_run',
    'map_dataflow_run',
    'map_dataset_refresh',
    'map_dataset_metadata',
    'map_capacity_metric',
    'map_user_activity',
    # Spark collector functions
    'collect_livy_sessions_workspace',
    'collect_livy_sessions_notebook',
    'collect_livy_sessions_sparkjob',
    'collect_livy_sessions_lakehouse',
    'collect_spark_logs',
    'collect_spark_metrics',
    'collect_spark_resource_usage',
    'collect_resource_usage_for_active_sessions',
    'collect_spark_applications_workspace',
    'collect_spark_applications_item',
]
