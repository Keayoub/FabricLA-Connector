"""
Spark Job Definition collectors.

Collects Spark Job Definition items and their job run history from a Fabric
workspace for ingestion into Log Analytics.
"""
import logging
from typing import Iterator, Dict, Any

from .base import BaseCollector
from ..utils import iso_now, safe_get
from ..api.exceptions import FabricResourceNotFoundError, FabricAuthorizationError

logger = logging.getLogger(__name__)


class SparkJobCollector(BaseCollector):
    """
    Collector for Spark Job Definition execution history.

    Collects:
    - SparkJobDefinition items in the workspace
    - Job run instances for each definition
    """

    def collect(self) -> Iterator[Dict[str, Any]]:
        """
        Collect Spark Job Definition run records.

        Yields:
            Spark job run records mapped to Log Analytics schema
        """
        yield from self.collect_spark_job_runs()

    def collect_spark_job_runs(self) -> Iterator[Dict[str, Any]]:
        """
        Enumerate SparkJobDefinitions and yield one record per job run instance.

        Yields:
            Spark job run records
        """
        try:
            job_definitions = self.client.list_workspace_items(
                self.workspace_id,
                item_type="SparkJobDefinition",
            )
        except FabricAuthorizationError:
            logger.warning(
                "Authorization denied when listing SparkJobDefinitions in workspace %s",
                self.workspace_id,
            )
            return
        except FabricResourceNotFoundError:
            logger.warning(
                "Workspace %s not found when listing SparkJobDefinitions",
                self.workspace_id,
            )
            return

        for job_def in job_definitions:
            job_def_id = safe_get(job_def, "id", default="")
            job_def_name = safe_get(job_def, "displayName", default="")

            try:
                instances = self.client.list_item_job_instances(
                    self.workspace_id,
                    job_def_id,
                    lookback_hours=self.lookback_hours,
                )
            except FabricResourceNotFoundError:
                logger.warning(
                    "No job instances found for SparkJobDefinition %s in workspace %s",
                    job_def_id,
                    self.workspace_id,
                )
                continue
            except FabricAuthorizationError:
                logger.warning(
                    "Authorization denied for job instances of SparkJobDefinition %s",
                    job_def_id,
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
                    "JobDefinitionId": job_def_id,
                    "JobDefinitionName": job_def_name,
                    "RunId": safe_get(instance, "id", default=""),
                    "Status": safe_get(instance, "status", default=""),
                    "StartTime": start_time,
                    "EndTime": end_time,
                    "DurationMs": duration_ms,
                    "TimeGenerated": iso_now(),
                }
