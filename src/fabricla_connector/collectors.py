"""
Data collection modules for Microsoft Fabric workloads.
Implements collectors for pipelines, datasets, capacity utilization, and user activity.
"""
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Iterator
import time
from .api import get_fabric_token
from .utils import parse_iso, within_lookback, iso_now


class FabricAPIException(Exception):
    """Custom exception for Fabric API errors"""
    pass


def handle_api_response(response: requests.Response, context: str) -> Any:
    """Handle API response with detailed error handling and debugging"""
    print(f"[DEBUG] API call: {context} - Status: {response.status_code}")
    
    if response.status_code == 200:
        return response.json()
        
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        print(f"⚠️ 429 Rate Limited - {context}")
        print(f"   Waiting {retry_after} seconds before retry...")
        print("   API rate limit exceeded, consider reducing concurrent requests")
        time.sleep(retry_after)
        raise FabricAPIException(f"Rate limited: {context}")
    
    if response.status_code == 401:
        print(f"❌ 401 Unauthorized - Authentication failed for {context}")
        print("   Possible causes:")
        print("   1. Token expired or invalid")
        print("   2. Service principal doesn't have 'Fabric.ReadAll' permission")
        print("   3. Service principal not granted admin consent")
        print("   4. Wrong tenant ID")
        print(f"   Response: {response.text[:200]}")
        raise FabricAPIException(f"Authentication failed: {context}")
        
    if response.status_code == 403:
        print(f"❌ 403 Forbidden - Permission denied for {context}")
        print("   The service principal needs 'Fabric.ReadAll' application permission")
        print(f"   Response: {response.text[:200]}")
        raise FabricAPIException(f"Permission denied: {context}")
        
    if response.status_code == 404:
        print(f"❌ 404 Not Found - Resource doesn't exist for {context}")
        print(f"   Response: {response.text[:200]}")
        raise FabricAPIException(f"Resource not found: {context}")
    
    # Default error handling
    try:
        error_data = response.json()
        error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
    except:
        error_msg = f'HTTP {response.status_code}: {response.text[:200]}'
    
    print(f"❌ API Error ({response.status_code}) for {context}: {error_msg}")
    raise FabricAPIException(f"API error: {error_msg} - {context}")


def list_item_job_instances(workspace_id: str, item_id: str, item_type: str, token: str, lookback_hours: int = 24) -> List[Dict]:
    """Get job instances for a specific item (pipeline/dataflow) within lookback period"""
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{item_id}/jobs/instances"
    headers = {"Authorization": f"Bearer {token}"}
    
    since_time = datetime.now() - timedelta(hours=lookback_hours)
    instances = []
    page_token = None
    
    while True:
        params = {}
        if page_token:
            params['continuationToken'] = page_token
            
        try:
            response = requests.get(url, headers=headers, params=params)
            data = handle_api_response(response, f"list job instances for {item_type} {item_id}")
            
            for instance in data.get('value', []):
                start_time = parse_iso(instance.get('startTimeUtc'))
                if start_time and start_time >= since_time:
                    instances.append(instance)
            
            page_token = data.get('continuationToken')
            if not page_token:
                break
                
        except FabricAPIException as e:
            if "Rate limited" in str(e):
                continue  # Retry after delay
            raise
    
    return instances


def query_pipeline_activity_runs(workspace_id: str, pipeline_id: str, run_id: str, token: str) -> List[Dict]:
    """Get activity runs for a specific pipeline run"""
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{pipeline_id}/jobs/instances/{run_id}/activities"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        data = handle_api_response(response, f"query activity runs for pipeline {pipeline_id}, run {run_id}")
        return data.get('value', [])
    except FabricAPIException as e:
        if "not found" in str(e).lower():
            return []  # No activity runs available
        raise


def list_workspace_datasets(workspace_id: str, token: str) -> List[Dict]:
    """List all datasets in a workspace"""
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"type": "SemanticModel"}  # Datasets are called Semantic Models in Fabric API
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = handle_api_response(response, f"list datasets in workspace {workspace_id}")
        return data.get('value', [])
    except FabricAPIException:
        return []


def get_dataset_refresh_history(workspace_id: str, dataset_id: str, token: str, lookback_hours: int = 24) -> List[Dict]:
    """Get refresh history for a dataset within lookback period"""
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{dataset_id}/refreshes"
    headers = {"Authorization": f"Bearer {token}"}
    
    since_time = datetime.now() - timedelta(hours=lookback_hours)
    refreshes = []
    
    try:
        response = requests.get(url, headers=headers)
        data = handle_api_response(response, f"get refresh history for dataset {dataset_id}")
        
        for refresh in data.get('value', []):
            start_time = parse_iso(refresh.get('startTime'))
            if start_time and start_time >= since_time:
                refreshes.append(refresh)
                
        return refreshes
    except FabricAPIException:
        return []


def get_dataset_metadata(workspace_id: str, dataset_id: str, token: str) -> Optional[Dict]:
    """Get metadata for a specific dataset"""
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{dataset_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        data = handle_api_response(response, f"get metadata for dataset {dataset_id}")
        return data
    except FabricAPIException:
        return None


def get_capacity_utilization(capacity_id: str, token: str, lookback_hours: int = 24) -> List[Dict]:
    """Get capacity utilization metrics within lookback period"""
    url = f"https://api.fabric.microsoft.com/v1/capacities/{capacity_id}/workloads"
    headers = {"Authorization": f"Bearer {token}"}
    
    since_time = datetime.now() - timedelta(hours=lookback_hours)
    metrics = []
    
    try:
        response = requests.get(url, headers=headers)
        data = handle_api_response(response, f"get capacity utilization for {capacity_id}")
        
        for metric in data.get('value', []):
            timestamp = parse_iso(metric.get('timestamp'))
            if timestamp and timestamp >= since_time:
                metrics.append(metric)
                
        return metrics
    except FabricAPIException:
        return []


def get_user_activity(workspace_id: str, token: str, lookback_hours: int = 24) -> List[Dict]:
    """Get user activity logs within lookback period (requires admin permissions)"""
    url = f"https://api.fabric.microsoft.com/v1/admin/workspaces/{workspace_id}/activities"
    headers = {"Authorization": f"Bearer {token}"}
    
    since_time = datetime.now() - timedelta(hours=lookback_hours)
    activities = []
    
    try:
        response = requests.get(url, headers=headers)
        data = handle_api_response(response, f"get user activity for workspace {workspace_id}")
        
        for activity in data.get('value', []):
            timestamp = parse_iso(activity.get('CreationTime'))
            if timestamp and timestamp >= since_time:
                activities.append(activity)
                
        return activities
    except FabricAPIException as e:
        if "403" in str(e):
            print(f"[Warning] User activity requires admin permissions: {e}")
        return []


# === Data Mapper Functions ===

def map_pipeline_run(workspace_id: str, pipeline_id: str, pipeline_name: str, run: Dict) -> Dict:
    """Map pipeline run data to Log Analytics schema"""
    start_time = run.get('startTimeUtc')
    end_time = run.get('endTimeUtc')
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
        "PipelineId": pipeline_id,
        "PipelineName": pipeline_name,
        "RunId": run.get('id'),
        "Status": run.get('status'),
        "StartTime": start_time,
        "EndTime": end_time,
        "DurationMs": duration_ms,
        "InvokeType": run.get('invokeType'),
        "JobType": run.get('jobType'),
        "RootActivityRunId": run.get('rootActivityRunId')
    }


def map_activity_run(workspace_id: str, pipeline_id: str, pipeline_run_id: str, activity: Dict) -> Dict:
    """Map activity run data to Log Analytics schema with performance metrics"""
    start_time = activity.get('startTimeUtc') or activity.get('activityRunStart') or activity.get('ActivityRunStart')
    end_time = activity.get('endTimeUtc') or activity.get('activityRunEnd') or activity.get('ActivityRunEnd')
    duration_ms = activity.get('durationInMs') or activity.get('DurationInMs')
    
    if start_time and end_time and not duration_ms:
        try:
            start_dt = parse_iso(start_time)
            end_dt = parse_iso(end_time)
            if start_dt and end_dt:
                duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
        except:
            pass
    
    # Extract performance metrics if available
    rows_read = None
    rows_written = None
    
    # Try to get performance metrics from activity output
    output = activity.get("output") or {}
    if isinstance(output, dict):
        # Check for common performance metric fields
        rows_read = output.get("rowsRead") or output.get("dataRead") or output.get("recordsRead")
        rows_written = output.get("rowsWritten") or output.get("dataWritten") or output.get("recordsWritten")
    
    return {
        "TimeGenerated": end_time or start_time or iso_now(),
        "WorkspaceId": workspace_id,
        "PipelineId": pipeline_id,
        "PipelineName": pipeline_id,  # Add pipeline name field for compatibility
        "ActivityName": activity.get("activityName") or activity.get("ActivityName"),
        "ActivityType": activity.get("activityType") or activity.get("ActivityType"),
        "RunId": pipeline_run_id,
        "Status": activity.get("status") or activity.get("Status"),
        "StartTimeUtc": start_time,
        "EndTimeUtc": end_time,
        "DurationMs": duration_ms,
        "RowsRead": rows_read,
        "RowsWritten": rows_written,
        "ErrorCode": (
            (activity.get("error") or {}).get("code")
            if isinstance(activity.get("error"), dict)
            else None
        ),
        "ErrorMessage": (
            (activity.get("error") or {}).get("message")
            if isinstance(activity.get("error"), dict)
            else None
        ),
    }


def map_dataflow_run(workspace_id: str, dataflow_id: str, dataflow_name: str, run: Dict) -> Dict:
    """Map dataflow run data to Log Analytics schema"""
    start_time = run.get('startTimeUtc')
    end_time = run.get('endTimeUtc')
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
        "DataflowId": dataflow_id,
        "DataflowName": dataflow_name,
        "RunId": run.get('id'),
        "Status": run.get('status'),
        "StartTime": start_time,
        "EndTime": end_time,
        "DurationMs": duration_ms,
        "InvokeType": run.get('invokeType'),
        "JobType": run.get('jobType')
    }


def map_dataset_refresh(workspace_id: str, dataset_id: str, dataset_name: str, refresh: Dict) -> Dict:
    """Map dataset refresh data to Log Analytics schema"""
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


def map_dataset_metadata(workspace_id: str, dataset: Dict) -> Dict:
    """Map dataset metadata to Log Analytics schema"""
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


def map_capacity_metric(capacity_id: str, metric: Dict) -> Dict:
    """Map capacity utilization metric to Log Analytics schema"""
    return {
        "TimeGenerated": metric.get('timestamp') or iso_now(),
        "CapacityId": capacity_id,
        "WorkloadType": metric.get('workloadType'),
        "CpuPercentage": metric.get('cpuPercentage'),
        "MemoryPercentage": metric.get('memoryPercentage'),
        "ActiveRequests": metric.get('activeRequests'),
        "QueuedRequests": metric.get('queuedRequests'),
        "Timestamp": metric.get('timestamp')
    }


def map_user_activity(workspace_id: str, activity: Dict) -> Dict:
    """Map user activity to Log Analytics schema"""
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


# === Collector Classes ===

class PipelineDataCollector:
    """Collector for pipeline and dataflow execution data"""
    
    def __init__(self, workspace_id: str, lookback_hours: int = 24):
        self.workspace_id = workspace_id
        self.lookback_hours = lookback_hours
        self.token = get_fabric_token()
    
    def collect_pipeline_runs(self) -> Iterator[Dict]:
        """Collect pipeline run data"""
        # Get all pipelines in workspace
        url = f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/items"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"type": "DataPipeline"}
        
        response = requests.get(url, headers=headers, params=params)
        data = handle_api_response(response, f"list pipelines in workspace {self.workspace_id}")
        
        for pipeline in data.get('value', []):
            pipeline_id = pipeline['id']
            pipeline_name = pipeline['displayName']
            
            # Get job instances for this pipeline
            instances = list_item_job_instances(
                self.workspace_id, pipeline_id, "pipeline", self.token, self.lookback_hours
            )
            
            for instance in instances:
                yield map_pipeline_run(self.workspace_id, pipeline_id, pipeline_name, instance)
    
    def collect_dataflow_runs(self) -> Iterator[Dict]:
        """Collect dataflow run data"""
        # Get all dataflows in workspace
        url = f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/items"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"type": "Dataflow"}
        
        response = requests.get(url, headers=headers, params=params)
        data = handle_api_response(response, f"list dataflows in workspace {self.workspace_id}")
        
        for dataflow in data.get('value', []):
            dataflow_id = dataflow['id']
            dataflow_name = dataflow['displayName']
            
            # Get job instances for this dataflow
            instances = list_item_job_instances(
                self.workspace_id, dataflow_id, "dataflow", self.token, self.lookback_hours
            )
            
            for instance in instances:
                yield map_dataflow_run(self.workspace_id, dataflow_id, dataflow_name, instance)
    
    def collect_activity_runs(self, pipeline_id: str, run_id: str) -> Iterator[Dict]:
        """Collect activity run data for a specific pipeline run"""
        activities = query_pipeline_activity_runs(
            self.workspace_id, pipeline_id, run_id, self.token
        )
        
        for activity in activities:
            yield map_activity_run(self.workspace_id, pipeline_id, run_id, activity)


class DatasetRefreshCollector:
    """Collector for dataset refresh monitoring"""
    
    def __init__(self, workspace_id: str, lookback_hours: int = 24):
        self.workspace_id = workspace_id
        self.lookback_hours = lookback_hours
        self.token = get_fabric_token()
    
    def collect_dataset_refreshes(self) -> Iterator[Dict]:
        """Collect dataset refresh data"""
        datasets = list_workspace_datasets(self.workspace_id, self.token)
        
        for dataset in datasets:
            dataset_id = dataset['id']
            dataset_name = dataset['displayName']
            
            # Get refresh history
            refreshes = get_dataset_refresh_history(
                self.workspace_id, dataset_id, self.token, self.lookback_hours
            )
            
            for refresh in refreshes:
                yield map_dataset_refresh(self.workspace_id, dataset_id, dataset_name, refresh)
    
    def collect_dataset_metadata(self) -> Iterator[Dict]:
        """Collect dataset metadata"""
        datasets = list_workspace_datasets(self.workspace_id, self.token)
        
        for dataset in datasets:
            yield map_dataset_metadata(self.workspace_id, dataset)


class CapacityUtilizationCollector:
    """Collector for capacity utilization monitoring"""
    
    def __init__(self, capacity_id: str, lookback_hours: int = 24):
        self.capacity_id = capacity_id
        self.lookback_hours = lookback_hours
        self.token = get_fabric_token()
    
    def collect_capacity_metrics(self) -> Iterator[Dict]:
        """Collect capacity utilization metrics"""
        metrics = get_capacity_utilization(self.capacity_id, self.token, self.lookback_hours)
        
        for metric in metrics:
            yield map_capacity_metric(self.capacity_id, metric)


class UserActivityCollector:
    """Collector for user activity monitoring (requires admin permissions)"""
    
    def __init__(self, workspace_id: str, lookback_hours: int = 24):
        self.workspace_id = workspace_id
        self.lookback_hours = lookback_hours
        self.token = get_fabric_token()
    
    def collect_user_activities(self) -> Iterator[Dict]:
        """Collect user activity data"""
        activities = get_user_activity(self.workspace_id, self.token, self.lookback_hours)
        
        for activity in activities:
            yield map_user_activity(self.workspace_id, activity)
