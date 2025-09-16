"""
Data collection modules for Microsoft Fabric workloads.
Implements collectors for pipelines, datasets, capacity utilization, and user activity etc.
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
    data_read = None
    data_written = None
    records_processed = None
    execution_statistics = None
    
    # Try to get performance metrics from activity output
    output = activity.get("output") or {}
    if isinstance(output, dict):
        # Check for common performance metric fields
        data_read = (
            output.get("dataRead") or 
            output.get("rowsRead") or 
            output.get("recordsRead") or
            output.get("bytesRead")
        )
        data_written = (
            output.get("dataWritten") or 
            output.get("rowsWritten") or 
            output.get("recordsWritten") or
            output.get("bytesWritten")
        )
        records_processed = (
            output.get("recordsProcessed") or 
            output.get("rowsProcessed") or
            output.get("itemsProcessed")
        )
        
        # Capture full execution statistics if available
        if output:
            execution_statistics = output
    
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
        "DataRead": data_read,
        "DataWritten": data_written,
        "RecordsProcessed": records_processed,
        "ExecutionStatistics": execution_statistics,
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


class OneLakeStorageCollector:
    """Collector for OneLake storage usage and lakehouse/warehouse data"""
    
    def __init__(self, workspace_id: str, token: Optional[str] = None):
        self.workspace_id = workspace_id
        self.token = token or get_fabric_token()
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def collect_lakehouse_storage(self) -> Iterator[Dict]:
        """Collect lakehouse storage information and usage patterns"""
        try:
            # Get all lakehouse items
            url = f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/items"
            params = {'type': 'Lakehouse'}
            
            response = requests.get(url, headers=self.headers, params=params)
            items_data = handle_api_response(response, f"Lakehouse items for workspace {self.workspace_id}")
            
            for item in items_data.get('value', []):
                # Get detailed lakehouse information
                detail_url = f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/lakehouses/{item['id']}"
                detail_response = requests.get(detail_url, headers=self.headers)
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    
                    # Get tables information
                    tables_url = f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/lakehouses/{item['id']}/tables"
                    tables_response = requests.get(tables_url, headers=self.headers)
                    tables_data = tables_response.json() if tables_response.status_code == 200 else {"value": []}
                    
                    yield {
                        "TimeGenerated": iso_now(),
                        "WorkspaceId": self.workspace_id,
                        "LakehouseId": item['id'],
                        "LakehouseName": item['displayName'],
                        "ItemType": item['type'],
                        "CreatedDate": detail_data.get('properties', {}).get('createdDate'),
                        "LastUpdated": detail_data.get('properties', {}).get('lastUpdatedTime'),
                        "TableCount": len(tables_data.get('value', [])),
                        "OneLakePath": f"abfss://{self.workspace_id}@onelake.dfs.fabric.microsoft.com/{item['id']}.lakehouse",
                        "SqlEndpointId": detail_data.get('properties', {}).get('sqlEndpointProperties', {}).get('id'),
                        "Description": item.get('description', '')
                    }
                else:
                    print(f"⚠️ Failed to get details for lakehouse {item['id']}: {detail_response.status_code}")
                    
        except Exception as e:
            print(f"❌ Error collecting lakehouse storage info: {str(e)}")
    
    def collect_warehouse_storage(self) -> Iterator[Dict]:
        """Collect warehouse storage information and usage patterns"""
        try:
            # Get all warehouse items
            url = f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/items"
            params = {'type': 'Warehouse'}
            
            response = requests.get(url, headers=self.headers, params=params)
            items_data = handle_api_response(response, f"Warehouse items for workspace {self.workspace_id}")
            
            for item in items_data.get('value', []):
                # Get detailed warehouse information
                detail_url = f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/warehouses/{item['id']}"
                detail_response = requests.get(detail_url, headers=self.headers)
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    
                    yield {
                        "TimeGenerated": iso_now(),
                        "WorkspaceId": self.workspace_id,
                        "WarehouseId": item['id'],
                        "WarehouseName": item['displayName'],
                        "ItemType": item['type'],
                        "CreatedDate": detail_data.get('properties', {}).get('createdDate'),
                        "LastUpdated": detail_data.get('properties', {}).get('lastUpdatedTime'),
                        "ConnectionString": detail_data.get('properties', {}).get('connectionInfo', {}).get('connectionString'),
                        "Description": item.get('description', '')
                    }
                else:
                    print(f"⚠️ Failed to get details for warehouse {item['id']}: {detail_response.status_code}")
                    
        except Exception as e:
            print(f"❌ Error collecting warehouse storage info: {str(e)}")


class SparkJobCollector:
    """Collector for Spark job definitions and execution monitoring"""
    
    def __init__(self, workspace_id: str, lookback_hours: int = 24, token: Optional[str] = None):
        self.workspace_id = workspace_id
        self.lookback_hours = lookback_hours
        self.token = token or get_fabric_token()
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def collect_spark_job_definitions(self) -> Iterator[Dict]:
        """Collect Spark job definitions"""
        try:
            url = f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/items"
            params = {'type': 'SparkJobDefinition'}
            
            response = requests.get(url, headers=self.headers, params=params)
            items_data = handle_api_response(response, f"Spark job definitions for workspace {self.workspace_id}")
            
            for item in items_data.get('value', []):
                # Get detailed job definition information
                detail_url = f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/items/{item['id']}"
                detail_response = requests.get(detail_url, headers=self.headers)
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    definition = detail_data.get('definition', {})
                    
                    yield {
                        "TimeGenerated": iso_now(),
                        "WorkspaceId": self.workspace_id,
                        "JobDefinitionId": item['id'],
                        "JobDefinitionName": item['displayName'],
                        "ItemType": item['type'],
                        "CreatedDate": item.get('createdDate'),
                        "LastModified": item.get('lastModifiedDateTime'),
                        "Language": definition.get('language'),
                        "MainClass": definition.get('mainClass'),
                        "MainFile": definition.get('mainFile'),
                        "Arguments": definition.get('arguments', []),
                        "Libraries": definition.get('libraries', []),
                        "Description": item.get('description', '')
                    }
                    
        except Exception as e:
            print(f"❌ Error collecting Spark job definitions: {str(e)}")
    
    def collect_spark_job_runs(self) -> Iterator[Dict]:
        """Collect Spark job execution runs within lookback period"""
        try:
            # Get all Spark job definitions first
            url = f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/items"
            params = {'type': 'SparkJobDefinition'}
            
            response = requests.get(url, headers=self.headers, params=params)
            items_data = handle_api_response(response, f"Spark job definitions for workspace {self.workspace_id}")
            
            since_time = datetime.now() - timedelta(hours=self.lookback_hours)
            
            for item in items_data.get('value', []):
                job_id = item['id']
                job_name = item['displayName']
                
                # Get job instances for this Spark job
                instances = list_item_job_instances(
                    self.workspace_id, job_id, "SparkJobDefinition", self.token, self.lookback_hours
                )
                
                for instance in instances:
                    start_time = parse_iso(instance.get('startTimeUtc'))
                    end_time = parse_iso(instance.get('endTimeUtc'))
                    
                    # Calculate duration
                    duration_ms = None
                    if start_time and end_time:
                        duration_ms = int((end_time - start_time).total_seconds() * 1000)
                    
                    yield {
                        "TimeGenerated": end_time or start_time or iso_now(),
                        "WorkspaceId": self.workspace_id,
                        "JobDefinitionId": job_id,
                        "JobDefinitionName": job_name,
                        "RunId": instance.get('id'),
                        "Status": instance.get('status'),
                        "StartTimeUtc": instance.get('startTimeUtc'),
                        "EndTimeUtc": instance.get('endTimeUtc'),
                        "DurationMs": duration_ms,
                        "JobType": instance.get('jobType'),
                        "ItemType": "SparkJobRun"
                    }
                    
        except Exception as e:
            print(f"❌ Error collecting Spark job runs: {str(e)}")


class NotebookCollector:
    """Collector for notebook inventory and execution monitoring"""
    
    def __init__(self, workspace_id: str, lookback_hours: int = 24, token: Optional[str] = None):
        self.workspace_id = workspace_id
        self.lookback_hours = lookback_hours
        self.token = token or get_fabric_token()
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def collect_notebooks(self) -> Iterator[Dict]:
        """Collect notebook inventory"""
        try:
            url = f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/items"
            params = {'type': 'Notebook'}
            
            response = requests.get(url, headers=self.headers, params=params)
            items_data = handle_api_response(response, f"Notebooks for workspace {self.workspace_id}")
            
            for item in items_data.get('value', []):
                yield {
                    "TimeGenerated": iso_now(),
                    "WorkspaceId": self.workspace_id,
                    "NotebookId": item['id'],
                    "NotebookName": item['displayName'],
                    "ItemType": item['type'],
                    "CreatedDate": item.get('createdDate'),
                    "LastModified": item.get('lastModifiedDateTime'),
                    "Description": item.get('description', '')
                }
                
        except Exception as e:
            print(f"❌ Error collecting notebook inventory: {str(e)}")
    
    def collect_notebook_runs(self) -> Iterator[Dict]:
        """Collect notebook execution runs within lookback period"""
        try:
            # Get all notebooks first
            url = f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/items"
            params = {'type': 'Notebook'}
            
            response = requests.get(url, headers=self.headers, params=params)
            items_data = handle_api_response(response, f"Notebooks for workspace {self.workspace_id}")
            
            for item in items_data.get('value', []):
                notebook_id = item['id']
                notebook_name = item['displayName']
                
                # Get job instances for this notebook
                instances = list_item_job_instances(
                    self.workspace_id, notebook_id, "Notebook", self.token, self.lookback_hours
                )
                
                for instance in instances:
                    start_time = parse_iso(instance.get('startTimeUtc'))
                    end_time = parse_iso(instance.get('endTimeUtc'))
                    
                    # Calculate duration
                    duration_ms = None
                    if start_time and end_time:
                        duration_ms = int((end_time - start_time).total_seconds() * 1000)
                    
                    yield {
                        "TimeGenerated": end_time or start_time or iso_now(),
                        "WorkspaceId": self.workspace_id,
                        "NotebookId": notebook_id,
                        "NotebookName": notebook_name,
                        "RunId": instance.get('id'),
                        "Status": instance.get('status'),
                        "StartTimeUtc": instance.get('startTimeUtc'),
                        "EndTimeUtc": instance.get('endTimeUtc'),
                        "DurationMs": duration_ms,
                        "ItemType": "NotebookRun"
                    }
                    
        except Exception as e:
            print(f"❌ Error collecting notebook runs: {str(e)}")


class GitIntegrationCollector:
    """Collector for Git integration and DevOps visibility"""
    
    def __init__(self, workspace_id: str, token: Optional[str] = None):
        self.workspace_id = workspace_id
        self.token = token or get_fabric_token()
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def collect_git_connection_info(self) -> Iterator[Dict]:
        """Collect Git connection information for the workspace"""
        try:
            url = f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/git/connection"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                connection_data = response.json()
                
                yield {
                    "TimeGenerated": iso_now(),
                    "WorkspaceId": self.workspace_id,
                    "GitProvider": connection_data.get('gitProviderDetails', {}).get('gitProviderType'),
                    "OrganizationName": connection_data.get('gitProviderDetails', {}).get('organizationName'),
                    "ProjectName": connection_data.get('gitProviderDetails', {}).get('projectName'),
                    "RepositoryName": connection_data.get('gitProviderDetails', {}).get('repositoryName'),
                    "BranchName": connection_data.get('gitProviderDetails', {}).get('branchName'),
                    "DirectoryName": connection_data.get('gitProviderDetails', {}).get('directoryName'),
                    "ConnectionId": connection_data.get('connectionId'),
                    "ItemType": "GitConnection"
                }
            elif response.status_code == 404:
                # No Git connection configured
                yield {
                    "TimeGenerated": iso_now(),
                    "WorkspaceId": self.workspace_id,
                    "GitProvider": None,
                    "ConnectionStatus": "Not Connected",
                    "ItemType": "GitConnection"
                }
            else:
                print(f"⚠️ Failed to get Git connection info: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error collecting Git connection info: {str(e)}")
    
    def collect_git_status(self) -> Iterator[Dict]:
        """Collect Git status for workspace items"""
        try:
            url = f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/git/status"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                status_data = response.json()
                
                # Process changes (modified items)
                for change in status_data.get('changes', []):
                    yield {
                        "TimeGenerated": iso_now(),
                        "WorkspaceId": self.workspace_id,
                        "ItemId": change.get('itemId'),
                        "ItemDisplayName": change.get('itemDisplayName'),
                        "ItemType": change.get('itemType'),
                        "ChangeType": change.get('changeType'),
                        "ConflictType": change.get('conflictType'),
                        "StatusType": "WorkspaceChange"
                    }
                
                # Process remote changes (items changed in Git)
                for remote_change in status_data.get('remoteChanges', []):
                    yield {
                        "TimeGenerated": iso_now(),
                        "WorkspaceId": self.workspace_id,
                        "ItemId": remote_change.get('itemId'),
                        "ItemDisplayName": remote_change.get('itemDisplayName'),
                        "ItemType": remote_change.get('itemType'),
                        "ChangeType": remote_change.get('changeType'),
                        "ConflictType": remote_change.get('conflictType'),
                        "StatusType": "RemoteChange"
                    }
                    
            elif response.status_code == 404:
                # No Git connection configured
                pass
            else:
                print(f"⚠️ Failed to get Git status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error collecting Git status: {str(e)}")


class AccessPermissionsCollector:
    """Collector for Access & Permissions APIs - Security compliance monitoring"""
    
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.base_url = "https://api.fabric.microsoft.com/v1"
    
    def collect_workspace_permissions(self) -> Iterator[Dict[str, Any]]:
        """Collect workspace permissions and role assignments"""
        try:
            token = get_fabric_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Get workspace role assignments
            url = f"{self.base_url}/workspaces/{self.workspace_id}/roleAssignments"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                for assignment in data.get('value', []):
                    yield {
                        "TimeGenerated": iso_now(),
                        "WorkspaceId": self.workspace_id,
                        "PrincipalId": assignment.get('principal', {}).get('id'),
                        "PrincipalType": assignment.get('principal', {}).get('type'),
                        "PrincipalDisplayName": assignment.get('principal', {}).get('displayName'),
                        "Role": assignment.get('role'),
                        "AssignmentType": "WorkspaceRole"
                    }
            else:
                print(f"⚠️ Failed to get workspace role assignments: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error collecting workspace permissions: {str(e)}")
    
    def collect_item_permissions(self) -> Iterator[Dict[str, Any]]:
        """Collect item-level permissions for datasets, reports, etc."""
        try:
            token = get_fabric_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Get workspace items first
            items_url = f"{self.base_url}/workspaces/{self.workspace_id}/items"
            items_response = requests.get(items_url, headers=headers)
            
            if items_response.status_code == 200:
                items_data = items_response.json()
                
                for item in items_data.get('value', []):
                    item_id = item.get('id')
                    item_type = item.get('type')
                    
                    # Get permissions for specific item types that support permissions
                    if item_type in ['Dataset', 'Report', 'Dashboard']:
                        permissions_url = f"{self.base_url}/workspaces/{self.workspace_id}/{item_type.lower()}s/{item_id}/users"
                        perm_response = requests.get(permissions_url, headers=headers)
                        
                        if perm_response.status_code == 200:
                            perm_data = perm_response.json()
                            for permission in perm_data.get('value', []):
                                yield {
                                    "TimeGenerated": iso_now(),
                                    "WorkspaceId": self.workspace_id,
                                    "ItemId": item_id,
                                    "ItemName": item.get('displayName'),
                                    "ItemType": item_type,
                                    "PrincipalId": permission.get('identifier'),
                                    "PrincipalType": permission.get('principalType'),
                                    "AccessRight": permission.get('datasetUserAccessRight', permission.get('reportUserAccessRight')),
                                    "AssignmentType": "ItemPermission"
                                }
                                
        except Exception as e:
            print(f"❌ Error collecting item permissions: {str(e)}")
    
    def collect_capacity_permissions(self, capacity_id: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """Collect capacity-level permissions and assignments"""
        try:
            if not capacity_id:
                return
                
            token = get_fabric_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Get capacity assignments
            url = f"{self.base_url}/capacities/{capacity_id}/roleAssignments"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                for assignment in data.get('value', []):
                    yield {
                        "TimeGenerated": iso_now(),
                        "WorkspaceId": self.workspace_id,
                        "CapacityId": capacity_id,
                        "PrincipalId": assignment.get('principal', {}).get('id'),
                        "PrincipalType": assignment.get('principal', {}).get('type'),
                        "PrincipalDisplayName": assignment.get('principal', {}).get('displayName'),
                        "Role": assignment.get('role'),
                        "AssignmentType": "CapacityRole"
                    }
            else:
                print(f"⚠️ Failed to get capacity role assignments: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error collecting capacity permissions: {str(e)}")


class DataLineageCollector:
    """Collector for Data Lineage APIs - Regulatory compliance tracking"""
    
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.base_url = "https://api.fabric.microsoft.com/v1"
    
    def collect_dataset_lineage(self) -> Iterator[Dict[str, Any]]:
        """Collect dataset lineage and data flow tracking"""
        try:
            token = get_fabric_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Get datasets in workspace
            datasets_url = f"{self.base_url}/workspaces/{self.workspace_id}/items?type=Dataset"
            datasets_response = requests.get(datasets_url, headers=headers)
            
            if datasets_response.status_code == 200:
                datasets_data = datasets_response.json()
                
                for dataset in datasets_data.get('value', []):
                    dataset_id = dataset.get('id')
                    
                    # Get dataset dependencies
                    deps_url = f"{self.base_url}/workspaces/{self.workspace_id}/datasets/{dataset_id}/dependencies"
                    deps_response = requests.get(deps_url, headers=headers)
                    
                    if deps_response.status_code == 200:
                        deps_data = deps_response.json()
                        for dependency in deps_data.get('value', []):
                            yield {
                                "TimeGenerated": iso_now(),
                                "WorkspaceId": self.workspace_id,
                                "SourceDatasetId": dataset_id,
                                "SourceDatasetName": dataset.get('displayName'),
                                "TargetDatasetId": dependency.get('datasourceId'),
                                "TargetDatasetName": dependency.get('datasourceName'),
                                "DependencyType": dependency.get('datasourceType'),
                                "LineageType": "DatasetDependency"
                            }
                    
                    # Get dataset data sources
                    sources_url = f"{self.base_url}/workspaces/{self.workspace_id}/datasets/{dataset_id}/datasources"
                    sources_response = requests.get(sources_url, headers=headers)
                    
                    if sources_response.status_code == 200:
                        sources_data = sources_response.json()
                        for source in sources_data.get('value', []):
                            yield {
                                "TimeGenerated": iso_now(),
                                "WorkspaceId": self.workspace_id,
                                "DatasetId": dataset_id,
                                "DatasetName": dataset.get('displayName'),
                                "DatasourceId": source.get('datasourceId'),
                                "DatasourceType": source.get('datasourceType'),
                                "ConnectionDetails": source.get('connectionDetails', {}),
                                "LineageType": "DataSource"
                            }
                            
        except Exception as e:
            print(f"❌ Error collecting dataset lineage: {str(e)}")
    
    def collect_dataflow_lineage(self) -> Iterator[Dict[str, Any]]:
        """Collect dataflow transformation lineage"""
        try:
            token = get_fabric_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Get dataflows in workspace
            dataflows_url = f"{self.base_url}/workspaces/{self.workspace_id}/items?type=Dataflow"
            dataflows_response = requests.get(dataflows_url, headers=headers)
            
            if dataflows_response.status_code == 200:
                dataflows_data = dataflows_response.json()
                
                for dataflow in dataflows_data.get('value', []):
                    dataflow_id = dataflow.get('id')
                    
                    # Get dataflow data sources
                    sources_url = f"{self.base_url}/workspaces/{self.workspace_id}/dataflows/{dataflow_id}/datasources"
                    sources_response = requests.get(sources_url, headers=headers)
                    
                    if sources_response.status_code == 200:
                        sources_data = sources_response.json()
                        for source in sources_data.get('value', []):
                            yield {
                                "TimeGenerated": iso_now(),
                                "WorkspaceId": self.workspace_id,
                                "DataflowId": dataflow_id,
                                "DataflowName": dataflow.get('displayName'),
                                "DatasourceId": source.get('datasourceId'),
                                "DatasourceType": source.get('datasourceType'),
                                "ConnectionDetails": source.get('connectionDetails', {}),
                                "LineageType": "DataflowSource"
                            }
                            
        except Exception as e:
            print(f"❌ Error collecting dataflow lineage: {str(e)}")


class SemanticModelCollector:
    """Collector for Semantic Model Performance - BI optimization monitoring"""
    
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.base_url = "https://api.fabric.microsoft.com/v1"
    
    def collect_model_refresh_performance(self) -> Iterator[Dict[str, Any]]:
        """Collect semantic model refresh performance metrics"""
        try:
            token = get_fabric_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Get datasets (semantic models) in workspace
            datasets_url = f"{self.base_url}/workspaces/{self.workspace_id}/items?type=Dataset"
            datasets_response = requests.get(datasets_url, headers=headers)
            
            if datasets_response.status_code == 200:
                datasets_data = datasets_response.json()
                
                for dataset in datasets_data.get('value', []):
                    dataset_id = dataset.get('id')
                    
                    # Get refresh history
                    refresh_url = f"{self.base_url}/workspaces/{self.workspace_id}/datasets/{dataset_id}/refreshes"
                    refresh_response = requests.get(refresh_url, headers=headers)
                    
                    if refresh_response.status_code == 200:
                        refresh_data = refresh_response.json()
                        for refresh in refresh_data.get('value', []):
                            start_time = parse_iso(refresh.get('startTime')) if refresh.get('startTime') else None
                            end_time = parse_iso(refresh.get('endTime')) if refresh.get('endTime') else None
                            duration = None
                            
                            if start_time and end_time:
                                duration = (end_time - start_time).total_seconds()
                            
                            yield {
                                "TimeGenerated": iso_now(),
                                "WorkspaceId": self.workspace_id,
                                "DatasetId": dataset_id,
                                "DatasetName": dataset.get('displayName'),
                                "RefreshId": refresh.get('requestId'),
                                "RefreshType": refresh.get('refreshType'),
                                "Status": refresh.get('status'),
                                "StartTime": refresh.get('startTime'),
                                "EndTime": refresh.get('endTime'),
                                "DurationSeconds": duration,
                                "ServiceExceptionJson": refresh.get('serviceExceptionJson'),
                                "MetricType": "RefreshPerformance"
                            }
                            
        except Exception as e:
            print(f"❌ Error collecting model refresh performance: {str(e)}")
    
    def collect_model_usage_patterns(self) -> Iterator[Dict[str, Any]]:
        """Collect semantic model query patterns and usage"""
        try:
            token = get_fabric_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Get datasets in workspace
            datasets_url = f"{self.base_url}/workspaces/{self.workspace_id}/items?type=Dataset"
            datasets_response = requests.get(datasets_url, headers=headers)
            
            if datasets_response.status_code == 200:
                datasets_data = datasets_response.json()
                
                for dataset in datasets_data.get('value', []):
                    dataset_id = dataset.get('id')
                    
                    # Get dataset users (who has access)
                    users_url = f"{self.base_url}/workspaces/{self.workspace_id}/datasets/{dataset_id}/users"
                    users_response = requests.get(users_url, headers=headers)
                    
                    if users_response.status_code == 200:
                        users_data = users_response.json()
                        user_count = len(users_data.get('value', []))
                        
                        yield {
                            "TimeGenerated": iso_now(),
                            "WorkspaceId": self.workspace_id,
                            "DatasetId": dataset_id,
                            "DatasetName": dataset.get('displayName'),
                            "UserCount": user_count,
                            "IsDirectQuery": dataset.get('isDirectQuery', False),
                            "MetricType": "ModelUsage"
                        }
                        
        except Exception as e:
            print(f"❌ Error collecting model usage patterns: {str(e)}")


class RealTimeIntelligenceCollector:
    """Collector for Real-Time Intelligence APIs - Streaming analytics monitoring"""
    
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.base_url = "https://api.fabric.microsoft.com/v1"
    
    def collect_eventstream_metrics(self) -> Iterator[Dict[str, Any]]:
        """Collect Eventstream monitoring and performance metrics"""
        try:
            token = get_fabric_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Get Eventstreams in workspace
            eventstreams_url = f"{self.base_url}/workspaces/{self.workspace_id}/items?type=Eventstream"
            eventstreams_response = requests.get(eventstreams_url, headers=headers)
            
            if eventstreams_response.status_code == 200:
                eventstreams_data = eventstreams_response.json()
                
                for eventstream in eventstreams_data.get('value', []):
                    eventstream_id = eventstream.get('id')
                    
                    yield {
                        "TimeGenerated": iso_now(),
                        "WorkspaceId": self.workspace_id,
                        "EventstreamId": eventstream_id,
                        "EventstreamName": eventstream.get('displayName'),
                        "Description": eventstream.get('description'),
                        "CreatedDate": eventstream.get('createdDate'),
                        "LastUpdated": eventstream.get('lastUpdatedTime'),
                        "MetricType": "EventstreamInfo"
                    }
                    
        except Exception as e:
            print(f"❌ Error collecting Eventstream metrics: {str(e)}")
    
    def collect_kql_database_performance(self) -> Iterator[Dict[str, Any]]:
        """Collect KQL Database performance and usage metrics"""
        try:
            token = get_fabric_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Get KQL Databases in workspace
            kql_url = f"{self.base_url}/workspaces/{self.workspace_id}/items?type=KQLDatabase"
            kql_response = requests.get(kql_url, headers=headers)
            
            if kql_response.status_code == 200:
                kql_data = kql_response.json()
                
                for kql_db in kql_data.get('value', []):
                    kql_db_id = kql_db.get('id')
                    
                    yield {
                        "TimeGenerated": iso_now(),
                        "WorkspaceId": self.workspace_id,
                        "KQLDatabaseId": kql_db_id,
                        "KQLDatabaseName": kql_db.get('displayName'),
                        "Description": kql_db.get('description'),
                        "CreatedDate": kql_db.get('createdDate'),
                        "LastUpdated": kql_db.get('lastUpdatedTime'),
                        "MetricType": "KQLDatabaseInfo"
                    }
                    
        except Exception as e:
            print(f"❌ Error collecting KQL Database performance: {str(e)}")


class MirroringCollector:
    """Collector for Mirroring APIs - Hybrid data monitoring"""
    
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.base_url = "https://api.fabric.microsoft.com/v1"
    
    def collect_mirror_status(self) -> Iterator[Dict[str, Any]]:
        """Collect Mirror status and synchronization metrics"""
        try:
            token = get_fabric_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Get Mirrors in workspace
            mirrors_url = f"{self.base_url}/workspaces/{self.workspace_id}/items?type=Mirror"
            mirrors_response = requests.get(mirrors_url, headers=headers)
            
            if mirrors_response.status_code == 200:
                mirrors_data = mirrors_response.json()
                
                for mirror in mirrors_data.get('value', []):
                    mirror_id = mirror.get('id')
                    
                    # Get mirror status
                    status_url = f"{self.base_url}/workspaces/{self.workspace_id}/mirrors/{mirror_id}/status"
                    status_response = requests.get(status_url, headers=headers)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        yield {
                            "TimeGenerated": iso_now(),
                            "WorkspaceId": self.workspace_id,
                            "MirrorId": mirror_id,
                            "MirrorName": mirror.get('displayName'),
                            "Status": status_data.get('status'),
                            "LastSyncTime": status_data.get('lastSyncTime'),
                            "SyncDurationSeconds": status_data.get('syncDurationSeconds'),
                            "SourceConnectionStatus": status_data.get('sourceConnectionStatus'),
                            "MetricType": "MirrorStatus"
                        }
                    else:
                        # Basic mirror info if status not available
                        yield {
                            "TimeGenerated": iso_now(),
                            "WorkspaceId": self.workspace_id,
                            "MirrorId": mirror_id,
                            "MirrorName": mirror.get('displayName'),
                            "Description": mirror.get('description'),
                            "CreatedDate": mirror.get('createdDate'),
                            "LastUpdated": mirror.get('lastUpdatedTime'),
                            "MetricType": "MirrorInfo"
                        }
                        
        except Exception as e:
            print(f"❌ Error collecting Mirror status: {str(e)}")


class MLAICollector:
    """Collector for ML/AI APIs - AI workload governance"""
    
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.base_url = "https://api.fabric.microsoft.com/v1"
    
    def collect_ml_models(self) -> Iterator[Dict[str, Any]]:
        """Collect ML Model monitoring and governance data"""
        try:
            token = get_fabric_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Get ML Models in workspace
            models_url = f"{self.base_url}/workspaces/{self.workspace_id}/items?type=MLModel"
            models_response = requests.get(models_url, headers=headers)
            
            if models_response.status_code == 200:
                models_data = models_response.json()
                
                for model in models_data.get('value', []):
                    model_id = model.get('id')
                    
                    yield {
                        "TimeGenerated": iso_now(),
                        "WorkspaceId": self.workspace_id,
                        "ModelId": model_id,
                        "ModelName": model.get('displayName'),
                        "Description": model.get('description'),
                        "CreatedDate": model.get('createdDate'),
                        "LastUpdated": model.get('lastUpdatedTime'),
                        "MetricType": "MLModelInfo"
                    }
                    
        except Exception as e:
            print(f"❌ Error collecting ML Models: {str(e)}")
    
    def collect_ml_experiments(self) -> Iterator[Dict[str, Any]]:
        """Collect ML Experiment tracking and performance data"""
        try:
            token = get_fabric_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Get ML Experiments in workspace
            experiments_url = f"{self.base_url}/workspaces/{self.workspace_id}/items?type=MLExperiment"
            experiments_response = requests.get(experiments_url, headers=headers)
            
            if experiments_response.status_code == 200:
                experiments_data = experiments_response.json()
                
                for experiment in experiments_data.get('value', []):
                    experiment_id = experiment.get('id')
                    
                    yield {
                        "TimeGenerated": iso_now(),
                        "WorkspaceId": self.workspace_id,
                        "ExperimentId": experiment_id,
                        "ExperimentName": experiment.get('displayName'),
                        "Description": experiment.get('description'),
                        "CreatedDate": experiment.get('createdDate'),
                        "LastUpdated": experiment.get('lastUpdatedTime'),
                        "MetricType": "MLExperimentInfo"
                    }
                    
        except Exception as e:
            print(f"❌ Error collecting ML Experiments: {str(e)}")
