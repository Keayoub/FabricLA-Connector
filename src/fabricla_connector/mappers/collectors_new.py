"""
Mappers for the 9 new collectors.

Each class transforms raw Fabric API item data into Log Analytics schema.
Used by workflow functions and can be called standalone.
"""
from typing import Dict, Any, Optional
from .base import BaseMapper
from ..utils import iso_now, parse_iso, safe_get


def _duration_ms(start: Optional[str], end: Optional[str]) -> Optional[int]:
    if not start or not end:
        return None
    try:
        s, e = parse_iso(start), parse_iso(end)
        if s and e:
            return int((e - s).total_seconds() * 1000)
    except (TypeError, ValueError, OSError):
        pass
    return None


class OneLakeStorageMapper(BaseMapper):
    """Map Lakehouse item data to Log Analytics schema."""

    @staticmethod
    def map(workspace_id: str, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "TimeGenerated": iso_now(),
            "WorkspaceId": workspace_id,
            "LakehouseId": safe_get(item, "id", default=""),
            "LakehouseName": safe_get(item, "displayName", default=""),
            "Description": safe_get(item, "description", default=""),
            "ItemType": "Lakehouse",
        }


class SparkJobMapper(BaseMapper):
    """Map SparkJobDefinition run instances to Log Analytics schema."""

    @staticmethod
    def map(
        workspace_id: str,
        job_def_id: str,
        job_def_name: str,
        instance: Dict[str, Any],
    ) -> Dict[str, Any]:
        start = safe_get(instance, "startTimeUtc", default="")
        end = safe_get(instance, "endTimeUtc", default="")
        return {
            "TimeGenerated": iso_now(),
            "WorkspaceId": workspace_id,
            "JobDefinitionId": job_def_id,
            "JobDefinitionName": job_def_name,
            "RunId": safe_get(instance, "id", default=""),
            "Status": safe_get(instance, "status", default=""),
            "StartTime": start,
            "EndTime": end,
            "DurationMs": _duration_ms(start, end),
        }


class NotebookRunMapper(BaseMapper):
    """Map Notebook run instances to Log Analytics schema."""

    @staticmethod
    def map(
        workspace_id: str,
        notebook_id: str,
        notebook_name: str,
        instance: Dict[str, Any],
    ) -> Dict[str, Any]:
        start = safe_get(instance, "startTimeUtc", default="")
        end = safe_get(instance, "endTimeUtc", default="")
        return {
            "TimeGenerated": iso_now(),
            "WorkspaceId": workspace_id,
            "NotebookId": notebook_id,
            "NotebookName": notebook_name,
            "RunId": safe_get(instance, "id", default=""),
            "Status": safe_get(instance, "status", default=""),
            "StartTime": start,
            "EndTime": end,
            "DurationMs": _duration_ms(start, end),
        }


class GitIntegrationMapper(BaseMapper):
    """Map workspace Git status/connection data to Log Analytics schema."""

    @staticmethod
    def map(
        workspace_id: str,
        git_status: Dict[str, Any],
        git_connection: Dict[str, Any],
    ) -> Dict[str, Any]:
        changes = git_status.get("changes", [])
        conflicted = [
            c for c in changes
            if safe_get(c, "conflictType") not in (None, "None", "")
        ]
        provider = safe_get(git_connection, "gitProviderDetails", default={})
        return {
            "TimeGenerated": iso_now(),
            "WorkspaceId": workspace_id,
            "RemoteCommitHash": safe_get(git_status, "remoteCommitHash", default=""),
            "WorkspaceHead": safe_get(git_status, "workspaceHead", default=""),
            "ConflictedItems": len(conflicted),
            "UnsyncedChanges": len(changes),
            "GitProviderType": safe_get(provider, "gitProviderType", default=""),
            "RepositoryName": safe_get(provider, "repositoryName", default=""),
            "BranchName": safe_get(provider, "branchName", default=""),
        }


class DataLineageMapper(BaseMapper):
    """Map item lineage data to Log Analytics schema."""

    @staticmethod
    def map(
        workspace_id: str,
        item: Dict[str, Any],
        lineage: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        lineage = lineage or {}
        upstream = lineage.get("upstreamItems", [])
        downstream = lineage.get("downstreamItems", [])
        return {
            "TimeGenerated": iso_now(),
            "WorkspaceId": workspace_id,
            "ItemId": safe_get(item, "id", default=""),
            "ItemName": safe_get(item, "displayName", default=""),
            "ItemType": safe_get(item, "type", default=""),
            "UpstreamCount": len(upstream),
            "DownstreamCount": len(downstream),
        }


class SemanticModelMapper(BaseMapper):
    """Map semantic model (dataset) metadata to Log Analytics schema."""

    @staticmethod
    def map(workspace_id: str, dataset: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "TimeGenerated": iso_now(),
            "WorkspaceId": workspace_id,
            "DatasetId": safe_get(dataset, "id", default=""),
            "DatasetName": safe_get(dataset, "name", default=""),
            "Type": safe_get(dataset, "type", default="SemanticModel"),
            "IsRefreshable": safe_get(dataset, "isRefreshable", default=False),
            "ConfiguredBy": safe_get(dataset, "configuredBy", default=""),
            "CreatedDate": safe_get(dataset, "createdDate", default=""),
        }


class RealTimeIntelligenceMapper(BaseMapper):
    """Map RTI item inventory (Eventhouse, KQLDatabase, Eventstream) to Log Analytics schema."""

    @staticmethod
    def map(workspace_id: str, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "TimeGenerated": iso_now(),
            "WorkspaceId": workspace_id,
            "ItemId": safe_get(item, "id", default=""),
            "ItemName": safe_get(item, "displayName", default=""),
            "ItemType": safe_get(item, "type", default=""),
            "Description": safe_get(item, "description", default=""),
        }


class MirroringMapper(BaseMapper):
    """Map mirrored database status to Log Analytics schema."""

    @staticmethod
    def map(
        workspace_id: str,
        item: Dict[str, Any],
        status: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        status = status or {}
        return {
            "TimeGenerated": iso_now(),
            "WorkspaceId": workspace_id,
            "MirroredDbId": safe_get(item, "id", default=""),
            "MirroredDbName": safe_get(item, "displayName", default=""),
            "Status": safe_get(status, "status", default="Unknown"),
            "LastSyncTime": safe_get(status, "lastSyncTime", default=""),
        }


class MLAIMapper(BaseMapper):
    """Map ML model and experiment items to Log Analytics schema."""

    @staticmethod
    def map(workspace_id: str, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "TimeGenerated": iso_now(),
            "WorkspaceId": workspace_id,
            "ItemId": safe_get(item, "id", default=""),
            "ItemName": safe_get(item, "displayName", default=""),
            "ItemType": safe_get(item, "type", default=""),
            "Description": safe_get(item, "description", default=""),
        }
