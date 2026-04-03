# FabricLA-Connector

> **Python v1.0.2** · Microsoft Fabric → Azure Log Analytics monitoring framework

Collects operational data from Microsoft Fabric REST APIs and ingests it into Azure Log Analytics via the Azure Monitor DCE/DCR pipeline. Supports local Python scripts, Fabric notebooks, and CI/CD.

## Quick Start

```bash
git clone https://github.com/Keayoub/FabricLA-Connector.git
cd FabricLA-Connector
pip install -e ".[dev]"
cp .env.example .env        # fill in your values
cp .env notebooks/.env      # for notebook runs
cp .env tests/.env          # for test runs
```

```python
from fabricla_connector import run_intelligent_monitoring_cycle

result = run_intelligent_monitoring_cycle(
    workspace_id="your-workspace-id",
    capacity_id="your-capacity-id"   # optional
)
```

## What Gets Monitored

| Data Source | Log Analytics Table | Status |
|-------------|---------------------|--------|
| Pipelines & Dataflows | `FabricPipelineRun_CL`, `FabricDataflowRun_CL` | ✅ |
| Dataset Refresh | `FabricDatasetRefresh_CL`, `FabricDatasetMetadata_CL` | ✅ |
| User Activity | `FabricUserActivity_CL` | ✅ |
| Capacity Workloads | `FabricCapacityMetrics_CL` | ✅ |
| Spark / Livy Sessions | `FabricSparkApplications_CL`, `FabricSparkLogs_CL` | ✅ |
| Workspace Configuration | `FabricWorkspaceConfig_CL` | 📓 Notebook only |
| Access Permissions | `FabricPermissions_CL` | 🔜 Planned |

DCR stream names follow `Custom-Fabric<Type>_CL` → table `Fabric<Type>_CL`.

## Architecture

```
Fabric REST APIs
     ↓
collectors/    — pull raw data
     ↓
mappers/       — transform to Log Analytics schema
     ↓
ingestion/     — chunk (1 MB limit), retry, POST to Azure Monitor DCE
```

`workflows.py` is the top-level orchestrator. Most callers use workflow functions directly rather than touching lower layers.

## Environment Variables

All config comes from a single `.env.example` at the repo root.

| Group | Key Variables |
|-------|--------------|
| Fabric auth | `FABRIC_TENANT_ID`, `FABRIC_APP_ID`, `FABRIC_APP_SECRET` |
| Fabric target | `FABRIC_WORKSPACE_ID`, `FABRIC_CAPACITY_ID` |
| Azure Monitor | `AZURE_MONITOR_DCE_ENDPOINT`, `AZURE_MONITOR_DCR_IMMUTABLE_ID` |
| Stream names | `AZURE_MONITOR_STREAM_LIVY_SESSION`, `AZURE_MONITOR_STREAM_SPARK_LOGS`, … |
| Collection | `LOOKBACK_HOURS` (default 24), `CHUNK_SIZE` (default 1000) |

Auth precedence for ingestion: env vars (`AZURE_CLIENT_*`) → Managed Identity → VS Code → Azure CLI → PowerShell. For local testing, `az login` is the simplest path.

## Setup Guide

### 1. Deploy Infrastructure

**Bicep**
```bash
cd infra/bicep
az deployment group create \
  --resource-group your-rg \
  --template-file main.bicep
```

**Terraform**
```bash
cd infra/terraform
terraform init
terraform apply -var-file="terraform.tfvars"
# Get DCE endpoint and DCR immutable ID:
terraform output -json
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values:
#   FABRIC_TENANT_ID, FABRIC_APP_ID, FABRIC_APP_SECRET
#   FABRIC_WORKSPACE_ID
#   AZURE_MONITOR_DCE_ENDPOINT, AZURE_MONITOR_DCR_IMMUTABLE_ID
```

### 3. Run Monitoring

**Intelligent cycle (recommended)** — auto-detects what Fabric already monitors and collects only the gaps:
```python
from fabricla_connector import run_intelligent_monitoring_cycle
result = run_intelligent_monitoring_cycle(workspace_id="...", capacity_id="...")
```

**Explicit full cycle:**
```python
from fabricla_connector.workflows import run_full_monitoring_cycle_enhanced
result = run_full_monitoring_cycle_enhanced(workspace_id="...", capacity_id="...")
```

**Individual sources:**
```python
from fabricla_connector import (
    collect_and_ingest_pipeline_data,
    collect_and_ingest_dataset_refreshes,
    collect_and_ingest_capacity_utilization,
    collect_and_ingest_user_activity,
    collect_and_ingest_spark_applications,
    comprehensive_spark_monitoring,
)
```

**CLI entry point:**
```bash
fabric-monitor
```

## Notebooks (`/notebooks/`)

Upload to your Fabric workspace and configure auth before running.

| Notebook | Purpose |
|----------|---------|
| `validate_environment.ipynb` | First-run connectivity check |
| `framework_quickstart_example.ipynb` | Getting started guide |
| `intelligent_monitoring_example.ipynb` | Intelligent monitoring with auto-detection |
| `fabric_pipeline_dataflow_collector.ipynb` | Pipeline & dataflow monitoring |
| `fabric_dataset_refresh_monitoring.ipynb` | Dataset refresh tracking |
| `fabric_user_activity_monitoring.ipynb` | User activity analytics |
| `fabric_capacity_utilization_monitoring.ipynb` | Capacity utilization monitoring |
| `fabric_spark_monitoring.ipynb` | Spark application & Livy session monitoring |
| `workspace_config_monitoring.ipynb` | Workspace configuration and compliance |
| `ama_gateway_deployment_guide.ipynb` | Azure Monitor Agent gateway setup |

## Development

```bash
# Install with dev extras
pip install -e ".[dev]"

# Run all tests
pytest

# Unit tests only (skip integration/slow)
pytest -m "not integration and not slow"

# Coverage
pytest --cov=src

# Lint / format / type-check
flake8 src/
black src/
mypy src/
```

Tests require `tests/.env` (copy from `.env.example`). By default all tests run with mocked APIs (`USE_MOCK_API=true`).

### Fabric Runtime Environments

To match Microsoft Fabric runtime specs locally:

```bash
cd setup
python setup_fabric_environment.py
# Runtime 1.2 → Python 3.10 + Spark 3.4 → .fabric-env-1.2/
# Runtime 1.3 → Python 3.11 + Spark 3.5 → .fabric-env-1.3/

# Activate on Windows:
.fabric-env-1.3\Scripts\activate.bat
```

### Build & Upload to Fabric

```bash
# Validate package build only
python tools/test_local_build.py --workspace-id <WS_ID> --environment-id <ENV_ID> --skip-upload

# Build + upload (staging)
python tools/test_local_build.py --workspace-id <WS_ID> --environment-id <ENV_ID>

# Build + upload + publish (immediate activation)
python tools/test_local_build.py --workspace-id <WS_ID> --environment-id <ENV_ID> --publish
```

Auth for upload tools: `--token` → service principal (`--client-id/--client-secret/--tenant-id`) → `--use-default-credential`.

### Adding a New Data Source

1. Create `collectors/<name>.py` extending `BaseCollector`, implement `collect()`.
2. Create `mappers/<name>.py` with a mapper class.
3. Add a workflow function in `workflows.py` wiring them via `AzureMonitorIngestionClient`.
4. Export from `collectors/__init__.py`, `mappers/__init__.py`, and `__init__.py`.

## Security

- Secrets are never logged. Token fragments are not emitted at any log level.
- All `subprocess` calls use `shell=False`.
- GUID inputs are validated at collector instantiation.
- Pre-commit hooks enforce `nbstripout` (strips notebook outputs), `detect-secrets`, and `flake8`.
- `terraform.tfvars` is gitignored — never committed.

## Troubleshooting

| Symptom | Likely cause |
|---------|-------------|
| "Missing required environment variables" | `.env` not loaded or wrong variable name |
| Upload fails with 4xx | Wrong DCR immutable ID, stream name mismatch, or missing "Monitoring Metrics Publisher" role |
| No data in Log Analytics | Wait 2–5 min; table name must include `_CL` suffix |
| `notebookutils` ImportError | Running locally, not in Fabric — expected, handled by `is_running_in_fabric()` |
| Auth failure on upload | Service principal needs `Fabric.ReadWrite.All` and workspace membership |

## Documentation

- [Environment Setup Guide](docs/EnvironmentSetup.md)
- [Setup Scripts](setup/README.md)
- [Tools Reference](tools/README.md)

## Contributing

```bash
pip install -e ".[dev]"
pre-commit install   # enables nbstripout, detect-secrets, flake8 hooks
```

1. Branch from `main`
2. Make changes and run `pytest`
3. Open a pull request

## License

MIT — see [LICENSE](LICENSE)
