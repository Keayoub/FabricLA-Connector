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
        Map user activity to Log Analytics schema.
        
        Args:
            workspace_id: Fabric workspace ID
            activity: Raw user activity data from API
            
        Returns:
            Mapped user activity data
        """
        return {
            "TimeGenerated": activity.get('CreationTime') or iso_now(),
            "WorkspaceId": workspace_id,
            "ActivityId": activity.get('Id'),
            "UserId": activity.get('UserId'),
            "UserEmail": activity.get('UserKey'),
            "ActivityType": activity.get('Activity'),
            "CreationTime": activity.get('CreationTime'),
            "ItemName": activity.get('ItemName'),
            "WorkspaceName": activity.get('WorkspaceName'),
            "ItemType": activity.get('ItemType'),
            "ObjectId": activity.get('ObjectId')
        }
