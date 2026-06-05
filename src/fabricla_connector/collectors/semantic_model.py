"""
Semantic model (dataset) collectors.

Collects Semantic Model metadata and refresh summary records from a Fabric
workspace for ingestion into Log Analytics.
"""
import logging
from typing import Iterator, Dict, Any

from .base import BaseCollector
from ..utils import iso_now, safe_get
from ..api.exceptions import FabricResourceNotFoundError, FabricAuthorizationError

logger = logging.getLogger(__name__)


class SemanticModelCollector(BaseCollector):
    """
    Collector for Fabric Semantic Model (dataset) metadata and refresh history.

    Collects:
    - Semantic Model metadata (name, type, refresh settings, owner)
    - Refresh summary per model (status counts from recent refresh history)
    """

    def collect(self) -> Iterator[Dict[str, Any]]:
        """
        Collect semantic model metadata and refresh summary records.

        Yields:
            Semantic model metadata and refresh summary records
        """
        yield from self.collect_semantic_models()

    def collect_semantic_models(self) -> Iterator[Dict[str, Any]]:
        """
        Enumerate Semantic Models and yield metadata plus refresh summary records.

        Yields:
            Semantic model metadata records and per-model refresh summary records
        """
        try:
            datasets = self.client.list_datasets(self.workspace_id)
        except FabricAuthorizationError:
            logger.warning(
                "Authorization denied when listing datasets in workspace %s",
                self.workspace_id,
            )
            return
        except FabricResourceNotFoundError:
            logger.warning(
                "Workspace %s not found when listing datasets",
                self.workspace_id,
            )
            return

        for dataset in datasets:
            dataset_id = safe_get(dataset, "id", default="")
            dataset_name = safe_get(dataset, "displayName", default="")

            # Metadata record
            yield {
                "WorkspaceId": self.workspace_id,
                "DatasetId": dataset_id,
                "DatasetName": dataset_name,
                "RecordType": "Metadata",
                "Type": safe_get(dataset, "type", default=""),
                "IsRefreshable": safe_get(dataset, "isRefreshable", default=None),
                "ConfiguredBy": safe_get(dataset, "configuredBy", default=""),
                "CreatedDate": safe_get(dataset, "createdDate", default=""),
                "TimeGenerated": iso_now(),
            }

            # Refresh summary record
            try:
                refreshes = self.client.get_dataset_refreshes(
                    self.workspace_id,
                    dataset_id,
                    lookback_hours=self.lookback_hours,
                )
            except FabricResourceNotFoundError:
                logger.warning(
                    "Refresh history not found for dataset %s in workspace %s",
                    dataset_id,
                    self.workspace_id,
                )
                continue
            except FabricAuthorizationError:
                logger.warning(
                    "Authorization denied for refresh history of dataset %s",
                    dataset_id,
                )
                continue

            total = len(refreshes)
            completed = sum(
                1 for r in refreshes
                if safe_get(r, "status", default="").lower() == "completed"
            )
            failed = sum(
                1 for r in refreshes
                if safe_get(r, "status", default="").lower() == "failed"
            )

            yield {
                "WorkspaceId": self.workspace_id,
                "DatasetId": dataset_id,
                "DatasetName": dataset_name,
                "RecordType": "RefreshSummary",
                "TotalRefreshes": total,
                "CompletedRefreshes": completed,
                "FailedRefreshes": failed,
                "TimeGenerated": iso_now(),
            }
