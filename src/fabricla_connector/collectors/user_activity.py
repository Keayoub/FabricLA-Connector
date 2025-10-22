"""
User activity data collectors.
"""
from typing import Iterator, Dict, Any
from .base import BaseCollector


class UserActivityCollector(BaseCollector):
    """
    Collector for user activity monitoring.
    
    Requires admin permissions in Fabric.
    Collects user interactions, item access, and workspace activities.
    """
    
    def collect(self) -> Iterator[Dict[str, Any]]:
        """
        Collect user activity data.
        
        Yields:
            User activity records mapped to Log Analytics schema
        """
        yield from self.collect_user_activities()
    
    def collect_user_activities(self) -> Iterator[Dict[str, Any]]:
        """
        Collect user activity data.
        
        Yields:
            User activity records
        """
        from ..mappers.user_activity import UserActivityMapper
        
        activities = self.client.get_user_activities(
            self.workspace_id,
            lookback_hours=self.lookback_hours
        )
        
        for activity in activities:
            yield UserActivityMapper.map(
                workspace_id=self.workspace_id,
                activity=activity
            )
