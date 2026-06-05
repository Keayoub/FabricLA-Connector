"""
Git integration collectors.

Collects Git synchronisation status and connection details for a Fabric
workspace for ingestion into Log Analytics.
"""
import logging
from typing import Iterator, Dict, Any

from .base import BaseCollector
from ..utils import iso_now, safe_get
from ..api.exceptions import FabricResourceNotFoundError, FabricAuthorizationError

logger = logging.getLogger(__name__)


class GitIntegrationCollector(BaseCollector):
    """
    Collector for Fabric workspace Git integration status.

    Collects:
    - Git synchronisation status (remote commit hash, workspace head, conflicts)
    - Git connection details (provider, repository, branch)
    """

    def collect(self) -> Iterator[Dict[str, Any]]:
        """
        Collect Git integration status and connection records.

        Yields:
            Git integration records mapped to Log Analytics schema
        """
        yield from self.collect_git_status()

    def collect_git_status(self) -> Iterator[Dict[str, Any]]:
        """
        Fetch Git status and connection for the workspace and yield one record.

        Yields:
            A single Git integration record
        """
        git_status: Dict[str, Any] = {}
        git_connection: Dict[str, Any] = {}

        try:
            git_status = self.client.get(
                f"workspaces/{self.workspace_id}/git/status",
                context=f"get git status for workspace {self.workspace_id}",
            )
        except FabricResourceNotFoundError:
            logger.warning(
                "Git integration not configured for workspace %s",
                self.workspace_id,
            )
            return
        except FabricAuthorizationError:
            logger.warning(
                "Authorization denied for git status in workspace %s",
                self.workspace_id,
            )
            return

        try:
            git_connection = self.client.get(
                f"workspaces/{self.workspace_id}/git/connection",
                context=f"get git connection for workspace {self.workspace_id}",
            )
        except FabricResourceNotFoundError:
            logger.warning(
                "Git connection not found for workspace %s; proceeding with status only",
                self.workspace_id,
            )
        except FabricAuthorizationError:
            logger.warning(
                "Authorization denied for git connection in workspace %s",
                self.workspace_id,
            )

        changes = git_status.get("changes", [])
        conflicted = [c for c in changes if safe_get(c, "conflictType") not in (None, "None", "")]

        git_provider_details = safe_get(git_connection, "gitProviderDetails", default={})

        yield {
            "WorkspaceId": self.workspace_id,
            "RemoteCommitHash": safe_get(git_status, "remoteCommitHash", default=""),
            "WorkspaceHead": safe_get(git_status, "workspaceHead", default=""),
            "ConflictedItems": len(conflicted),
            "UnsyncedChanges": len(changes),
            "GitProviderType": safe_get(git_provider_details, "gitProviderType", default=""),
            "RepositoryName": safe_get(git_provider_details, "repositoryName", default=""),
            "BranchName": safe_get(git_provider_details, "branchName", default=""),
            "TimeGenerated": iso_now(),
        }
