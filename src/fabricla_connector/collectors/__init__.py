"""
Data collectors for Microsoft Fabric workloads.

This package provides collector classes for gathering operational data from Fabric.
Each collector focuses on a specific workload type and yields records ready for ingestion.
"""
from typing import Any
from .base import BaseCollector
from .pipeline import PipelineDataCollector
from .dataset import DatasetRefreshCollector
from .capacity import CapacityUtilizationCollector
from .user_activity import UserActivityCollector
from .permissions import AccessPermissionsCollector
from .onelake import OneLakeStorageCollector
from .spark_job import SparkJobCollector
from .notebook import NotebookCollector
from .git_integration import GitIntegrationCollector
from .data_lineage import DataLineageCollector
from .semantic_model import SemanticModelCollector
from .realtime_intelligence import RealTimeIntelligenceCollector
from .mirroring import MirroringCollector
from .ml_ai import MLAICollector

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

# Collectors not yet implemented — stub classes give a clear error at instantiation
# rather than a confusing TypeError at attribute access.
class _NotImplementedCollector:
    """Base for unimplemented collector stubs."""
    _name: str = "Collector"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(
            f"{self.__class__.__name__} is not yet implemented. "
            "Track progress at https://github.com/Keayoub/FabricLA-Connector/issues"
        )


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
