"""
Unit tests for all mapper classes — happy path + edge cases (null fields,
malformed API responses, missing keys).
"""
import pytest
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
def _import_mappers():
    """Ensure mappers are importable; skip entire module if not."""
    try:
        import fabricla_connector.mappers  # noqa: F401
    except ImportError as exc:
        pytest.skip(f"fabricla_connector not installed: {exc}")


# ── PipelineRunMapper ─────────────────────────────────────────────────────────

class TestPipelineRunMapper:
    def _mapper(self):
        from fabricla_connector.mappers import PipelineRunMapper
        return PipelineRunMapper()

    def _run(self, **overrides):
        base = {
            "id": "run-id-1",
            "status": "Succeeded",
            "startTimeUtc": "2024-01-15T10:00:00Z",
            "endTimeUtc": "2024-01-15T10:05:00Z",
            "invokeType": "Manual",
            "jobType": "Pipeline",
        }
        base.update(overrides)
        return base

    def test_happy_path(self):
        mapper = self._mapper()
        result = mapper.map(self._run(), workspace_id="ws-1", pipeline_id="pl-1")
        assert result["RunId"] == "run-id-1"
        assert result["Status"] == "Succeeded"
        assert result["WorkspaceId"] == "ws-1"
        assert result["PipelineId"] == "pl-1"
        assert "TimeGenerated" in result
        assert result["DurationMs"] == 5 * 60 * 1000

    def test_missing_end_time_does_not_crash(self):
        mapper = self._mapper()
        run = self._run()
        del run["endTimeUtc"]
        result = mapper.map(run, workspace_id="ws-1", pipeline_id="pl-1")
        assert result["Status"] == "Succeeded"

    def test_null_invoke_type(self):
        mapper = self._mapper()
        result = mapper.map(self._run(invokeType=None), workspace_id="ws-1", pipeline_id="pl-1")
        assert result is not None

    def test_time_generated_is_iso_utc(self):
        mapper = self._mapper()
        result = mapper.map(self._run(), workspace_id="ws-1", pipeline_id="pl-1")
        tg = result["TimeGenerated"]
        assert tg.endswith("Z") or "+" in tg or tg.endswith("+00:00")


# ── ActivityRunMapper ─────────────────────────────────────────────────────────

class TestActivityRunMapper:
    def _mapper(self):
        from fabricla_connector.mappers import ActivityRunMapper
        return ActivityRunMapper()

    def _activity(self, **overrides):
        base = {
            "activityName": "Copy Data",
            "activityType": "Copy",
            "status": "Succeeded",
            "startTimeUtc": "2024-01-15T10:01:00Z",
            "endTimeUtc": "2024-01-15T10:04:00Z",
            "durationInMs": 180000,
            "output": {
                "dataRead": 1024,
                "dataWritten": 1024,
                "recordsProcessed": 100,
            },
        }
        base.update(overrides)
        return base

    def test_happy_path(self):
        mapper = self._mapper()
        result = mapper.map(self._activity(), workspace_id="ws-1", pipeline_id="pl-1", run_id="r-1")
        assert result["ActivityName"] == "Copy Data"
        assert result["ActivityType"] == "Copy"
        assert result["DurationMs"] == 180000

    def test_missing_output_block(self):
        mapper = self._mapper()
        activity = self._activity()
        del activity["output"]
        result = mapper.map(activity, workspace_id="ws-1", pipeline_id="pl-1", run_id="r-1")
        assert result is not None

    def test_partial_output_block(self):
        mapper = self._mapper()
        result = mapper.map(
            self._activity(output={"dataRead": 512}),
            workspace_id="ws-1", pipeline_id="pl-1", run_id="r-1",
        )
        assert result["DataRead"] == 512


# ── DataflowRunMapper ─────────────────────────────────────────────────────────

class TestDataflowRunMapper:
    def _mapper(self):
        from fabricla_connector.mappers import DataflowRunMapper
        return DataflowRunMapper()

    def test_happy_path(self):
        mapper = self._mapper()
        run = {
            "id": "df-run-1",
            "status": "Succeeded",
            "startTimeUtc": "2024-01-15T10:00:00Z",
            "endTimeUtc": "2024-01-15T10:10:00Z",
            "invokeType": "Scheduled",
            "jobType": "Dataflow",
        }
        result = mapper.map(run, workspace_id="ws-1", dataflow_id="df-1")
        assert result["Status"] == "Succeeded"
        assert "TimeGenerated" in result

    def test_empty_run_does_not_crash(self):
        mapper = self._mapper()
        result = mapper.map({}, workspace_id="ws-1", dataflow_id="df-1")
        assert isinstance(result, dict)


# ── DatasetRefreshMapper ──────────────────────────────────────────────────────

class TestDatasetRefreshMapper:
    def _mapper(self):
        from fabricla_connector.mappers import DatasetRefreshMapper
        return DatasetRefreshMapper()

    def test_happy_path(self):
        mapper = self._mapper()
        result = mapper.map(
            {
                "id": "refresh-1",
                "refreshType": "Full",
                "status": "Completed",
                "startTime": "2024-01-15T10:00:00Z",
                "endTime": "2024-01-15T10:03:00Z",
            },
            workspace_id="ws-1",
            dataset_id="ds-1",
        )
        assert result["Status"] == "Completed"
        assert result["DatasetId"] == "ds-1"
        assert result["DurationMs"] == 3 * 60 * 1000

    def test_missing_end_time(self):
        mapper = self._mapper()
        result = mapper.map(
            {"id": "r1", "status": "InProgress", "startTime": "2024-01-15T10:00:00Z"},
            workspace_id="ws-1",
            dataset_id="ds-1",
        )
        assert result is not None


# ── DatasetMetadataMapper ─────────────────────────────────────────────────────

class TestDatasetMetadataMapper:
    def _mapper(self):
        from fabricla_connector.mappers import DatasetMetadataMapper
        return DatasetMetadataMapper()

    def test_happy_path(self):
        mapper = self._mapper()
        result = mapper.map(
            {
                "id": "ds-1",
                "name": "Sales Dataset",
                "createdDate": "2024-01-01T00:00:00Z",
                "modifiedDate": "2024-01-10T00:00:00Z",
                "createdBy": "user@contoso.com",
            },
            workspace_id="ws-1",
        )
        assert result["DatasetName"] == "Sales Dataset"
        assert "TimeGenerated" in result

    def test_missing_optional_fields(self):
        mapper = self._mapper()
        result = mapper.map({"id": "ds-2", "name": "Min Dataset"}, workspace_id="ws-1")
        assert result["DatasetName"] == "Min Dataset"


# ── CapacityMetricMapper ──────────────────────────────────────────────────────

class TestCapacityMetricMapper:
    def _mapper(self):
        from fabricla_connector.mappers import CapacityMetricMapper
        return CapacityMetricMapper()

    def test_happy_path(self):
        mapper = self._mapper()
        result = mapper.map(
            {"workloadType": "PowerBI", "workloadState": "Enabled", "maxMemoryPercentage": 75.5},
            capacity_id="cap-1",
        )
        assert result["WorkloadName"] == "PowerBI"
        assert result["CapacityId"] == "cap-1"
        assert "TimeGenerated" in result

    def test_zero_memory_percentage(self):
        mapper = self._mapper()
        result = mapper.map(
            {"workloadType": "Spark", "workloadState": "Disabled", "maxMemoryPercentage": 0},
            capacity_id="cap-1",
        )
        assert result["MaxMemoryPercentage"] == 0


# ── UserActivityMapper ────────────────────────────────────────────────────────

class TestUserActivityMapper:
    def _mapper(self):
        from fabricla_connector.mappers import UserActivityMapper
        return UserActivityMapper()

    def test_happy_path(self):
        mapper = self._mapper()
        result = mapper.map(
            {
                "id": "evt-1",
                "userId": "user-1",
                "activityType": "DatasetRefresh",
                "creationTime": "2024-01-15T10:00:00Z",
                "itemName": "My Dataset",
                "workspaceName": "My Workspace",
                "isSuccess": True,
            }
        )
        assert result["UserId"] == "user-1"
        assert result["Activity"] == "DatasetRefresh"
        assert result["IsSuccess"] is True

    def test_null_item_name(self):
        mapper = self._mapper()
        result = mapper.map(
            {
                "id": "evt-2",
                "userId": "user-1",
                "activityType": "Export",
                "creationTime": "2024-01-15T10:00:00Z",
                "itemName": None,
            }
        )
        assert result is not None

    def test_missing_client_ip(self):
        mapper = self._mapper()
        result = mapper.map(
            {
                "id": "evt-3",
                "userId": "u1",
                "activityType": "ViewReport",
                "creationTime": "2024-01-15T10:00:00Z",
            }
        )
        assert "ClientIP" in result  # key must exist even if empty/None


# ── LivySessionMapper ─────────────────────────────────────────────────────────

class TestLivySessionMapper:
    def _mapper(self):
        from fabricla_connector.mappers import LivySessionMapper
        return LivySessionMapper()

    def test_happy_path(self):
        mapper = self._mapper()
        result = mapper.map(
            {
                "id": "session-1",
                "appId": "app-1",
                "state": "idle",
                "kind": "pyspark",
                "driverLogUrl": "https://example.com/log",
                "sparkUiUrl": "https://example.com/ui",
            },
            workspace_id="ws-1",
            item_id="nb-1",
            item_type="Notebook",
        )
        assert result["SessionId"] == "session-1"
        assert result["State"] == "idle"
        assert "TimeGenerated" in result

    def test_missing_urls(self):
        mapper = self._mapper()
        result = mapper.map(
            {"id": "session-2", "state": "starting"},
            workspace_id="ws-1",
            item_id="nb-1",
            item_type="Notebook",
        )
        assert result is not None
