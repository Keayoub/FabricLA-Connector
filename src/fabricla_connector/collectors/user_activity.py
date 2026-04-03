"""
User activity data collectors.
"""
from typing import Iterator, Dict, Any
from .base import BaseCollector
from ..ingestion.retry import RetryPolicy
from ..api.exceptions import FabricRateLimitError


class UserActivityCollector(BaseCollector):
    """
    Collector for user activity monitoring via the Power BI Admin Activity Events API.

    API: GET https://api.powerbi.com/v1.0/myorg/admin/activityevents
    - Requires Tenant.Read.All scope (delegated) or service principal auth.
    - Tenant-wide: returns all activity events, not scoped to a single workspace.
    - startDateTime and endDateTime must be on the same UTC day; max 28-day lookback.
    - Rate limit: 200 requests/hour.
    """

    _retry_policy = RetryPolicy(max_retries=3, base_delay=60.0, max_delay=300.0, exponential=False)
    
    def collect(self) -> Iterator[Dict[str, Any]]:
        """
        Collect user activity data.
        
        Yields:
            User activity records mapped to Log Analytics schema
        """
        yield from self.collect_user_activities()
    
    def collect_user_activities(self) -> Iterator[Dict[str, Any]]:
        """
        Collect user activity data with retry on rate-limit (429) responses.
        
        Yields:
            User activity records
        """
        from ..mappers.user_activity import UserActivityMapper

        def _fetch() -> list:
            return self.client.get_user_activities(
                self.workspace_id,
                lookback_hours=self.lookback_hours,
            )

        try:
            activities = self._retry_policy.execute(_fetch, operation_name="get_user_activities")
        except FabricRateLimitError:
            return
        except Exception:
            return

        for activity in activities:
            yield UserActivityMapper.map(
                workspace_id=self.workspace_id,
                activity=activity,
            )
