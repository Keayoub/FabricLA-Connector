"""
OneLake storage collectors.

Collects Lakehouse inventory from a Fabric workspace, enumerating each
Lakehouse item and its metadata for ingestion into Log Analytics.
"""
import logging
from typing import Iterator, Dict, Any

from .base import BaseCollector
from ..utils import iso_now, safe_get
from ..api.exceptions import FabricResourceNotFoundError, FabricAuthorizationError

logger = logging.getLogger(__name__)


class OneLakeStorageCollector(BaseCollector):
    """
    Collector for OneLake / Lakehouse storage inventory.

    Collects:
    - Lakehouses present in the workspace
    - Per-lakehouse metadata (id, name, description)
    """

    def collect(self) -> Iterator[Dict[str, Any]]:
        """
        Collect OneLake / Lakehouse storage records.

        Yields:
            Lakehouse inventory records mapped to Log Analytics schema
        """
        yield from self.collect_lakehouses()

    def collect_lakehouses(self) -> Iterator[Dict[str, Any]]:
        """
        List Lakehouses in the workspace and yield one record per Lakehouse.

        Yields:
            Lakehouse metadata records
        """
        try:
            lakehouses = self.client.list_workspace_items(
                self.workspace_id,
                item_type="Lakehouse",
            )
        except FabricAuthorizationError:
            logger.warning(
                "Authorization denied when listing Lakehouses in workspace %s",
                self.workspace_id,
            )
            return
        except FabricResourceNotFoundError:
            logger.warning(
                "Workspace %s not found when listing Lakehouses",
                self.workspace_id,
            )
            return

        for lakehouse in lakehouses:
            lakehouse_id = safe_get(lakehouse, "id", default="")
            lakehouse_name = safe_get(lakehouse, "displayName", default="")

            detail = {}
            try:
                detail = self.client.get(
                    f"workspaces/{self.workspace_id}/lakehouses/{lakehouse_id}",
                    context=f"get lakehouse {lakehouse_id}",
                )
            except FabricResourceNotFoundError:
                logger.warning(
                    "Lakehouse %s not found in workspace %s",
                    lakehouse_id,
                    self.workspace_id,
                )
            except FabricAuthorizationError:
                logger.warning(
                    "Authorization denied for Lakehouse %s in workspace %s",
                    lakehouse_id,
                    self.workspace_id,
                )

            yield {
                "WorkspaceId": self.workspace_id,
                "LakehouseId": lakehouse_id,
                "LakehouseName": lakehouse_name,
                "Description": safe_get(detail, "description", default=""),
                "ItemType": "Lakehouse",
                "TimeGenerated": iso_now(),
            }
