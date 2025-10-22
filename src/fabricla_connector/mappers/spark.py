"""
Mappers for Spark monitoring data.

Transforms raw Spark API responses into Log Analytics schema-compliant records.
"""
from typing import Dict, Optional, List
from fabricla_connector.utils import iso_now


class LivySessionMapper:
    """Maps Livy session data to Log Analytics schema."""
    
    @staticmethod
    def map(workspace_id: str, item_type: str, item_id: str, item_name: str, 
            session: Dict, workspace_name: Optional[str] = None) -> Dict:
        """
        Map Livy session data to FabricSparkLivySession_CL table schema.
        
        Args:
            workspace_id: The Fabric workspace ID
            item_type: Type of item (Notebook, SparkJobDefinition, Lakehouse)
            item_id: ID of the parent item
            item_name: Display name of the parent item
            session: Livy session object from API
            workspace_name: Optional workspace display name
        
        Returns:
            Dictionary matching FabricSparkLivySession_CL schema
        """
        # Extract timestamps
        created_time = session.get('createdAt') or session.get('createdTime')
        last_updated = session.get('lastUpdatedAt') or session.get('lastUpdatedTime') or created_time
        
        # Use last_updated as TimeGenerated, fallback to created, then current time
        time_generated = last_updated or created_time or iso_now()
        
        # Extract application ID (may be in different fields)
        app_id = session.get('appId') or session.get('applicationId') or session.get('sparkApplicationId')
        
        # Extract session logs if available
        session_logs = session.get('log') or session.get('logs')
        if session_logs and isinstance(session_logs, list):
            # Keep as structured data for Log Analytics
            session_logs = session_logs
        else:
            session_logs = None
        
        return {
            "TimeGenerated": time_generated,
            "WorkspaceId": workspace_id,
            "SessionId": session.get('id'),
            "ApplicationId": app_id,
            "ItemType": item_type,
            "ItemId": item_id,
            "ItemName": item_name,
            "Owner": session.get('owner'),
            "ProxyUser": session.get('proxyUser'),
            "Kind": session.get('kind'),  # spark, pyspark, sparkr, sql
            "State": session.get('state'),  # not_started, starting, idle, busy, shutting_down, error, dead, killed, success
            "DriverLogUrl": session.get('driverLogUrl'),
            "SparkUiUrl": session.get('sparkUiUrl') or session.get('appInfo', {}).get('sparkUiUrl'),
            "SessionLogs": session_logs,
            "CreatedTime": created_time,
            "LastUpdatedTime": last_updated,
            "WorkspaceName": workspace_name
        }


class SparkResourceMapper:
    """Maps Spark resource usage data to Log Analytics schema."""
    
    @staticmethod
    def map_driver(workspace_id: str, session_id: str, app_id: str, item_type: str, 
                   item_id: str, item_name: str, driver_data: Dict, 
                   timestamp: Optional[str] = None) -> Dict:
        """
        Map Spark driver resource usage to FabricSparkResourceUsage_CL schema.
        
        Args:
            workspace_id: The Fabric workspace ID
            session_id: Livy session ID
            app_id: Spark application ID
            item_type: Type of item (Notebook, SparkJobDefinition, etc.)
            item_id: ID of the parent item
            item_name: Display name of the parent item
            driver_data: Driver resource data from API
            timestamp: Optional timestamp for the metrics
        
        Returns:
            Dictionary matching FabricSparkResourceUsage_CL schema
        """
        return {
            "TimeGenerated": timestamp or iso_now(),
            "WorkspaceId": workspace_id,
            "SessionId": session_id,
            "ApplicationId": app_id,
            "ItemType": item_type,
            "ItemId": item_id,
            "ItemName": item_name,
            "ResourceType": "driver",
            "ExecutorId": None,  # Drivers don't have executor IDs
            "CpuUsagePercent": driver_data.get('cpuUsagePercent'),
            "MemoryUsedMB": driver_data.get('memoryUsedMB'),
            "MemoryTotalMB": driver_data.get('memoryTotalMB'),
            "MemoryUsagePercent": driver_data.get('memoryUsagePercent'),
            "DiskUsedMB": driver_data.get('diskUsedMB'),
            "DiskTotalMB": driver_data.get('diskTotalMB'),
            "NetworkReadMB": driver_data.get('networkReadMB'),
            "NetworkWriteMB": driver_data.get('networkWriteMB'),
            "GcTimeMs": driver_data.get('gcTimeMs'),
            "TasksActive": driver_data.get('tasksActive'),
            "TasksCompleted": driver_data.get('tasksCompleted'),
            "TasksFailed": driver_data.get('tasksFailed'),
            "ShuffleReadMB": driver_data.get('shuffleReadMB'),
            "ShuffleWriteMB": driver_data.get('shuffleWriteMB'),
            "Timestamp": timestamp or iso_now()
        }
    
    @staticmethod
    def map_executor(workspace_id: str, session_id: str, app_id: str, item_type: str,
                     item_id: str, item_name: str, executor_data: Dict,
                     timestamp: Optional[str] = None) -> Dict:
        """
        Map Spark executor resource usage to FabricSparkResourceUsage_CL schema.
        
        Args:
            workspace_id: The Fabric workspace ID
            session_id: Livy session ID
            app_id: Spark application ID
            item_type: Type of item (Notebook, SparkJobDefinition, etc.)
            item_id: ID of the parent item
            item_name: Display name of the parent item
            executor_data: Executor resource data from API
            timestamp: Optional timestamp for the metrics
        
        Returns:
            Dictionary matching FabricSparkResourceUsage_CL schema
        """
        return {
            "TimeGenerated": timestamp or iso_now(),
            "WorkspaceId": workspace_id,
            "SessionId": session_id,
            "ApplicationId": app_id,
            "ItemType": item_type,
            "ItemId": item_id,
            "ItemName": item_name,
            "ResourceType": "executor",
            "ExecutorId": executor_data.get('executorId'),
            "CpuUsagePercent": executor_data.get('cpuUsagePercent'),
            "MemoryUsedMB": executor_data.get('memoryUsedMB'),
            "MemoryTotalMB": executor_data.get('memoryTotalMB'),
            "MemoryUsagePercent": executor_data.get('memoryUsagePercent'),
            "DiskUsedMB": executor_data.get('diskUsedMB'),
            "DiskTotalMB": executor_data.get('diskTotalMB'),
            "NetworkReadMB": executor_data.get('networkReadMB'),
            "NetworkWriteMB": executor_data.get('networkWriteMB'),
            "GcTimeMs": executor_data.get('gcTimeMs'),
            "TasksActive": executor_data.get('tasksActive'),
            "TasksCompleted": executor_data.get('tasksCompleted'),
            "TasksFailed": executor_data.get('tasksFailed'),
            "ShuffleReadMB": executor_data.get('shuffleReadMB'),
            "ShuffleWriteMB": executor_data.get('shuffleWriteMB'),
            "Timestamp": timestamp or iso_now()
        }
    
    @staticmethod
    def map_aggregate(workspace_id: str, session_id: str, app_id: str, item_type: str,
                      item_id: str, item_name: str, aggregate_data: Dict,
                      timestamp: Optional[str] = None) -> Dict:
        """
        Map Spark aggregate resource usage to FabricSparkResourceUsage_CL schema.
        
        Args:
            workspace_id: The Fabric workspace ID
            session_id: Livy session ID
            app_id: Spark application ID
            item_type: Type of item (Notebook, SparkJobDefinition, etc.)
            item_id: ID of the parent item
            item_name: Display name of the parent item
            aggregate_data: Aggregate resource data from API
            timestamp: Optional timestamp for the metrics
        
        Returns:
            Dictionary matching FabricSparkResourceUsage_CL schema
        """
        return {
            "TimeGenerated": timestamp or iso_now(),
            "WorkspaceId": workspace_id,
            "SessionId": session_id,
            "ApplicationId": app_id,
            "ItemType": item_type,
            "ItemId": item_id,
            "ItemName": item_name,
            "ResourceType": "aggregate",
            "ExecutorId": None,  # Aggregates don't have executor IDs
            "CpuUsagePercent": aggregate_data.get('cpuUsagePercent'),
            "MemoryUsedMB": aggregate_data.get('memoryUsedMB'),
            "MemoryTotalMB": aggregate_data.get('memoryTotalMB'),
            "MemoryUsagePercent": aggregate_data.get('memoryUsagePercent'),
            "DiskUsedMB": aggregate_data.get('diskUsedMB'),
            "DiskTotalMB": aggregate_data.get('diskTotalMB'),
            "NetworkReadMB": aggregate_data.get('networkReadMB'),
            "NetworkWriteMB": aggregate_data.get('networkWriteMB'),
            "GcTimeMs": aggregate_data.get('gcTimeMs'),
            "TasksActive": aggregate_data.get('tasksActive'),
            "TasksCompleted": aggregate_data.get('tasksCompleted'),
            "TasksFailed": aggregate_data.get('tasksFailed'),
            "ShuffleReadMB": aggregate_data.get('shuffleReadMB'),
            "ShuffleWriteMB": aggregate_data.get('shuffleWriteMB'),
            "Timestamp": timestamp or iso_now()
        }


# Legacy function-style mappers for backward compatibility
def map_livy_session(workspace_id: str, item_type: str, item_id: str, item_name: str,
                     session: Dict, workspace_name: Optional[str] = None) -> Dict:
    """Legacy function wrapper for LivySessionMapper.map()"""
    return LivySessionMapper.map(workspace_id, item_type, item_id, item_name, session, workspace_name)


def map_spark_resource_driver(workspace_id: str, session_id: str, app_id: str, item_type: str,
                               item_id: str, item_name: str, driver_data: Dict,
                               timestamp: Optional[str] = None) -> Dict:
    """Legacy function wrapper for SparkResourceMapper.map_driver()"""
    return SparkResourceMapper.map_driver(workspace_id, session_id, app_id, item_type,
                                          item_id, item_name, driver_data, timestamp)


def map_spark_resource_executor(workspace_id: str, session_id: str, app_id: str, item_type: str,
                                 item_id: str, item_name: str, executor_data: Dict,
                                 timestamp: Optional[str] = None) -> Dict:
    """Legacy function wrapper for SparkResourceMapper.map_executor()"""
    return SparkResourceMapper.map_executor(workspace_id, session_id, app_id, item_type,
                                            item_id, item_name, executor_data, timestamp)


def map_spark_resource_aggregate(workspace_id: str, session_id: str, app_id: str, item_type: str,
                                  item_id: str, item_name: str, aggregate_data: Dict,
                                  timestamp: Optional[str] = None) -> Dict:
    """Legacy function wrapper for SparkResourceMapper.map_aggregate()"""
    return SparkResourceMapper.map_aggregate(workspace_id, session_id, app_id, item_type,
                                             item_id, item_name, aggregate_data, timestamp)
