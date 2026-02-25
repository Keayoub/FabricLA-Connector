"""
User activity mappers.
Transform raw Fabric API responses to Log Analytics schema.
"""
from typing import Dict, Any
from .base import BaseMapper
from ..utils import iso_now


class UserActivityMapper(BaseMapper):
    """Map user activity data to Log Analytics schema."""
    
    @staticmethod
    def map(workspace_id: str, activity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a Power BI Admin Activity Event to Log Analytics schema.

        Args:
            workspace_id: Fabric workspace ID (may be empty; activity events
                          are tenant-wide from api.powerbi.com)
            activity: Raw activity event from the activityEventEntities array

        Returns:
            Mapped user activity data
        """
        return {
            "TimeGenerated": activity.get('CreationTime') or iso_now(),
            "WorkspaceId": activity.get('WorkspaceId') or workspace_id,
            "ActivityId": activity.get('Id'),
            "UserId": activity.get('UserId'),
            "UserKey": activity.get('UserKey'),
            "Activity": activity.get('Activity'),
            "Operation": activity.get('Operation'),
            "IsSuccess": activity.get('IsSuccess'),
            "RequestId": activity.get('RequestId'),
            "Workload": activity.get('Workload'),
            "ClientIP": activity.get('ClientIP'),
            "OrganizationId": activity.get('OrganizationId'),
            "CreationTime": activity.get('CreationTime'),
            "ItemName": activity.get('ItemName'),
            "WorkspaceName": activity.get('WorkSpaceName') or activity.get('WorkspaceName'),
            "ItemType": activity.get('ItemType'),
            "ObjectId": activity.get('ObjectId'),
            "ArtifactId": activity.get('ArtifactId'),
            "ArtifactName": activity.get('ArtifactName'),
            "CapacityId": activity.get('CapacityId'),
            "CapacityName": activity.get('CapacityName'),
        }
