"""
Dataset data mappers.
Transform raw Fabric API responses to Log Analytics schema.
"""
from typing import Dict, Any
from .base import BaseMapper
from ..utils import parse_iso, iso_now


class DatasetRefreshMapper(BaseMapper):
    """Map dataset refresh data to Log Analytics schema."""
    
    @staticmethod
    def map(workspace_id: str, dataset_id: str, dataset_name: str, refresh: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map dataset refresh to Log Analytics schema.
        
        Args:
            workspace_id: Fabric workspace ID
            dataset_id: Dataset ID
            dataset_name: Dataset display name
            refresh: Raw dataset refresh data from API
            
        Returns:
            Mapped dataset refresh data
        """
        start_time = refresh.get('startTime')
        end_time = refresh.get('endTime')
        duration_ms = None
        
        if start_time and end_time:
            try:
                start_dt = parse_iso(start_time)
                end_dt = parse_iso(end_time)
                if start_dt and end_dt:
                    duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
            except:
                pass
        
        return {
            "TimeGenerated": end_time or start_time or iso_now(),
            "WorkspaceId": workspace_id,
            "DatasetId": dataset_id,
            "DatasetName": dataset_name,
            "RefreshId": refresh.get('id'),
            "RefreshType": refresh.get('refreshType'),
            "Status": refresh.get('status'),
            "StartTime": start_time,
            "EndTime": end_time,
            "DurationMs": duration_ms,
            "ServicePrincipalId": refresh.get('servicePrincipalId'),
            "ErrorCode": refresh.get('errorCode'),
            "ErrorMessage": refresh.get('errorMessage'),
            "RequestId": refresh.get('requestId')
        }


class DatasetMetadataMapper(BaseMapper):
    """Map dataset metadata to Log Analytics schema."""
    
    @staticmethod
    def map(workspace_id: str, dataset: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map dataset metadata to Log Analytics schema.
        
        Args:
            workspace_id: Fabric workspace ID
            dataset: Raw dataset metadata from API
            
        Returns:
            Mapped dataset metadata
        """
        return {
            "TimeGenerated": iso_now(),
            "WorkspaceId": workspace_id,
            "DatasetId": dataset.get('id'),
            "DatasetName": dataset.get('displayName'),
            "Description": dataset.get('description'),
            "Type": dataset.get('type'),
            "CreatedDate": dataset.get('createdDate'),
            "ModifiedDate": dataset.get('modifiedDate'),
            "CreatedBy": dataset.get('createdBy'),
            "ModifiedBy": dataset.get('modifiedBy')
        }
