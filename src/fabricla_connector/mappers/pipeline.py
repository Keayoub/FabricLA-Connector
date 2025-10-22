"""
Pipeline and dataflow data mappers.
Transform raw Fabric API responses to Log Analytics schema.
"""
from typing import Dict, Any, Optional
from .base import BaseMapper
from ..utils import parse_iso, iso_now


class PipelineRunMapper(BaseMapper):
    """Map pipeline run data to Log Analytics schema."""
    
    @staticmethod
    def map(workspace_id: str, pipeline_id: str, pipeline_name: str, run: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map pipeline run to Log Analytics schema.
        
        Args:
            workspace_id: Fabric workspace ID
            pipeline_id: Pipeline ID
            pipeline_name: Pipeline display name
            run: Raw pipeline run data from API
            
        Returns:
            Mapped pipeline run data
        """
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


class ActivityRunMapper(BaseMapper):
    """Map activity run data to Log Analytics schema."""
    
    @staticmethod
    def map(workspace_id: str, pipeline_id: str, pipeline_run_id: str, activity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map activity run to Log Analytics schema with performance metrics.
        
        Args:
            workspace_id: Fabric workspace ID
            pipeline_id: Pipeline ID
            pipeline_run_id: Pipeline run ID
            activity: Raw activity run data from API
            
        Returns:
            Mapped activity run data
        """
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
        
        # Extract performance metrics from activity output
        output = activity.get("output") or {}
        data_read = None
        data_written = None
        records_processed = None
        execution_statistics = None
        
        if isinstance(output, dict):
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
            if output:
                execution_statistics = output
        
        return {
            "TimeGenerated": end_time or start_time or iso_now(),
            "WorkspaceId": workspace_id,
            "PipelineId": pipeline_id,
            "PipelineName": pipeline_id,  # For compatibility
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


class DataflowRunMapper(BaseMapper):
    """Map dataflow run data to Log Analytics schema."""
    
    @staticmethod
    def map(workspace_id: str, dataflow_id: str, dataflow_name: str, run: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map dataflow run to Log Analytics schema.
        
        Args:
            workspace_id: Fabric workspace ID
            dataflow_id: Dataflow ID
            dataflow_name: Dataflow display name
            run: Raw dataflow run data from API
            
        Returns:
            Mapped dataflow run data
        """
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
