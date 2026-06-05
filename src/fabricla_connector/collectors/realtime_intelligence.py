"""
Real-Time Intelligence collectors.

Collects inventory of Real-Time Intelligence items (Eventhouses, KQL Databases,
Eventstreams) from a Fabric workspace for ingestion into Log Analytics.
"""
import logging
from typing import Iterator, Dict, Any

from .base import BaseCollector
from ..utils import iso_now, safe_get
from ..api.exceptions import FabricResourceNotFoundError, FabricAuthorizationError

logger = logging.getLogger(__name__)

_RTI_ITEM_TYPES = ("Eventhouse", "KQLDatabase", "Eventstream")


class RealTimeIntelligenceCollector(BaseCollector):
    """
    Collector for Fabric Real-Time Intelligence item inventory.

    Collects:
    - Eventhouses
    - KQL Databases
    - Eventstreams
    """

    def collect(self) -> Iterator[Dict[str, Any]]:
        """
        Collect Real-Time Intelligence item inventory records.

        Yields:
            Inventory records for each RTI item type
        """
        for item_type in _RTI_ITEM_TYPES:
            yield from self.collect_items_by_type(item_type)

    def collect_items_by_type(self, item_type: str) -> Iterator[Dict[str, Any]]:
        """
        List items of a given RTI type and yield one inventory record per item.

        Args:
            item_type: Fabric item type string (e.g. "Eventhouse")

        Yields:
            Inventory records for the specified item type
        """
        try:
            items = self.client.list_workspace_items(
                self.workspace_id,
                item_type=item_type,
            )
        except FabricAuthorizationError:
            logger.warning(
                "Authorization denied when listing %s items in workspace %s",
                item_type,
                self.workspace_id,
            )
            return
        except FabricResourceNotFoundError:
            logger.warning(
                "Workspace %s not found when listing %s items",
                self.workspace_id,
                item_type,
            )
            return

        for item in items:
            yield {
                "WorkspaceId": self.workspace_id,
                "ItemId": safe_get(item, "id", default=""),
                "ItemName": safe_get(item, "displayName", default=""),
                "ItemType": item_type,
                "TimeGenerated": iso_now(),
            }
