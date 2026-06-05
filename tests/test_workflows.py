"""
Unit tests for key workflow functions — mocked collectors and ingestion.
Tests orchestration logic, error isolation, and parallel execution.
"""
import pytest
from unittest.mock import patch, MagicMock


WORKSPACE_ID = "00000000-0000-0000-0000-000000000001"
CAPACITY_ID  = "00000000-0000-0000-0000-000000000002"

_SUCCESS_RESULT = {
    "status": "success",
    "collected_count": 10,
    "total_records": 10,
    "ingestion_result": {"ingested_count": 10, "failed_count": 0},
}
_ERROR_RESULT = {"status": "error", "message": "API timeout", "collected_count": 0}


@pytest.fixture(autouse=True)
def _import_guard():
    try:
        import fabricla_connector.workflows  # noqa: F401
    except ImportError as exc:
        pytest.skip(f"fabricla_connector not installed: {exc}")


# ── _run_parallel ─────────────────────────────────────────────────────────────

class TestRunParallel:
    def test_all_succeed(self):
        from fabricla_connector.workflows import _run_parallel
        tasks = [
            ("a", lambda: {"status": "success", "val": 1}),
            ("b", lambda: {"status": "success", "val": 2}),
        ]
        results = _run_parallel(tasks)
        assert results["a"]["val"] == 1
        assert results["b"]["val"] == 2

    def test_one_failure_does_not_block_others(self):
        from fabricla_connector.workflows import _run_parallel

        def fail():
            raise RuntimeError("boom")

        tasks = [
            ("ok", lambda: {"status": "success"}),
            ("bad", fail),
        ]
        results = _run_parallel(tasks)
        assert results["ok"]["status"] == "success"
        assert results["bad"]["status"] == "error"
        assert "boom" in results["bad"]["error"]

    def test_returns_all_keys(self):
        from fabricla_connector.workflows import _run_parallel
        tasks = [(f"task_{i}", lambda i=i: {"n": i}) for i in range(5)]
        results = _run_parallel(tasks)
        assert set(results.keys()) == {f"task_{i}" for i in range(5)}


# ── run_full_monitoring_cycle_enhanced ────────────────────────────────────────

class TestRunFullMonitoringCycleEnhanced:
    @patch("fabricla_connector.workflows.collect_and_ingest_user_activity")
    @patch("fabricla_connector.workflows.collect_and_ingest_dataset_refreshes")
    @patch("fabricla_connector.workflows.collect_and_ingest_pipeline_data")
    def test_all_collectors_called(self, mock_pipeline, mock_dataset, mock_user):
        mock_pipeline.return_value = _SUCCESS_RESULT
        mock_dataset.return_value = _SUCCESS_RESULT
        mock_user.return_value = _SUCCESS_RESULT

        from fabricla_connector.workflows import run_full_monitoring_cycle_enhanced
        result = run_full_monitoring_cycle_enhanced(workspace_id=WORKSPACE_ID)

        mock_pipeline.assert_called_once()
        mock_dataset.assert_called_once()
        mock_user.assert_called_once()
        assert result["total_collected"] == 30

    @patch("fabricla_connector.workflows.collect_and_ingest_capacity_utilization")
    @patch("fabricla_connector.workflows.collect_and_ingest_user_activity")
    @patch("fabricla_connector.workflows.collect_and_ingest_dataset_refreshes")
    @patch("fabricla_connector.workflows.collect_and_ingest_pipeline_data")
    def test_capacity_only_called_when_capacity_id_given(
        self, mock_pipeline, mock_dataset, mock_user, mock_capacity
    ):
        for m in (mock_pipeline, mock_dataset, mock_user, mock_capacity):
            m.return_value = _SUCCESS_RESULT

        from fabricla_connector.workflows import run_full_monitoring_cycle_enhanced
        result = run_full_monitoring_cycle_enhanced(workspace_id=WORKSPACE_ID, capacity_id=CAPACITY_ID)

        mock_capacity.assert_called_once()
        assert result["capacity_utilization"]["status"] == "success"

    @patch("fabricla_connector.workflows.collect_and_ingest_capacity_utilization")
    @patch("fabricla_connector.workflows.collect_and_ingest_user_activity")
    @patch("fabricla_connector.workflows.collect_and_ingest_dataset_refreshes")
    @patch("fabricla_connector.workflows.collect_and_ingest_pipeline_data")
    def test_capacity_skipped_without_capacity_id(
        self, mock_pipeline, mock_dataset, mock_user, mock_capacity
    ):
        for m in (mock_pipeline, mock_dataset, mock_user):
            m.return_value = _SUCCESS_RESULT

        from fabricla_connector.workflows import run_full_monitoring_cycle_enhanced
        result = run_full_monitoring_cycle_enhanced(workspace_id=WORKSPACE_ID)

        mock_capacity.assert_not_called()
        assert result["capacity_utilization"]["status"] == "skipped"

    @patch("fabricla_connector.workflows.collect_and_ingest_user_activity")
    @patch("fabricla_connector.workflows.collect_and_ingest_dataset_refreshes")
    @patch("fabricla_connector.workflows.collect_and_ingest_pipeline_data")
    def test_one_error_sets_partial_status(self, mock_pipeline, mock_dataset, mock_user):
        mock_pipeline.return_value = _ERROR_RESULT
        mock_dataset.return_value = _SUCCESS_RESULT
        mock_user.return_value = _SUCCESS_RESULT

        from fabricla_connector.workflows import run_full_monitoring_cycle_enhanced
        result = run_full_monitoring_cycle_enhanced(workspace_id=WORKSPACE_ID)

        assert result["overall_status"] == "partial"

    @patch("fabricla_connector.workflows.collect_and_ingest_user_activity")
    @patch("fabricla_connector.workflows.collect_and_ingest_dataset_refreshes")
    @patch("fabricla_connector.workflows.collect_and_ingest_pipeline_data")
    def test_exception_in_collector_sets_partial(self, mock_pipeline, mock_dataset, mock_user):
        mock_pipeline.side_effect = RuntimeError("network error")
        mock_dataset.return_value = _SUCCESS_RESULT
        mock_user.return_value = _SUCCESS_RESULT

        from fabricla_connector.workflows import run_full_monitoring_cycle_enhanced
        result = run_full_monitoring_cycle_enhanced(workspace_id=WORKSPACE_ID)

        assert result["overall_status"] == "partial"
        assert result["pipeline_data"]["status"] == "error"


# ── run_operational_monitoring_cycle ─────────────────────────────────────────

class TestRunOperationalMonitoringCycle:
    @patch("fabricla_connector.workflows.collect_and_ingest_git_integration")
    @patch("fabricla_connector.workflows.collect_and_ingest_notebooks")
    @patch("fabricla_connector.workflows.collect_and_ingest_spark_jobs")
    @patch("fabricla_connector.workflows.collect_and_ingest_onelake_storage")
    def test_all_operational_collectors_called(
        self, mock_onelake, mock_spark, mock_nb, mock_git
    ):
        for m in (mock_onelake, mock_spark, mock_nb, mock_git):
            m.return_value = _SUCCESS_RESULT

        from fabricla_connector.workflows import run_operational_monitoring_cycle
        result = run_operational_monitoring_cycle(workspace_id=WORKSPACE_ID)

        for m in (mock_onelake, mock_spark, mock_nb, mock_git):
            m.assert_called_once()
        assert result["total_collected"] == 40

    @patch("fabricla_connector.workflows.collect_and_ingest_git_integration")
    @patch("fabricla_connector.workflows.collect_and_ingest_notebooks")
    @patch("fabricla_connector.workflows.collect_and_ingest_spark_jobs")
    @patch("fabricla_connector.workflows.collect_and_ingest_onelake_storage")
    def test_partial_failure_isolation(
        self, mock_onelake, mock_spark, mock_nb, mock_git
    ):
        mock_onelake.return_value = _SUCCESS_RESULT
        mock_spark.side_effect = ConnectionError("timeout")
        mock_nb.return_value = _SUCCESS_RESULT
        mock_git.return_value = _SUCCESS_RESULT

        from fabricla_connector.workflows import run_operational_monitoring_cycle
        result = run_operational_monitoring_cycle(workspace_id=WORKSPACE_ID)

        assert result["overall_status"] == "partial"
        assert result["spark_jobs"]["status"] == "error"
        assert result["onelake_storage"]["status"] == "success"


# ── validate_and_test_configuration ──────────────────────────────────────────

class TestValidateAndTestConfiguration:
    @patch("fabricla_connector.workflows.get_fabric_token")
    @patch("fabricla_connector.workflows.validate_config")
    def test_returns_dict_with_status(self, mock_validate, mock_token):
        mock_validate.return_value = {
            "valid": True,
            "missing_required": [],
            "missing_optional": [],
            "format_errors": [],
            "environment": "local",
            "fabric_available": False,
        }
        mock_token.return_value = "fake-token"

        from fabricla_connector.workflows import validate_and_test_configuration
        result = validate_and_test_configuration()

        assert isinstance(result, dict)

    @patch("fabricla_connector.workflows.get_fabric_token")
    @patch("fabricla_connector.workflows.validate_config")
    def test_invalid_config_returns_error(self, mock_validate, mock_token):
        mock_validate.return_value = {
            "valid": False,
            "missing_required": ["ingestion.dce_endpoint — expected: https://..."],
            "missing_optional": [],
            "format_errors": [],
            "environment": "local",
            "fabric_available": False,
        }

        from fabricla_connector.workflows import validate_and_test_configuration
        result = validate_and_test_configuration()

        assert isinstance(result, dict)
