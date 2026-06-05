"""
Unit tests for config.py validate_config() — format checks, GUID validation,
actionable error messages.
"""
import os
import pytest
from unittest.mock import patch


# ── helpers ──────────────────────────────────────────────────────────────────

def _env(**kwargs):
    """Build a minimal valid environment dict, overridable per test."""
    base = {
        "AZURE_MONITOR_DCE_ENDPOINT": "https://my-dce.eastus-1.ingest.monitor.azure.com",
        "AZURE_MONITOR_DCR_IMMUTABLE_ID": "dcr-" + "a" * 32,
        "AZURE_MONITOR_STREAM_NAME": "Custom-FabricPipeline_CL",
        "FABRIC_TENANT_ID": "tenant-id-value",
        "FABRIC_APP_ID": "app-id-value",
        "FABRIC_APP_SECRET": "secret-value",  # pragma: allowlist secret
        "FABRIC_WORKSPACE_ID": "00000000-0000-0000-0000-000000000001",
        "LOOKBACK_HOURS": "24",
        "CHUNK_SIZE": "1000",
        "MAX_RETRIES": "3",
    }
    base.update(kwargs)
    # Remove keys set to None so os.getenv returns the default
    return {k: v for k, v in base.items() if v is not None}


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    """Remove real env vars so tests are hermetic."""
    for key in list(os.environ.keys()):
        if key.startswith(("AZURE_", "FABRIC_", "LOOKBACK_", "CHUNK_", "MAX_")):
            monkeypatch.delenv(key, raising=False)


# ── happy path ────────────────────────────────────────────────────────────────

def test_valid_config_passes(monkeypatch):
    for k, v in _env().items():
        monkeypatch.setenv(k, v)
    from fabricla_connector.config import validate_config
    result = validate_config("all")
    assert result["valid"] is True
    assert result["missing_required"] == []
    assert result["format_errors"] == []


# ── missing required fields ───────────────────────────────────────────────────

def test_missing_dce_endpoint(monkeypatch):
    for k, v in _env(AZURE_MONITOR_DCE_ENDPOINT=None).items():
        monkeypatch.setenv(k, v)
    from fabricla_connector.config import validate_config
    result = validate_config("ingestion")
    assert result["valid"] is False
    assert any("dce_endpoint" in m for m in result["missing_required"])


def test_missing_dcr_id(monkeypatch):
    for k, v in _env(AZURE_MONITOR_DCR_IMMUTABLE_ID=None).items():
        monkeypatch.setenv(k, v)
    from fabricla_connector.config import validate_config
    result = validate_config("ingestion")
    assert result["valid"] is False
    assert any("dcr_immutable_id" in m for m in result["missing_required"])


def test_missing_stream_name(monkeypatch):
    for k, v in _env(AZURE_MONITOR_STREAM_NAME=None).items():
        monkeypatch.setenv(k, v)
    from fabricla_connector.config import validate_config
    result = validate_config("ingestion")
    assert result["valid"] is False
    assert any("stream_name" in m for m in result["missing_required"])


def test_missing_fabric_auth(monkeypatch):
    for k, v in _env(FABRIC_TENANT_ID=None, FABRIC_APP_ID=None, FABRIC_APP_SECRET=None).items():
        monkeypatch.setenv(k, v)
    from fabricla_connector.config import validate_config
    result = validate_config("fabric")
    assert result["valid"] is False
    assert len([m for m in result["missing_required"] if "fabric." in m]) == 3


# ── format validation ─────────────────────────────────────────────────────────

def test_bad_dce_url_format(monkeypatch):
    for k, v in _env(AZURE_MONITOR_DCE_ENDPOINT="not-a-url").items():
        monkeypatch.setenv(k, v)
    from fabricla_connector.config import validate_config
    result = validate_config("ingestion")
    assert result["valid"] is False
    assert any("dce_endpoint" in e for e in result["format_errors"])


def test_bad_dcr_id_format(monkeypatch):
    for k, v in _env(AZURE_MONITOR_DCR_IMMUTABLE_ID="wrong-format").items():
        monkeypatch.setenv(k, v)
    from fabricla_connector.config import validate_config
    result = validate_config("ingestion")
    assert result["valid"] is False
    assert any("dcr_immutable_id" in e for e in result["format_errors"])


def test_bad_workspace_guid(monkeypatch):
    for k, v in _env(FABRIC_WORKSPACE_ID="not-a-guid").items():
        monkeypatch.setenv(k, v)
    from fabricla_connector.config import validate_config
    result = validate_config("fabric")
    assert result["valid"] is False
    assert any("workspace_id" in e for e in result["format_errors"])


def test_valid_workspace_guid_passes(monkeypatch):
    for k, v in _env(FABRIC_WORKSPACE_ID="aabbccdd-eeff-0011-2233-445566778899").items():
        monkeypatch.setenv(k, v)
    from fabricla_connector.config import validate_config
    result = validate_config("fabric")
    assert not any("workspace_id" in e for e in result.get("format_errors", []))


def test_bad_lookback_hours(monkeypatch):
    for k, v in _env(LOOKBACK_HOURS="0").items():
        monkeypatch.setenv(k, v)
    from fabricla_connector.config import validate_config
    result = validate_config("fabric")
    assert result["valid"] is False
    assert any("lookback_hours" in e for e in result["format_errors"])


# ── error message quality ─────────────────────────────────────────────────────

def test_missing_error_messages_are_actionable(monkeypatch):
    for k, v in _env(AZURE_MONITOR_DCE_ENDPOINT=None).items():
        monkeypatch.setenv(k, v)
    from fabricla_connector.config import validate_config
    result = validate_config("ingestion")
    msg = result["missing_required"][0]
    # Must tell the user what format to use
    assert "https://" in msg or "expected" in msg.lower()


def test_format_error_messages_show_bad_value(monkeypatch):
    bad_value = "http://wrong-domain.com"
    for k, v in _env(AZURE_MONITOR_DCE_ENDPOINT=bad_value).items():
        monkeypatch.setenv(k, v)
    from fabricla_connector.config import validate_config
    result = validate_config("ingestion")
    assert any(bad_value in e for e in result["format_errors"])
