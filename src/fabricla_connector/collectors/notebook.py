"""
Notebook execution collectors.

Collects Notebook items and their run history from a Fabric workspace for
ingestion into Log Analytics.
"""
import logging
from typing import Iterator, Dict, Any

from .base import BaseCollector
from ..utils import iso_now, safe_get
from ..api.exceptions import FabricResourceNotFoundError, FabricAuthorizationError

logger = logging.getLogger(__name__)


class NotebookCollector(BaseCollector):
    """
    Collector for Fabric Notebook execution history.

    Collects:
    - Notebook items in the workspace
    - Job run instances for each notebook
    """

    def collect(self) -> Iterator[Dict[str, Any]]:
        """
        Collect Notebook run records.

        Yields:
            Notebook run records mapped to Log Analytics schema
        """
        yield from self.collect_notebook_runs()

    def collect_notebook_runs(self) -> Iterator[Dict[str, Any]]:
        """
        Enumerate Notebooks and yield one record per run instance.

        Yields:
            Notebook run records
        """
        try:
            notebooks = self.client.list_workspace_items(
                self.workspace_id,
                item_type="Notebook",
            )
        except FabricAuthorizationError:
            logger.warning(
                "Authorization denied when listing Notebooks in workspace %s",
                self.workspace_id,
            )
            return
        except FabricResourceNotFoundError:
            logger.warning(
                "Workspace %s not found when listing Notebooks",
                self.workspace_id,
            )
            return

        for notebook in notebooks:
            notebook_id = safe_get(notebook, "id", default="")
            notebook_name = safe_get(notebook, "displayName", default="")

            try:
                instances = self.client.list_item_job_instances(
                    self.workspace_id,
                    notebook_id,
                    lookback_hours=self.lookback_hours,
                )
            except FabricResourceNotFoundError:
                logger.warning(
                    "No job instances found for Notebook %s in workspace %s",
                    notebook_id,
                    self.workspace_id,
                )
                continue
            except FabricAuthorizationError:
                logger.warning(
                    "Authorization denied for job instances of Notebook %s",
                    notebook_id,
                )
                continue

            for instance in instances:
                start_time = safe_get(instance, "startTimeUtc", default="")
                end_time = safe_get(instance, "endTimeUtc", default="")

                duration_ms = None
                if start_time and end_time:
                    from ..utils import parse_iso
                    start_dt = parse_iso(start_time)
                    end_dt = parse_iso(end_time)
                    if start_dt and end_dt:
                        duration_ms = int(
                            (end_dt - start_dt).total_seconds() * 1000
                        )

                yield {
                    "WorkspaceId": self.workspace_id,
                    "NotebookId": notebook_id,
                    "NotebookName": notebook_name,
                    "RunId": safe_get(instance, "id", default=""),
                    "Status": safe_get(instance, "status", default=""),
                    "StartTime": start_time,
                    "EndTime": end_time,
                    "DurationMs": duration_ms,
                    "TimeGenerated": iso_now(),
                }
