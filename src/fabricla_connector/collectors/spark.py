"""
Spark monitoring collectors for Microsoft Fabric.

Provides collectors and functions for gathering Spark session data, resource usage,
logs, and metrics from Fabric workspaces.
"""
import requests
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Iterator

from fabricla_connector.api import get_fabric_token
from fabricla_connector.utils import parse_iso, iso_now
from fabricla_connector.mappers.spark import (
    LivySessionMapper,
    SparkResourceMapper,
    map_livy_session,
    map_spark_resource_driver,
    map_spark_resource_executor,
    map_spark_resource_aggregate
)


class FabricAPIException(Exception):
    """Custom exception for Fabric API errors"""
    pass


def handle_api_response(response: requests.Response, context: str) -> Any:
    """Handle API response with detailed error handling"""
    if response.status_code == 200:
        return response.json()
    
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        print(f"WARNING: 429 Rate Limited - {context} - waiting {retry_after}s")
        raise FabricAPIException(f"Rate limited: {context}")
    
    if response.status_code in [401, 403]:
        print(f"ERROR: {response.status_code} - Authentication/Permission error for {context}")
        raise FabricAPIException(f"Auth error: {context}")
    
    if response.status_code == 404:
        print(f"INFO: 404 - Resource not found for {context}")
        return None
    
    print(f"ERROR: API Error ({response.status_code}) for {context}")
    raise FabricAPIException(f"API error {response.status_code}: {context}")


# === Livy Session Collection Functions ===

def collect_livy_sessions_workspace(
    workspace_id: str,
    workspace_name: Optional[str] = None,
    lookback_hours: int = 24
) -> Iterator[Dict[str, Any]]:
    """
    Collect Livy sessions at workspace level using the Livy Sessions API.
    
    API: GET /v1/workspaces/{workspaceId}/spark/livySessions
    
    Args:
        workspace_id: Fabric workspace ID
        workspace_name: Optional workspace display name
        lookback_hours: Hours to look back for sessions
        
    Yields:
        Dict containing Livy session data mapped to FabricSparkLivySession_CL schema
    """
    try:
        token = get_fabric_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/spark/livySessions"
        
        response = requests.get(url, headers=headers, timeout=60)
        data = handle_api_response(response, f"Workspace Livy Sessions - {workspace_id}")
        
        if not data or "value" not in data:
            return
            
        sessions = data["value"]
        print(f"Found {len(sessions)} Livy sessions")
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        collected_count = 0
        
        for session in sessions:
            try:
                submitted_time = parse_iso(session.get('submittedDateTime'))
                if submitted_time and submitted_time < cutoff_time:
                    continue
                
                yield LivySessionMapper.map(
                    workspace_id=workspace_id,
                    item_type="Workspace",
                    item_id=workspace_id,
                    item_name=workspace_name or workspace_id,
                    session=session,
                    workspace_name=workspace_name
                )
                collected_count += 1
                
            except Exception as e:
                print(f"WARNING: Error processing session: {str(e)}")
                continue
        
        print(f"Collected {collected_count} sessions")
        
    except FabricAPIException as e:
        print(f"ERROR: {str(e)}")
    except Exception as e:
        print(f"ERROR: {str(e)}")


def collect_livy_sessions_notebook(
    workspace_id: str,
    notebook_id: str,
    notebook_name: str,
    workspace_name: Optional[str] = None,
    lookback_hours: int = 24
) -> Iterator[Dict[str, Any]]:
    """
    Collect Livy sessions for a specific Notebook.
    
    API: GET /v1/workspaces/{workspaceId}/notebooks/{notebookId}/spark/livySessions
    
    Args:
        workspace_id: Fabric workspace ID
        notebook_id: Notebook item ID
        notebook_name: Notebook display name
        workspace_name: Optional workspace display name
        lookback_hours: Hours to look back for sessions
        
    Yields:
        Dict containing Livy session data for the notebook
    """
    try:
        token = get_fabric_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/notebooks/{notebook_id}/spark/livySessions"
        
        response = requests.get(url, headers=headers, timeout=30)
        data = handle_api_response(response, f"Notebook Livy Sessions - {notebook_name}")
        
        if not data or "sessions" not in data:
            return
            
        sessions = data["sessions"]
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        collected_count = 0
        
        for session in sessions:
            try:
                created_time = parse_iso(session.get('createdAt') or session.get('createdTime'))
                if created_time and created_time < cutoff_time:
                    continue
                
                yield LivySessionMapper.map(
                    workspace_id=workspace_id,
                    item_type="Notebook",
                    item_id=notebook_id,
                    item_name=notebook_name,
                    session=session,
                    workspace_name=workspace_name
                )
                collected_count += 1
                
            except Exception as e:
                print(f"WARNING: Error processing notebook session {session.get('id')}: {str(e)}")
                continue
        
        if collected_count > 0:
            print(f"SUCCESS: Collected {collected_count} Livy sessions for notebook '{notebook_name}'")
        
    except FabricAPIException as e:
        if "404" not in str(e):
            print(f"WARNING: Failed to collect notebook Livy sessions for '{notebook_name}': {str(e)}")
    except Exception as e:
        print(f"ERROR: Unexpected error collecting notebook Livy sessions: {str(e)}")


def collect_livy_sessions_sparkjob(
    workspace_id: str,
    sparkjob_id: str,
    sparkjob_name: str,
    workspace_name: Optional[str] = None,
    lookback_hours: int = 24
) -> Iterator[Dict[str, Any]]:
    """
    Collect Livy sessions for a specific Spark Job Definition.
    
    API: GET /v1/workspaces/{workspaceId}/sparkJobDefinitions/{sparkJobId}/spark/livySessions
    
    Args:
        workspace_id: Fabric workspace ID
        sparkjob_id: SparkJobDefinition item ID
        sparkjob_name: SparkJobDefinition display name
        workspace_name: Optional workspace display name
        lookback_hours: Hours to look back for sessions
        
    Yields:
        Dict containing Livy session data for the Spark job
    """
    try:
        token = get_fabric_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/sparkJobDefinitions/{sparkjob_id}/spark/livySessions"
        
        response = requests.get(url, headers=headers, timeout=30)
        data = handle_api_response(response, f"SparkJob Livy Sessions - {sparkjob_name}")
        
        if not data or "sessions" not in data:
            return
            
        sessions = data["sessions"]
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        collected_count = 0
        
        for session in sessions:
            try:
                created_time = parse_iso(session.get('createdAt') or session.get('createdTime'))
                if created_time and created_time < cutoff_time:
                    continue
                
                yield LivySessionMapper.map(
                    workspace_id=workspace_id,
                    item_type="SparkJobDefinition",
                    item_id=sparkjob_id,
                    item_name=sparkjob_name,
                    session=session,
                    workspace_name=workspace_name
                )
                collected_count += 1
                
            except Exception as e:
                print(f"WARNING: Error processing SparkJob session {session.get('id')}: {str(e)}")
                continue
        
        if collected_count > 0:
            print(f"SUCCESS: Collected {collected_count} Livy sessions for SparkJob '{sparkjob_name}'")
        
    except FabricAPIException as e:
        if "404" not in str(e):
            print(f"WARNING: Failed to collect SparkJob Livy sessions for '{sparkjob_name}': {str(e)}")
    except Exception as e:
        print(f"ERROR: Unexpected error collecting SparkJob Livy sessions: {str(e)}")


def collect_livy_sessions_lakehouse(
    workspace_id: str,
    lakehouse_id: str,
    lakehouse_name: str,
    workspace_name: Optional[str] = None,
    lookback_hours: int = 24
) -> Iterator[Dict[str, Any]]:
    """
    Collect Livy sessions for a specific Lakehouse.
    
    API: GET /v1/workspaces/{workspaceId}/lakehouses/{lakehouseId}/spark/livySessions
    
    Args:
        workspace_id: Fabric workspace ID
        lakehouse_id: Lakehouse item ID
        lakehouse_name: Lakehouse display name
        workspace_name: Optional workspace display name
        lookback_hours: Hours to look back for sessions
        
    Yields:
        Dict containing Livy session data for the lakehouse
    """
    try:
        token = get_fabric_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/lakehouses/{lakehouse_id}/spark/livySessions"
        
        response = requests.get(url, headers=headers, timeout=30)
        data = handle_api_response(response, f"Lakehouse Livy Sessions - {lakehouse_name}")
        
        if not data or "sessions" not in data:
            return
            
        sessions = data["sessions"]
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        collected_count = 0
        
        for session in sessions:
            try:
                created_time = parse_iso(session.get('createdAt') or session.get('createdTime'))
                if created_time and created_time < cutoff_time:
                    continue
                
                yield LivySessionMapper.map(
                    workspace_id=workspace_id,
                    item_type="Lakehouse",
                    item_id=lakehouse_id,
                    item_name=lakehouse_name,
                    session=session,
                    workspace_name=workspace_name
                )
                collected_count += 1
                
            except Exception as e:
                print(f"WARNING: Error processing Lakehouse session {session.get('id')}: {str(e)}")
                continue
        
        if collected_count > 0:
            print(f"SUCCESS: Collected {collected_count} Livy sessions for Lakehouse '{lakehouse_name}'")
        
    except FabricAPIException as e:
        if "404" not in str(e):
            print(f"WARNING: Failed to collect Lakehouse Livy sessions for '{lakehouse_name}': {str(e)}")
    except Exception as e:
        print(f"ERROR: Unexpected error collecting Lakehouse Livy sessions: {str(e)}")


# === Resource Usage Collection Functions ===

def collect_spark_resource_usage(
    workspace_id: str,
    application_id: str,
    session_id: str,
    item_type: str,
    item_id: str,
    item_name: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> Iterator[Dict[str, Any]]:
    """
    Collect resource usage metrics for a specific Spark application.
    
    API: GET /v1/workspaces/{workspaceId}/spark/applications/{applicationId}/resource-usage
    
    Args:
        workspace_id: Fabric workspace ID
        application_id: Spark application ID
        session_id: Livy session ID
        item_type: Type of item (Notebook, SparkJobDefinition, etc.)
        item_id: ID of the parent item
        item_name: Display name of the parent item
        start_time: Optional start time for historical metrics (ISO 8601)
        end_time: Optional end time for historical metrics (ISO 8601)
        
    Yields:
        Dict containing resource usage data (driver, executors, aggregates)
    """
    try:
        token = get_fabric_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/spark/applications/{application_id}/resource-usage"
        params = {}
        
        if start_time and end_time:
            params['startTime'] = start_time
            params['endTime'] = end_time
            context_msg = f"Historical resource usage for {application_id} ({start_time} to {end_time})"
        else:
            context_msg = f"Current resource usage for {application_id}"
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        data = handle_api_response(response, context_msg)
        
        if not data:
            return
        
        timestamp = data.get('timestamp') or iso_now()
        
        # Yield driver resource metrics
        driver_data = data.get('driver')
        if driver_data:
            yield SparkResourceMapper.map_driver(
                workspace_id=workspace_id,
                session_id=session_id,
                app_id=application_id,
                item_type=item_type,
                item_id=item_id,
                item_name=item_name,
                driver_data=driver_data,
                timestamp=timestamp
            )
        
        # Yield executor resource metrics
        executors = data.get('executors', [])
        for executor in executors:
            yield SparkResourceMapper.map_executor(
                workspace_id=workspace_id,
                session_id=session_id,
                app_id=application_id,
                item_type=item_type,
                item_id=item_id,
                item_name=item_name,
                executor_data=executor,
                timestamp=timestamp
            )
        
        # Yield aggregate resource metrics
        aggregates = data.get('aggregates')
        if aggregates:
            yield SparkResourceMapper.map_aggregate(
                workspace_id=workspace_id,
                session_id=session_id,
                app_id=application_id,
                item_type=item_type,
                item_id=item_id,
                item_name=item_name,
                aggregate_data=aggregates,
                timestamp=timestamp
            )
        
    except FabricAPIException as e:
        if "404" not in str(e):
            print(f"WARNING: Failed to collect resource usage for {application_id}: {str(e)}")
    except Exception as e:
        print(f"ERROR: Unexpected error collecting resource usage: {str(e)}")


def collect_resource_usage_for_active_sessions(
    workspace_id: str,
    workspace_name: Optional[str] = None,
    lookback_hours: int = 24
) -> Iterator[Dict[str, Any]]:
    """
    Batch collect resource usage for all active Livy sessions in a workspace.
    
    Args:
        workspace_id: Fabric workspace ID
        workspace_name: Optional workspace display name
        lookback_hours: Hours to look back for sessions
        
    Yields:
        Dict containing resource usage data for all active sessions
    """
    try:
        # First, collect all Livy sessions to get session and application IDs
        sessions = list(collect_livy_sessions_workspace(
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            lookback_hours=lookback_hours
        ))
        
        print(f"INFO: Collecting resource usage for {len(sessions)} sessions")
        
        active_states = ['idle', 'busy', 'starting']
        resource_count = 0
        
        for session_data in sessions:
            session_id = session_data.get('SessionId')
            app_id = session_data.get('ApplicationId')
            state = session_data.get('State')
            item_type = session_data.get('ItemType')
            item_id = session_data.get('ItemId')
            item_name = session_data.get('ItemName')
            
            # Only collect resource usage for active sessions with application IDs
            if not app_id or state not in active_states:
                continue
            
            # Collect resource usage for this session
            for resource_metric in collect_spark_resource_usage(
                workspace_id=workspace_id,
                application_id=app_id,
                session_id=session_id,
                item_type=item_type,
                item_id=item_id,
                item_name=item_name
            ):
                yield resource_metric
                resource_count += 1
        
        if resource_count > 0:
            print(f"SUCCESS: Collected {resource_count} resource usage metrics from {len(sessions)} sessions")
        
    except Exception as e:
        print(f"ERROR: collecting batch resource usage: {str(e)}")


# === Spark Application Collection Functions ===

def get_spark_session_details(
    workspace_id: str,
    session_id: str,
    headers: Dict[str, str],
    item_type: Optional[str] = None,
    item_id: Optional[str] = None
) -> Dict[str, Any]:
    """Get detailed information for a specific Spark session"""
    try:
        if item_type and item_id:
            endpoint_map = {
                "notebook": f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/notebooks/{item_id}/spark/sessions/{session_id}",
                "sparkjobdefinition": f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/sparkJobDefinitions/{item_id}/spark/sessions/{session_id}",
                "lakehouse": f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/lakehouses/{item_id}/spark/sessions/{session_id}"
            }
            url = endpoint_map.get(item_type.lower())
        else:
            url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/spark/sessions/{session_id}"
            
        if not url:
            return {}
            
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {}
            
    except Exception as e:
        return {}


def collect_spark_applications_workspace(
    workspace_id: str,
    lookback_hours: int = 24,
    max_items: int = 500
) -> Iterator[Dict[str, Any]]:
    """
    Collect Spark applications from workspace level.
    
    Args:
        workspace_id: Fabric workspace ID
        lookback_hours: Hours to look back for applications
        max_items: Maximum items to retrieve
        
    Yields:
        Dict containing Spark application information
    """
    try:
        token = get_fabric_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/spark/sessions"
        
        print(f"INFO: Collecting Spark applications for workspace {workspace_id}")
        
        response = requests.get(url, headers=headers, timeout=30)
        data = handle_api_response(response, f"Workspace Spark Applications - {workspace_id}")
        
        if not data or "value" not in data:
            print("WARNING: No Spark applications found in workspace")
            return
            
        sessions = data["value"]
        print(f"Found {len(sessions)} Spark sessions")
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        collected_count = 0
        
        for session in sessions:
            if collected_count >= max_items:
                print(f"WARNING: Reached max items limit ({max_items})")
                break
                
            try:
                session_time = parse_iso(session.get('submissionTime', ''))
                if session_time and session_time < cutoff_time:
                    continue
                
                session_id = session.get('id')
                session_details = get_spark_session_details(workspace_id, session_id, headers)
                
                yield {
                    "WorkspaceId": workspace_id,
                    "SessionId": session_id,
                    "ApplicationId": session.get('appId'),
                    "ApplicationName": session.get('name'),
                    "State": session.get('state'),
                    "SubmissionTime": session.get('submissionTime'),
                    "Kind": session.get('kind'),
                    "SparkVersion": session.get('sparkVersion'),
                    "DriverCores": session_details.get('driverCores'),
                    "DriverMemory": session_details.get('driverMemory'),
                    "ExecutorCores": session_details.get('executorCores'),
                    "ExecutorMemory": session_details.get('executorMemory'),
                    "ExecutorCount": session_details.get('numExecutors'),
                    "Tags": json.dumps(session.get('tags', {})),
                    "CollectedAt": iso_now(),
                    "MetricType": "SparkApplication"
                }
                
                collected_count += 1
                
            except Exception as e:
                print(f"WARNING: Error processing session {session.get('id', 'unknown')}: {str(e)}")
                continue
                
        print(f"SUCCESS: Collected {collected_count} Spark applications")
        
    except Exception as e:
        print(f"ERROR: collecting workspace Spark applications: {str(e)}")


def collect_spark_applications_item(
    workspace_id: str,
    item_id: str,
    item_type: str = "notebook",
    lookback_hours: int = 24,
    max_items: int = 100
) -> Iterator[Dict[str, Any]]:
    """
    Collect Spark applications for specific item.
    
    Args:
        workspace_id: Fabric workspace ID
        item_id: Item ID (notebook, Spark job definition, etc.)
        item_type: Type of item ('notebook', 'sparkjobdefinition', 'lakehouse')
        lookback_hours: Hours to look back for applications
        max_items: Maximum items to retrieve
        
    Yields:
        Dict containing Spark application information
    """
    try:
        token = get_fabric_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        endpoint_map = {
            "notebook": f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/notebooks/{item_id}/spark/sessions",
            "sparkjobdefinition": f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/sparkJobDefinitions/{item_id}/spark/sessions",
            "lakehouse": f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/lakehouses/{item_id}/spark/sessions"
        }
        
        url = endpoint_map.get(item_type.lower())
        if not url:
            print(f"ERROR: Unsupported item type: {item_type}")
            return
            
        print(f"INFO: Collecting Spark applications for {item_type} {item_id}")
        
        response = requests.get(url, headers=headers, timeout=30)
        data = handle_api_response(response, f"{item_type} Spark Applications - {item_id}")
        
        if not data or "value" not in data:
            print(f"WARNING: No Spark applications found for {item_type} {item_id}")
            return
            
        sessions = data["value"]
        print(f"Found {len(sessions)} Spark sessions for {item_type}")
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        collected_count = 0
        
        for session in sessions:
            if collected_count >= max_items:
                break
                
            try:
                session_time = parse_iso(session.get('submissionTime', ''))
                if session_time and session_time < cutoff_time:
                    continue
                
                session_id = session.get('id')
                session_details = get_spark_session_details(workspace_id, session_id, headers, item_type, item_id)
                
                yield {
                    "WorkspaceId": workspace_id,
                    "ItemId": item_id,
                    "ItemType": item_type,
                    "SessionId": session_id,
                    "ApplicationId": session.get('appId'),
                    "ApplicationName": session.get('name'),
                    "State": session.get('state'),
                    "SubmissionTime": session.get('submissionTime'),
                    "Kind": session.get('kind'),
                    "SparkVersion": session.get('sparkVersion'),
                    "DriverCores": session_details.get('driverCores'),
                    "DriverMemory": session_details.get('driverMemory'),
                    "ExecutorCores": session_details.get('executorCores'),
                    "ExecutorMemory": session_details.get('executorMemory'),
                    "ExecutorCount": session_details.get('numExecutors'),
                    "Duration": session_details.get('duration'),
                    "Tags": json.dumps(session.get('tags', {})),
                    "CollectedAt": iso_now(),
                    "MetricType": "SparkApplicationItem"
                }
                
                collected_count += 1
                
            except Exception as e:
                print(f"WARNING: Error processing session {session.get('id', 'unknown')}: {str(e)}")
                continue
                
        print(f"SUCCESS: Collected {collected_count} Spark applications for {item_type}")
        
    except Exception as e:
        print(f"ERROR: collecting Spark applications for {item_type}: {str(e)}")


# === Spark Logs and Metrics Collection Functions ===

def collect_spark_logs(
    workspace_id: str,
    session_id: str,
    log_type: str = "driver",
    max_lines: int = 1000
) -> Iterator[Dict[str, Any]]:
    """
    Collect Spark logs (driver, executor, livy) for a specific session.
    
    Args:
        workspace_id: Fabric workspace ID
        session_id: Spark session ID
        log_type: Type of logs ('driver', 'executor', 'livy')
        max_lines: Maximum log lines to retrieve
        
    Yields:
        Dict containing log entries
    """
    try:
        token = get_fabric_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        endpoint_map = {
            "driver": f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/spark/sessions/{session_id}/driverlog",
            "executor": f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/spark/sessions/{session_id}/executorlog",
            "livy": f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/spark/sessions/{session_id}/livylog"
        }
        
        url = endpoint_map.get(log_type.lower())
        if not url:
            print(f"ERROR: Unsupported log type: {log_type}")
            return
            
        print(f"INFO: Collecting {log_type} logs for session {session_id}")
        
        response = requests.get(url, headers=headers, timeout=60)
        
        if response.status_code == 200:
            log_content = response.text
            log_lines = log_content.split('\n')
            
            print(f"Found {len(log_lines)} log lines")
            
            for i, line in enumerate(log_lines[-max_lines:], 1):
                if line.strip():
                    yield {
                        "WorkspaceId": workspace_id,
                        "SessionId": session_id,
                        "LogType": log_type,
                        "LineNumber": i,
                        "LogMessage": line.strip(),
                        "CollectedAt": iso_now(),
                        "MetricType": "SparkLog"
                    }
                    
        else:
            print(f"WARNING: Failed to get {log_type} logs: {response.status_code}")
            
    except Exception as e:
        print(f"ERROR: collecting {log_type} logs: {str(e)}")


def collect_spark_metrics(
    workspace_id: str,
    session_id: str,
    application_id: str
) -> Iterator[Dict[str, Any]]:
    """
    Collect Spark metrics using Spark History Server APIs.
    
    Args:
        workspace_id: Fabric workspace ID
        session_id: Spark session ID
        application_id: Spark application ID
        
    Yields:
        Dict containing Spark metrics
    """
    try:
        token = get_fabric_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        base_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/spark/sessions/{session_id}/applications/{application_id}"
        
        metrics_endpoints = {
            "application": f"{base_url}",
            "jobs": f"{base_url}/jobs",
            "stages": f"{base_url}/stages",
            "executors": f"{base_url}/executors",
            "storage": f"{base_url}/storage/rdd"
        }
        
        print(f"INFO: Collecting Spark metrics for application {application_id}")
        
        for metric_type, url in metrics_endpoints.items():
            try:
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if metric_type == "application":
                        yield {
                            "WorkspaceId": workspace_id,
                            "SessionId": session_id,
                            "ApplicationId": application_id,
                            "MetricCategory": "Application",
                            "AppName": data.get('name'),
                            "Duration": data.get('duration'),
                            "StartTime": data.get('startTime'),
                            "EndTime": data.get('endTime'),
                            "SparkUser": data.get('sparkUser'),
                            "Completed": data.get('completed', False),
                            "CollectedAt": iso_now(),
                            "MetricType": "SparkMetric"
                        }
                        
                    elif metric_type == "executors":
                        if isinstance(data, list):
                            for executor in data:
                                yield {
                                    "WorkspaceId": workspace_id,
                                    "SessionId": session_id,
                                    "ApplicationId": application_id,
                                    "MetricCategory": "Executor",
                                    "ExecutorId": executor.get('id'),
                                    "HostPort": executor.get('hostPort'),
                                    "IsActive": executor.get('isActive'),
                                    "RddBlocks": executor.get('rddBlocks'),
                                    "MemoryUsed": executor.get('memoryUsed'),
                                    "DiskUsed": executor.get('diskUsed'),
                                    "TotalCores": executor.get('totalCores'),
                                    "MaxTasks": executor.get('maxTasks'),
                                    "ActiveTasks": executor.get('activeTasks'),
                                    "FailedTasks": executor.get('failedTasks'),
                                    "CompletedTasks": executor.get('completedTasks'),
                                    "TotalTasks": executor.get('totalTasks'),
                                    "CollectedAt": iso_now(),
                                    "MetricType": "SparkMetric"
                                }
                        
                    elif metric_type == "jobs":
                        if isinstance(data, list):
                            for job in data:
                                yield {
                                    "WorkspaceId": workspace_id,
                                    "SessionId": session_id,
                                    "ApplicationId": application_id,
                                    "MetricCategory": "Job",
                                    "JobId": job.get('jobId'),
                                    "Name": job.get('name'),
                                    "Status": job.get('status'),
                                    "SubmissionTime": job.get('submissionTime'),
                                    "CompletionTime": job.get('completionTime'),
                                    "NumTasks": job.get('numTasks'),
                                    "NumActiveTasks": job.get('numActiveTasks'),
                                    "NumCompletedTasks": job.get('numCompletedTasks'),
                                    "NumSkippedTasks": job.get('numSkippedTasks'),
                                    "NumFailedTasks": job.get('numFailedTasks'),
                                    "CollectedAt": iso_now(),
                                    "MetricType": "SparkMetric"
                                }
                                
                else:
                    print(f"WARNING: Failed to get {metric_type} metrics: {response.status_code}")
                    
            except Exception as e:
                print(f"WARNING: Error collecting {metric_type} metrics: {str(e)}")
                continue
                
        print(f"SUCCESS: Collected Spark metrics for application {application_id}")
        
    except Exception as e:
        print(f"ERROR: collecting Spark metrics: {str(e)}")
