"""
Data mappers for Microsoft Fabric workloads.

This module provides mapper classes that transform raw API responses
into Log Analytics schema format for ingestion.
"""

from typing import Dict, Any
from .collectors import (
    map_pipeline_run as _map_pipeline_run,
    map_activity_run as _map_activity_run,
    map_dataset_refresh as _map_dataset_refresh,
    map_capacity_metric as _map_capacity_metric,
    map_user_activity as _map_user_activity
)


class PipelineRunMapper:
    """Mapper for pipeline run data."""
    
    @staticmethod
    def map(workspace_id: str, pipeline_id: str, pipeline_name: str, run: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a pipeline run to Log Analytics schema.
        
        Args:
            workspace_id: Fabric workspace ID
            pipeline_id: Pipeline ID
            pipeline_name: Pipeline name
            run: Raw pipeline run data from API
            
        Returns:
            Mapped pipeline run data for Log Analytics
        """
        return _map_pipeline_run(workspace_id, pipeline_id, pipeline_name, run)


class ActivityRunMapper:
    """Mapper for activity run data."""
    
    @staticmethod
    def map(workspace_id: str, pipeline_id: str, pipeline_run_id: str, activity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map an activity run to Log Analytics schema.
        
        Args:
            workspace_id: Fabric workspace ID
            pipeline_id: Pipeline ID
            pipeline_run_id: Pipeline run ID
            activity: Raw activity run data from API
            
        Returns:
            Mapped activity run data for Log Analytics
        """
        return _map_activity_run(workspace_id, pipeline_id, pipeline_run_id, activity)


class DatasetRefreshMapper:
    """Mapper for dataset refresh data."""
    
    @staticmethod
    def map(workspace_id: str, dataset_id: str, dataset_name: str, refresh: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a dataset refresh to Log Analytics schema.
        
        Args:
            workspace_id: Fabric workspace ID
            dataset_id: Dataset ID
            dataset_name: Dataset name
            refresh: Raw dataset refresh data from API
            
        Returns:
            Mapped dataset refresh data for Log Analytics
        """
        return _map_dataset_refresh(workspace_id, dataset_id, dataset_name, refresh)


class CapacityMetricMapper:
    """Mapper for capacity utilization metrics."""
    
    @staticmethod
    def map(capacity_id: str, metric: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map capacity utilization metrics to Log Analytics schema.
        
        Args:
            capacity_id: Fabric capacity ID
            metric: Raw capacity metric data from API
            
        Returns:
            Mapped capacity metric data for Log Analytics
        """
        return _map_capacity_metric(capacity_id, metric)


class UserActivityMapper:
    """Mapper for user activity data."""
    
    @staticmethod
    def map(workspace_id: str, activity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map user activity to Log Analytics schema.
        
        Args:
            workspace_id: Fabric workspace ID
            activity: Raw user activity data from API
            
        Returns:
            Mapped user activity data for Log Analytics
        """
        return _map_user_activity(workspace_id, activity)


# Export all mapper classes
__all__ = [
    'PipelineRunMapper',
    'ActivityRunMapper', 
    'DatasetRefreshMapper',
    'CapacityMetricMapper',
    'UserActivityMapper'
]