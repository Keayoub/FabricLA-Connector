# Copilot Instructions

## Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_collectors.py

# Run a single test by name
pytest tests/test_collectors.py::TestPipelineDataCollector::test_collect_pipeline_runs_success

# Run only unit tests (skip integration/slow)
pytest -m "not integration and not slow"

# Run with coverage
pytest --cov=src

# Lint / format / type check
flake8 src/
black src/
mypy src/
```

Tests require `tests/.env` — copy `.env.example` to `tests/.env` and fill in values. By default, tests run with mocked APIs (`USE_MOCK_API=true`). The `conftest.py` auto-loads `tests/.env` via `python-dotenv`.

## Architecture

The package (`src/fabricla_connector/`) is a strict 3-layer pipeline:

```
Fabric REST APIs  (api/fabric_client.py + api/auth.py)
       ↓
collectors/       pull raw data; one class per source, each extends BaseCollector
       ↓
mappers/          transform raw API responses into Log Analytics schema (flat dicts)
       ↓
ingestion/        chunk to ≤1 MB, exponential-backoff retry, POST to Azure Monitor DCE
```

**`workflows.py`** is the only public entry point callers should use. It composes collectors + mappers + `AzureMonitorIngestionClient` into named functions. Do not call lower layers directly from notebooks or external code.

**`monitoring_detection.py`** detects which data Microsoft Fabric already monitors natively (via its built-in workspace monitoring Eventhouse), then produces per-source recommendations. `run_intelligent_monitoring_cycle()` calls this automatically so you never duplicate built-in telemetry.

**`config.py`** exposes configuration through four typed helpers:
- `get_config()` — all general config
- `get_ingestion_config()` — DCE endpoint, DCR ID, stream name
- `get_fabric_config()` — workspace/capacity IDs, auth
- `get_monitoring_config()` — lookback hours, chunk size, strategy

Config precedence: **env vars → Fabric Key Vault (when inside Fabric) → defaults**.

**Dual-environment detection**: `is_running_in_fabric()` returns `True` when `notebookutils` is importable (inside a Fabric notebook). Locally, all secrets come from `.env`.

## Key Conventions

### Collectors

- All collectors extend `BaseCollector` and implement `collect() -> Iterator[Dict[str, Any]]`.
- The `client` property is **lazy-loaded** via a property — authentication is deferred until first HTTP call, so collectors are cheap to instantiate.
- Collectors are usable directly as iterators: `for record in collector:`.
- Available collectors and what they call:

| Class | Data source | Notable constraint |
|-------|-------------|-------------------|
| `PipelineDataCollector` | Pipeline runs, Dataflow runs, Activity run details | — |
| `DatasetRefreshCollector` | Dataset refresh history + metadata | — |
| `CapacityUtilizationCollector` | Workload state & max memory % | Workload state only; for CU% time-series use Azure Monitor diagnostics |
| `UserActivityCollector` | Tenant-wide activity events | Requires `Tenant.Read.All`; max 28-day lookback; 200 req/hour limit |
| `AccessPermissionsCollector` | Workspace settings, capacity, security | Tries admin endpoint first, falls back to regular on 403 |
| Spark functions (`collect_livy_sessions_*`, `collect_spark_logs`, etc.) | Spark/Livy sessions, logs, metrics, resource usage | 10 free functions in `collectors/__init__.py` |

### Mappers

Each mapper has a `map()` method (signature varies). Mappers always output flat dicts with a `TimeGenerated` field (ISO UTC) for Log Analytics:

| Class | Output fields (key ones) |
|-------|--------------------------|
| `PipelineRunMapper` | WorkspaceId, PipelineId, RunId, Status, DurationMs, InvokeType, FailureReason |
| `ActivityRunMapper` | ActivityName, ActivityType, DataRead, DataWritten, RecordsProcessed, ErrorCode |
| `DataflowRunMapper` | Same shape as PipelineRunMapper |
| `DatasetRefreshMapper` | DatasetId, RefreshId, Status, DurationMs, InvokeType, FailureReason |
| `DatasetMetadataMapper` | DatasetName, Type, CreatedDate, CreatedBy, ModifiedBy |
| `CapacityMetricMapper` | CapacityId, WorkloadName, WorkloadState, MaxMemoryPercentage |
| `UserActivityMapper` | UserId, Activity, Operation, IsSuccess, ClientIP, ArtifactName |
| `LivySessionMapper` | SessionId, ApplicationId, ItemType, State, DriverLogUrl, SparkUiUrl |
| `SparkResourceMapper` | Three static methods: `map_driver()`, `map_executor()`, `map_aggregate()` — all include CpuUsagePercent, MemoryUsedMB, GcTimeMs, ShuffleReadMB |

### Adding a new data source

1. `collectors/<name>.py` — extend `BaseCollector`, implement `collect()`
2. `mappers/<name>.py` — extend `BaseMapper`, define `map()` returning a flat dict with `TimeGenerated`
3. `workflows.py` — add a `collect_and_ingest_<name>()` function using `AzureMonitorIngestionClient`
4. Export from `collectors/__init__.py`, `mappers/__init__.py`, and the top-level `__init__.py`
5. Add a DCR stream with name `Custom-Fabric<Type>_CL` → table `Fabric<Type>_CL`

### Authentication

**Fabric API** (`api/auth.py`):
- `get_fabric_token()` — primary entry point; tries Fabric workspace identity first, falls back to MSAL client-credentials with `FABRIC_APP_ID` + `FABRIC_APP_SECRET`
- `get_credentials_fabric_aware()` — returns `(tenant_id, client_id, client_secret, use_fabric_auth)`; reads from Fabric Key Vault when in Fabric, otherwise from env vars

**Azure Monitor ingestion**: uses `DefaultAzureCredential` chain — env vars (`AZURE_CLIENT_*`) → Managed Identity → VS Code → Azure CLI → PowerShell. For local dev, `az login` is the simplest path.

**Upload/deploy tools** accept three auth methods in priority order: `--token` (bearer) → `--client-id/--client-secret/--tenant-id` → `--use-default-credential`.

### Exception handling

Custom exception hierarchy in `api/exceptions.py`:
- `FabricAPIException` — base; carries `status_code` and `response_text`
- `FabricAuthenticationError` — 401
- `FabricAuthorizationError` — 403
- `FabricResourceNotFoundError` — 404
- `FabricRateLimitError` — 429; carries `retry_after`

Patterns used throughout: graceful degradation (collectors return `[]` on 404), admin-endpoint fallback on 403, rate-limit extraction from `Retry-After` header, exponential backoff in `ingestion/retry.py`.

### Ingestion details

- `ingestion/batch.py`: `split_by_size()` keeps batches under **1 MB** (950 KB working limit with `chunk_records_by_size()`); `estimate_payload_size()` measures JSON serialization size.
- `ingestion/retry.py`: `RetryPolicy` class; retries on 429 / 5xx / timeout / connection errors; non-retryable errors fail immediately.
- `AzureMonitorIngestionClient.ingest()` returns `{ingested_count, failed_count, status}`.

### Schema validation

`schema_validator.py` provides per-source `validate_*_schema()` functions (notebook, semantic model, workspace permissions, datamart, deployment pipeline, app analytics, import monitoring, eventhouse, lakehouse, gateway, report analytics). The generic `validate_payload()` just asserts the input is a list.

### Utility functions (`utils.py`)

Key helpers used across the codebase:
- `iso_now()` / `to_iso()` — UTC ISO strings with `Z` suffix
- `parse_iso()` — handles `Z`, `+00:00`, and timezone-naive strings
- `within_lookback_minutes(start_iso, end_iso, lookback_minutes)` — uses `end_iso` (falls back to `start_iso`) compared against `now(UTC) - timedelta(minutes)`
- `safe_get(d, *keys, default)` — nested dict access without KeyError
- `truncate_string(s, max_length)` — for Log Analytics field limits
- `clean_column_name(name)` — strips non-alphanumeric/underscore chars for LA column names
- `validate_workspace_id(id)` — regex UUID validation
- `create_time_window(lookback_hours)` — returns `(start_iso, end_iso)` tuple

### Telemetry (`telemetry.py`)

- `log_event(event_type, **kwargs)` — emits a structured JSON log line via `logging`
- `timed_event(event_type, **kwargs)` — context manager; logs the event with `elapsed_ms` on exit

```python
from fabricla_connector.telemetry import log_event, timed_event

log_event("collection_started", source="pipeline", workspace_id=wid)

with timed_event("ingestion_chunk", chunk=1, records=500, stream="Custom-FabricPipeline_CL"):
    client.upload(...)  # elapsed_ms logged automatically
```

### Monitoring strategy

`FABRIC_MONITORING_STRATEGY` env var (or the `strategy` parameter) controls collection scope:
- `auto` *(default)* — uses `WorkspaceMonitoringDetector` recommendations
- `full` — always collect everything
- `complement` — only collect sources where `conflict_level == "none"` (safe alongside built-in monitoring)
- `minimal` — pipeline execution + dataflow execution + capacity utilization only

## Workflow Functions Reference

All callers should import from `fabricla_connector.workflows` (or the top-level package):

**Core collect-and-ingest:**
- `collect_and_ingest_pipeline_data(workspace_id, lookback_hours, custom_config)`
- `collect_and_ingest_dataset_refreshes(workspace_id, lookback_hours, custom_config)`
- `collect_and_ingest_capacity_utilization(capacity_id, lookback_hours, custom_config)`
- `collect_and_ingest_user_activity(workspace_id, lookback_hours, custom_config)`

**Enhanced:**
- `collect_and_ingest_pipeline_data_enhanced(workspace_id, pipeline_item_ids, lookback_hours, collect_activity_runs, enable_troubleshooting, custom_config)`
- `collect_and_ingest_spark_applications/logs/metrics/jobs/notebooks/git_integration/onelake_storage()`

**Intelligent monitoring (recommended entry points):**
- `run_intelligent_monitoring_cycle()` — auto-detects built-in Fabric monitoring, collects only gaps
- `run_full_monitoring_cycle_intelligent()` — comprehensive with intelligent decisions
- `run_complementary_monitoring_cycle()` — safe alongside Microsoft native monitoring
- `run_minimal_monitoring_cycle()` — core operational data only

**Utility:**
- `validate_and_test_configuration()` — validates all env vars and tests auth
- `check_workspace_monitoring_status(workspace_id)` — returns detection result
- `get_collection_recommendations(workspace_id)` — returns strategy dict

**Phase 2/3 (not yet fully implemented):**
`collect_and_ingest_access_permissions`, `collect_and_ingest_semantic_models`, `collect_and_ingest_real_time_intelligence`, `run_comprehensive_monitoring_cycle`, and others — present in code, marked for future phases.

## Environment Variables

See `.env.example` for the full list. Key groups:

| Group | Variables |
|-------|-----------|
| Fabric auth | `FABRIC_TENANT_ID`, `FABRIC_APP_ID`, `FABRIC_APP_SECRET` |
| Azure subscription | `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP` |
| Fabric target | `FABRIC_WORKSPACE_ID`, `FABRIC_CAPACITY_IDS`, `FABRIC_LAKEHOUSE_ID` |
| Azure Monitor | `AZURE_MONITOR_DCE_ENDPOINT`, `AZURE_MONITOR_DCR_IMMUTABLE_ID`, `LOG_ANALYTICS_WORKSPACE_ID` |
| Spark streams | `AZURE_MONITOR_STREAM_LIVY_SESSION`, `AZURE_MONITOR_STREAM_SPARK_LOGS`, `AZURE_MONITOR_STREAM_HISTORY_METRICS`, `AZURE_MONITOR_STREAM_RESOURCE_USAGE` |
| Governance streams | `AZURE_MONITOR_STREAM_TENANT_SETTINGS`, `AZURE_MONITOR_STREAM_GOVERNANCE_EVENTS` |
| Key Vault | `AZURE_KEY_VAULT_URI`, `AZURE_KEY_VAULT_SECRET_NAME` |
| Collection tuning | `FABRIC_LOOKBACK_HOURS` (24), `CHUNK_SIZE` (1000), `FABRIC_METRICS_INTERVAL_MINUTES` (15) |
| Monitoring strategy | `FABRIC_MONITORING_STRATEGY` (auto/full/complement/minimal) |
| Auth method | `AUTH_METHOD` (AzureCLI / ManagedIdentity / ServicePrincipal) |
| Logging | `LOG_LEVEL` (INFO), `DEBUG_MODE` (false), `LOG_FILE_PATH` |

## Security Conventions

- **Never log token fragments.** `auth.py` must not emit any part of a bearer token at any log level.
- **All `subprocess` calls use `shell=False`.** Pass argument lists, never shell strings.
- **GUID inputs are validated at collector instantiation.** `BaseCollector.__init__` calls `validate_workspace_id()` from `utils.py`; `CapacityUtilizationCollector` validates `capacity_id` separately. Raise `ValueError` on invalid format.
- **Bare `except:` is banned.** Always catch a specific exception type (e.g., `except Exception as e:`).
- **Collector stubs in `collectors/__init__.py`** that are not yet implemented must be `_NotImplementedCollector` subclasses that raise `NotImplementedError`, not `None` assignments.
- **Pre-commit hooks** (`.pre-commit-config.yaml`): `nbstripout` (strips notebook outputs before commit), `detect-secrets`, `detect-private-key`, `flake8`. Install once with `pre-commit install`.
- **`terraform.tfvars` is gitignored** and must never be committed — it contains real infrastructure IDs.

## Deployment

```bash
# Validate config and test connectivity
fabric-monitor validate
fabric-monitor validate --ingestion   # ingestion config only
fabric-monitor validate --fabric      # Fabric auth config only

# Build wheel only (validate package)
python tools/test_local_build.py --workspace-id <WS_ID> --environment-id <ENV_ID> --skip-upload

# Build + upload to Fabric staging (manual publish required)
python tools/test_local_build.py --workspace-id <WS_ID> --environment-id <ENV_ID>

# Build + upload + auto-publish (immediate activation)
python tools/test_local_build.py --workspace-id <WS_ID> --environment-id <ENV_ID> --publish

# Upload existing wheel directly
python tools/upload_wheel_to_fabric.py --workspace-id <WS_ID> --environment-id <ENV_ID> \
  --file dist/fabricla_connector-1.0.2-py3-none-any.whl --use-default-credential
```

The CI pipeline (`.github/workflows/fabric-deployment.yml`) builds on every push to `main`/`develop`. Pushes to `main` and version tags (`v*`) auto-add `--publish` for immediate activation; `develop` stages only.

**Versioning / release automation** (`scripts/release.ps1` or `.bat`):
- Updates version in `pyproject.toml`, `__init__.py`, `README.md`
- Commits with `"Bump version to X.Y.Z"`, creates git tag `vX.Y.Z`
- Use `-Push` flag to push and `-Build` to validate build

## Fabric Item Creation Tools

`tools/` includes scripts to create Fabric items via REST API. All support the same three auth methods and a `--dry-run` flag:

```bash
# Create a data pipeline
python tools/create_fabric_pipeline.py --workspace-id <WS_ID> --pipeline-file tools/samples/sample_pipeline.json --use-default-credential

# Create a warehouse (DW100c=small, DW200c=medium, DW400c=large)
python tools/create_fabric_warehouse.py --workspace-id <WS_ID> --size medium --use-default-credential

# Create a Dataflow Gen2
python tools/create_fabric_dataflow_gen2.py --workspace-id <WS_ID> --mashup-file tools/samples/sample_mashup.pq --name "My ETL" --use-default-credential
```

Auth precedence for all tools: `--token` → `--client-id/--client-secret/--tenant-id` → `--use-default-credential`.

## Fabric-Compatible Local Environments

```bash
cd setup && python setup_fabric_environment.py
# Runtime 1.2 → Python 3.10 + Spark 3.4 → .fabric-env-1.2/
# Runtime 1.3 → Python 3.11 + Spark 3.5 → .fabric-env-1.3/  (recommended)
```

Activate on Windows: `.fabric-env-1.3\Scripts\activate.bat`

The package **requires Python ≥ 3.11**. Key dependency constraints to preserve at all times:
- `numpy <2.0.0` (shared runtime compatibility)
- `pandas >=2.2.0, <2.3.0` (keeps numpy <2 constraint)
- `fsspec <=2024.3.1` (datasets 2.19.x compatibility)
- `PyJWT <3.0.0`, `filelock <3.12`

## Troubleshooting

| Symptom | Cause |
|---------|-------|
| "Missing required environment variables" | `.env` not loaded or wrong variable name |
| "Upload failed with 4xx" | Wrong DCR immutable ID, stream name mismatch, or missing "Monitoring Metrics Publisher" role |
| No data in Log Analytics | Wait 2–5 min; table name must include `_CL` suffix |
| `notebookutils` ImportError | Running locally — expected; handled by `is_running_in_fabric()` |
| Auth failure on upload | Service principal needs `Fabric.ReadWrite.All` and workspace membership |
| 403 on permissions collector | Falls back automatically; admin endpoint needs tenant-admin scope |
| `UserActivityCollector` returns empty | Check `Tenant.Read.All` scope; lookback must be ≤28 days and within same day |
