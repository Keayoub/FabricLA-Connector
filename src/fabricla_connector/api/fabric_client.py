"""
Fabric API client with authentication and error handling.
Uses only official Fabric REST APIs.
"""
import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .exceptions import (
    FabricAPIException,
    FabricAuthenticationError,
    FabricAuthorizationError,
    FabricResourceNotFoundError,
    FabricRateLimitError
)


class FabricAPIClient:
    """
    Client for interacting with Microsoft Fabric REST APIs.
    Handles authentication, error handling, pagination, and rate limiting.
    """
    
    BASE_URL = "https://api.fabric.microsoft.com/v1"
    
    def __init__(self, token: str):
        """
        Initialize Fabric API client.
        
        Args:
            token: Bearer token for Fabric API authentication
        """
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def _handle_response(self, response: requests.Response, context: str) -> Any:
        """
        Handle API response with detailed error handling.
        
        Args:
            response: HTTP response object
            context: Description of the API call for error messages
            
        Returns:
            Parsed JSON response data
            
        Raises:
            FabricAPIException: For various API errors
        """
        print(f"[DEBUG] API call: {context} - Status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            print(f"WARNING: 429 Rate Limited - {context}")
            print(f"   Waiting {retry_after} seconds before retry...")
            time.sleep(retry_after)
            raise FabricRateLimitError(
                f"Rate limited: {context}",
                retry_after=retry_after,
                status_code=response.status_code
            )
        
        if response.status_code == 401:
            print(f"ERROR: 401 Unauthorized - {context}")
            print("   Check: Token validity, Fabric.ReadAll permission, admin consent, tenant ID")
            raise FabricAuthenticationError(
                f"Authentication failed: {context}",
                status_code=response.status_code,
                response_text=response.text[:200]
            )
        
        if response.status_code == 403:
            print(f"ERROR: 403 Forbidden - {context}")
            print("   The service principal needs 'Fabric.ReadAll' application permission")
            raise FabricAuthorizationError(
                f"Permission denied: {context}",
                status_code=response.status_code,
                response_text=response.text[:200]
            )
        
        if response.status_code == 404:
            print(f"ERROR: 404 Not Found - {context}")
            raise FabricResourceNotFoundError(
                f"Resource not found: {context}",
                status_code=response.status_code,
                response_text=response.text[:200]
            )
        
        # Default error handling
        try:
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
        except:
            error_msg = f'HTTP {response.status_code}: {response.text[:200]}'
        
        print(f"ERROR: API Error ({response.status_code}) for {context}: {error_msg}")
        raise FabricAPIException(
            f"API error: {error_msg} - {context}",
            status_code=response.status_code,
            response_text=response.text[:200]
        )
    
    def get(self, endpoint: str, params: Optional[Dict] = None, context: str = "") -> Any:
        """
        Make GET request to Fabric API.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            context: Description for error messages
            
        Returns:
            Parsed JSON response
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params)
        return self._handle_response(response, context or f"GET {endpoint}")
    
    def get_paginated(self, endpoint: str, params: Optional[Dict] = None, context: str = "") -> List[Dict]:
        """
        Make GET request with automatic pagination handling.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            context: Description for error messages
            
        Returns:
            List of all items across all pages
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        all_items = []
        continuation_token = None
        
        while True:
            request_params = params.copy() if params else {}
            if continuation_token:
                request_params['continuationToken'] = continuation_token
            
            try:
                response = self.session.get(url, params=request_params)
                data = self._handle_response(response, context or f"GET {endpoint}")
                
                items = data.get('value', [])
                all_items.extend(items)
                
                continuation_token = data.get('continuationToken')
                if not continuation_token:
                    break
                    
            except FabricRateLimitError:
                # Retry after rate limit delay (already handled in _handle_response)
                continue
        
        return all_items
    
    # === Workspace Operations ===
    
    def list_workspace_items(self, workspace_id: str, item_type: Optional[str] = None) -> List[Dict]:
        """
        List items in a workspace.
        
        Args:
            workspace_id: Fabric workspace ID
            item_type: Optional filter by type (DataPipeline, Dataflow, SemanticModel, etc.)
            
        Returns:
            List of items
        """
        params = {"type": item_type} if item_type else {}
        return self.get_paginated(
            f"workspaces/{workspace_id}/items",
            params=params,
            context=f"list items in workspace {workspace_id}"
        )
    
    def get_item(self, workspace_id: str, item_id: str) -> Dict:
        """
        Get item metadata.
        
        Args:
            workspace_id: Fabric workspace ID
            item_id: Item ID
            
        Returns:
            Item metadata
        """
        return self.get(
            f"workspaces/{workspace_id}/items/{item_id}",
            context=f"get item {item_id}"
        )
    
    # === Job Operations ===
    
    def list_item_job_instances(
        self, 
        workspace_id: str, 
        item_id: str, 
        lookback_hours: Optional[int] = None
    ) -> List[Dict]:
        """
        List job instances for an item (pipeline/dataflow).
        
        Args:
            workspace_id: Fabric workspace ID
            item_id: Item ID
            lookback_hours: Optional filter by time window
            
        Returns:
            List of job instances
        """
        instances = self.get_paginated(
            f"workspaces/{workspace_id}/items/{item_id}/jobs/instances",
            context=f"list job instances for item {item_id}"
        )
        
        # Filter by lookback if specified
        if lookback_hours:
            from ..utils import parse_iso
            since_time = datetime.now() - timedelta(hours=lookback_hours)
            filtered_instances = []
            for inst in instances:
                start_time = parse_iso(inst.get('startTimeUtc'))
                if start_time and start_time >= since_time:
                    filtered_instances.append(inst)
            instances = filtered_instances
        
        return instances
    
    def get_activity_runs(self, workspace_id: str, pipeline_id: str, run_id: str) -> List[Dict]:
        """
        Get activity runs for a pipeline run.
        
        Args:
            workspace_id: Fabric workspace ID
            pipeline_id: Pipeline ID
            run_id: Run ID
            
        Returns:
            List of activity runs
        """
        try:
            data = self.get(
                f"workspaces/{workspace_id}/items/{pipeline_id}/jobs/instances/{run_id}/activities",
                context=f"get activity runs for pipeline {pipeline_id}, run {run_id}"
            )
            return data.get('value', [])
        except FabricResourceNotFoundError:
            return []  # No activity runs available
    
    # === Dataset Operations ===
    
    def list_datasets(self, workspace_id: str) -> List[Dict]:
        """
        List datasets (Semantic Models) in a workspace.
        
        Args:
            workspace_id: Fabric workspace ID
            
        Returns:
            List of datasets
        """
        return self.list_workspace_items(workspace_id, item_type="SemanticModel")
    
    def get_dataset_refreshes(
        self, 
        workspace_id: str, 
        dataset_id: str,
        lookback_hours: Optional[int] = None
    ) -> List[Dict]:
        """
        Get refresh history for a dataset.
        
        Args:
            workspace_id: Fabric workspace ID
            dataset_id: Dataset ID
            lookback_hours: Optional filter by time window
            
        Returns:
            List of refresh records
        """
        try:
            data = self.get(
                f"workspaces/{workspace_id}/items/{dataset_id}/refreshes",
                context=f"get refresh history for dataset {dataset_id}"
            )
            
            refreshes = data.get('value', [])
            
            # Filter by lookback if specified
            if lookback_hours:
                from ..utils import parse_iso
                since_time = datetime.now() - timedelta(hours=lookback_hours)
                filtered_refreshes = []
                for ref in refreshes:
                    start_time = parse_iso(ref.get('startTime'))
                    if start_time and start_time >= since_time:
                        filtered_refreshes.append(ref)
                refreshes = filtered_refreshes
            
            return refreshes
        except FabricAPIException:
            return []
    
    # === Capacity Operations ===
    
    def get_capacity_utilization(
        self,
        capacity_id: str,
        lookback_hours: Optional[int] = None
    ) -> List[Dict]:
        """
        Get current workload state for a capacity via the Power BI REST API.

        API: GET https://api.powerbi.com/v1.0/myorg/capacities/{capacityId}/workloads
        Returns the enabled/disabled state and max memory % for each workload type
        (Dataflows, AIML, Datamart, etc.).

        Note: For time-series utilization metrics (CU%, memory%), configure
        Azure Monitor diagnostic settings on the capacity resource or use the
        Fabric Capacity Metrics Power BI app.

        Args:
            capacity_id: Fabric capacity ID.
            lookback_hours: Unused (workload state is current, not time-series).

        Returns:
            List of workload state dicts with keys: name, state,
            maxMemoryPercentageSetByUser.
        """
        try:
            url = f"https://api.powerbi.com/v1.0/myorg/capacities/{capacity_id}/workloads"
            response = self.session.get(url, timeout=60)

            if response.status_code == 200:
                return response.json().get("value", [])
            elif response.status_code in (401, 403):
                print(
                    f"WARNING: {response.status_code} on capacity workloads - "
                    "requires Capacity.Read.All scope."
                )
                return []
            else:
                print(
                    f"WARNING: Capacity workloads API returned {response.status_code}: "
                    f"{response.text[:200]}"
                )
                return []
        except FabricAPIException:
            return []
    
    # === Admin Operations ===

    def get_user_activities(
        self,
        workspace_id: str,
        lookback_hours: Optional[int] = None
    ) -> List[Dict]:
        """
        Get user activity logs via the Power BI Admin Activity Events API.

        API: GET https://api.powerbi.com/v1.0/myorg/admin/activityevents
        Requires Tenant.Read.All scope (delegated) or service principal auth.
        Rate limit: 200 requests/hour. startDateTime and endDateTime must be on
        the same UTC day and within the last 28 days.

        Args:
            workspace_id: Preserved for backward compatibility; this API is
                          tenant-wide (not scoped to a single workspace).
            lookback_hours: Hours to look back. Capped at 24h (same-day
                            constraint of the API). Defaults to 1h.

        Returns:
            List of activity event dicts (activityEventEntities).
        """
        from datetime import timezone

        try:
            hours = min(lookback_hours or 1, 24)
            end_dt = datetime.now(timezone.utc)
            start_dt = end_dt - timedelta(hours=hours)

            # API requires datetime wrapped in single quotes
            def _fmt(dt: datetime) -> str:
                return f"'{dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')}'"

            url = "https://api.powerbi.com/v1.0/myorg/admin/activityevents"
            base_params = {
                "startDateTime": _fmt(start_dt),
                "endDateTime": _fmt(end_dt),
            }

            all_activities: List[Dict] = []
            continuation_token = None

            while True:
                params = (
                    {"continuationToken": continuation_token}
                    if continuation_token
                    else base_params
                )
                response = self.session.get(url, params=params, timeout=60)

                if response.status_code == 200:
                    data = response.json()
                    all_activities.extend(data.get("activityEventEntities", []))
                    continuation_token = data.get("continuationToken")
                    if not continuation_token:
                        break
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    print(f"WARNING: 429 Rate limited on activity events - retry after {retry_after}s")
                    raise FabricRateLimitError(
                        "Rate limited: activity events",
                        retry_after=retry_after,
                        status_code=429,
                    )
                elif response.status_code in (401, 403):
                    print(
                        f"WARNING: {response.status_code} on activity events - "
                        "requires Tenant.Read.All scope or service principal auth."
                    )
                    return []
                else:
                    print(
                        f"WARNING: Activity events API returned {response.status_code}: "
                        f"{response.text[:200]}"
                    )
                    return []

            return all_activities

        except FabricAuthorizationError as e:
            print(f"[Warning] User activity requires Tenant.Read.All permissions: {e}")
            return []
        except FabricAPIException:
            return []
