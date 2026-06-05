"""
Mirroring collectors.

Collects mirrored database items and their mirroring status from a Fabric
workspace for ingestion into Log Analytics.
"""
import logging
from typing import Iterator, Dict, Any

import requests

from .base import BaseCollector
from ..utils import iso_now, safe_get
from ..api.exceptions import FabricResourceNotFoundError, FabricAuthorizationError

logger = logging.getLogger(__name__)


class MirroringCollector(BaseCollector):
    """
    Collector for Fabric mirrored database status.

    Collects:
    - MirroredDatabase items in the workspace
    - Current mirroring status for each mirrored database
    """

    def collect(self) -> Iterator[Dict[str, Any]]:
        """
        Collect mirrored database status records.

        Yields:
            Mirrored database status records mapped to Log Analytics schema
        """
        yield from self.collect_mirrored_databases()

    def collect_mirrored_databases(self) -> Iterator[Dict[str, Any]]:
        """
        Enumerate MirroredDatabase items and yield one status record each.

        Yields:
            Mirrored database status records
        """
        try:
            mirrored_dbs = self.client.list_workspace_items(
                self.workspace_id,
                item_type="MirroredDatabase",
            )
        except FabricAuthorizationError:
            logger.warning(
                "Authorization denied when listing MirroredDatabases in workspace %s",
                self.workspace_id,
            )
            return
        except FabricResourceNotFoundError:
            logger.warning(
                "Workspace %s not found when listing MirroredDatabases",
                self.workspace_id,
            )
            return

        for db in mirrored_dbs:
            db_id = safe_get(db, "id", default="")
            db_name = safe_get(db, "displayName", default="")

            status = "Unknown"
            try:
                url = (
                    f"{self.client.BASE_URL}/workspaces/{self.workspace_id}"
                    f"/mirroredDatabases/{db_id}/getMirroringStatus"
                )
                response = self.client.session.post(url, json={})
                if response.status_code == 200:
                    data = response.json()
                    status = safe_get(data, "status", default="Unknown")
                elif response.status_code == 404:
                    logger.warning(
                        "getMirroringStatus not available for MirroredDatabase %s",
                        db_id,
                    )
                elif response.status_code == 403:
                    logger.warning(
                        "Authorization denied for getMirroringStatus of MirroredDatabase %s",
                        db_id,
                    )
                else:
                    logger.warning(
                        "getMirroringStatus returned %s for MirroredDatabase %s",
                        response.status_code,
                        db_id,
                    )
            except requests.RequestException as exc:
                logger.warning(
                    "Failed to get mirroring status for MirroredDatabase %s: %s",
                    db_id,
                    exc,
                )

            yield {
                "WorkspaceId": self.workspace_id,
                "MirroredDbId": db_id,
                "MirroredDbName": db_name,
                "Status": status,
                "TimeGenerated": iso_now(),
            }
