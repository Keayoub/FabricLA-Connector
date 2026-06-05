"""
Data lineage collectors.

Collects item-level lineage information (upstream / downstream counts) for all
items in a Fabric workspace for ingestion into Log Analytics.
"""
import logging
from typing import Iterator, Dict, Any

from .base import BaseCollector
from ..utils import iso_now, safe_get
from ..api.exceptions import FabricResourceNotFoundError, FabricAuthorizationError

logger = logging.getLogger(__name__)


class DataLineageCollector(BaseCollector):
    """
    Collector for Fabric item data lineage.

    Collects:
    - All items in the workspace
    - Upstream and downstream lineage counts per item (best-effort; 404 is silently skipped)
    """

    def collect(self) -> Iterator[Dict[str, Any]]:
        """
        Collect data lineage records for all workspace items.

        Yields:
            Data lineage records mapped to Log Analytics schema
        """
        yield from self.collect_lineage()

    def collect_lineage(self) -> Iterator[Dict[str, Any]]:
        """
        Enumerate all workspace items and yield one lineage record per item.

        Yields:
            Item lineage records
        """
        try:
            items = self.client.list_workspace_items(self.workspace_id)
        except FabricAuthorizationError:
            logger.warning(
                "Authorization denied when listing items in workspace %s",
                self.workspace_id,
            )
            return
        except FabricResourceNotFoundError:
            logger.warning(
                "Workspace %s not found when listing items for lineage",
                self.workspace_id,
            )
            return

        for item in items:
            item_id = safe_get(item, "id", default="")
            item_name = safe_get(item, "displayName", default="")
            item_type = safe_get(item, "type", default="")

            lineage: Dict[str, Any] = {}
            try:
                lineage = self.client.get(
                    f"workspaces/{self.workspace_id}/items/{item_id}/lineage",
                    context=f"get lineage for item {item_id}",
                )
            except FabricResourceNotFoundError:
                logger.warning(
                    "Lineage not available for item %s (%s) in workspace %s",
                    item_id,
                    item_type,
                    self.workspace_id,
                )
            except FabricAuthorizationError:
                logger.warning(
                    "Authorization denied for lineage of item %s in workspace %s",
                    item_id,
                    self.workspace_id,
                )

            upstream_items = lineage.get("upstreamItems", [])
            downstream_items = lineage.get("downstreamItems", [])

            yield {
                "WorkspaceId": self.workspace_id,
                "ItemId": item_id,
                "ItemName": item_name,
                "ItemType": item_type,
                "UpstreamCount": len(upstream_items),
                "DownstreamCount": len(downstream_items),
                "TimeGenerated": iso_now(),
            }
