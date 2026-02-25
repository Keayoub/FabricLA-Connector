# FabricLA-Connector: Microsoft Fabric to Azure Log Analytics Framework

A comprehensive **Python framework** that collects operational data from Microsoft Fabric REST APIs and ingests it into **Azure Log Analytics** for monitoring, analysis, and alerting.

## ✨ **Quick Start: One-Line Collection**

```python
from fabricla_connector import run_intelligent_monitoring_cycle

result = run_intelligent_monitoring_cycle(
    workspace_id="your-workspace-id",
    capacity_id="your-capacity-id"  # Optional
)
```

## 🚀 Quick Start

### **Install & Test Locally**
```bash
# Clone and install
git clone https://github.com/Keayoub/FabricLA-Connector.git
cd FabricLA-Connector
pip install -e .

# Test intelligent monitoring
python -c "from fabricla_connector import run_intelligent_monitoring_cycle; print('OK: Ready');"
```

### **⚙️ Environment Configuration (Centralized)**

This repository uses a **single centralized `.env.example`** file in the root folder for all configuration:

```bash
# Step 1: Copy the master .env.example to create your .env
cp .env.example .env

# Step 2: Copy to your working directories
cp .env notebooks/.env              # For notebook monitoring

# Step 3: Edit each .env with your specific values
```

**Why centralized?**
- ✅ **Single source of truth** - One file to maintain
- ✅ **No duplication** - Changes propagate from one place
- ✅ **Complete coverage** - All variables for all monitoring scenarios
- ✅ **Clear documentation** - Comprehensive comments and examples

The `.env.example` includes:
- Azure AD App Registration (Service Principal)
- Azure Monitor configuration (DCE, DCR, Log Analytics)
- Fabric workspace and capacity settings
- Stream names for all monitoring scenarios
- Authentication methods and debugging options

See the [Environment Configuration Guide](#2-configure-environment) below for detailed setup.

### **Authentication Setup**
```bash
# Simplest: Azure CLI login
az login

# Or set environment variables for service principal
export FABRIC_APP_ID="your-app-id"
export FABRIC_APP_SECRET="your-app-secret"  
export FABRIC_TENANT_ID="your-tenant-id"
```

### **🔧 Fabric Runtime Environment Setup**

For development environments that need to match Microsoft Fabric runtime specifications exactly, use the automated setup scripts:

```bash
# Create Fabric-compatible Python environment
cd setup
python setup_fabric_environment.py

# Or use Windows batch script
setup_fabric_environment.bat
```

These scripts automatically:
- Download official requirements from Microsoft Synapse Spark Runtime repository
- Create version-specific virtual environments (Runtime 1.2/1.3)
- Configure environment variables template
- Support both Python 3.10 (Fabric 1.2) and Python 3.11 (Fabric 1.3)

See [setup/README.md](setup/README.md) for detailed documentation.

## 📊 What This Framework Monitors

| **Data Source** | **Information Collected** | **Custom Table** | **Status** |
|-----------------|---------------------------|------------------|------------|
| **Pipelines & Dataflows** | Execution status, performance metrics, errors | `FabricPipelineRun_CL`, `FabricDataflowRun_CL` | ✅ Available |
| **Dataset Refresh** | Refresh operations, duration, failure analysis | `FabricDatasetRefresh_CL`, `FabricDatasetMetadata_CL` | ✅ Available |
| **User Activity** | Access patterns, security events, usage analytics | `FabricUserActivity_CL` | ✅ Available |
| **Capacity Metrics** | Resource utilization, workload distribution | `FabricCapacityMetrics_CL`, `FabricCapacityWorkloads_CL` | ✅ Available |
| **Spark Execution** | Spark applications, Livy sessions, logs, metrics | `FabricSparkApplications_CL`, `FabricSparkLogs_CL` | ✅ Available |
| **Workspace Configuration** | OAP settings, security policies, Git integration, compliance | `FabricWorkspaceConfig_CL` | 📓 Notebook only |
| **Access Permissions** | User roles, item permissions, capacity assignments | `FabricPermissions_CL` | 🔜 Planned |

## 🔧 Framework Components

### **Core Python Package** (`/src/fabricla_connector/`)
```python
# High-level workflows (one-line data collection)
from fabricla_connector.workflows import collect_and_ingest_pipeline_data_enhanced

result = collect_and_ingest_pipeline_data_enhanced(
    workspace_id="your-workspace-id",
    lookback_minutes=1440  # 24 hours
)

# Individual components for custom workflows
from fabricla_connector.api import FabricAPIClient
from fabricla_connector.collectors import PipelineCollector
from fabricla_connector.ingestion import FabricIngestion
```

### **Data Collection Notebooks** (`/notebooks/`)
- `framework_quickstart_example.ipynb` - Getting started guide
- `intelligent_monitoring_example.ipynb` - Intelligent monitoring with auto-detection
- `fabric_pipeline_dataflow_collector.ipynb` - Pipeline & dataflow monitoring
- `fabric_dataset_refresh_monitoring.ipynb` - Dataset refresh tracking
- `fabric_user_activity_monitoring.ipynb` - User activity analytics
- `fabric_capacity_utilization_monitoring.ipynb` - Capacity utilization monitoring
- `fabric_spark_monitoring.ipynb` - Spark application & session monitoring
- `workspace_config_monitoring.ipynb` - Workspace configuration and compliance
- `ama_gateway_deployment_guide.ipynb` - Azure Monitor Agent gateway setup
- `validate_environment.ipynb` - Environment validation and diagnostics

### **Infrastructure Deployment** (`/infra/`)
- **Bicep**: `bicep/main.bicep` - Log Analytics workspace + DCR + custom tables
- **Terraform**: `terraform/main.tf` - Complete infrastructure deployment

### **Development Tools** (`/tools/`)
- Local testing and package upload utilities
- See [tools/README.md](tools/README.md) for detailed documentation

## 📋 Complete Setup Guide

### **1. Deploy Infrastructure**

**Option A: Bicep**
```bash
az deployment group create \
  --resource-group your-rg \
  --template-file bicep/main.bicep \
  --parameters @bicep/params.json
```

**Option B: Terraform**  
```bash
cd terraform/
terraform init
terraform apply -var-file="terraform.tfvars"
```

### **2. Configure Environment**

**Copy and configure the environment file:**
```bash
# Copy the master .env.example from root to your working directory
cp .env.example .env

# For notebooks (main monitoring):
cp .env notebooks/.env

# Edit .env with your actual values
```

**Required environment variables** (see `.env.example` for complete list):
```bash
# Azure AD & Fabric
FABRIC_TENANT_ID=your-tenant-id
FABRIC_APP_ID=your-service-principal-id
FABRIC_APP_SECRET=your-service-principal-secret
FABRIC_WORKSPACE_ID=your-workspace-id

# Azure Monitor configuration (from infrastructure deployment)
AZURE_MONITOR_DCE_ENDPOINT=https://your-dce.monitor.azure.com
AZURE_MONITOR_DCR_IMMUTABLE_ID=dcr-xxxxxxxxxxxxxxxx
LOG_ANALYTICS_WORKSPACE_ID=your-workspace-id
```

> 💡 **Tip**: A single `.env.example` file in the root contains all configuration. Copy it to your working directory and customize as needed.

### **3. Start Monitoring**

**Framework Approach (Recommended):**
```python
from fabricla_connector import run_intelligent_monitoring_cycle

result = run_intelligent_monitoring_cycle(
    workspace_id="your-workspace-id",
    capacity_id="your-capacity-id"  # Optional
)
```

**Or use the enhanced full cycle for explicit control:**
```python
from fabricla_connector.workflows import run_full_monitoring_cycle_enhanced

result = run_full_monitoring_cycle_enhanced(
    workspace_id="your-workspace-id",
    capacity_id="your-capacity-id"
)
```

**Notebook Approach:**
- Upload notebooks to your Fabric workspace
- Configure authentication
- Execute based on your monitoring needs

## 🧪 Local Development

### **Build & Test Package**
```bash
# Test build only
python test_local_build.py --workspace-id YOUR_ID --environment-id YOUR_ID --skip-upload

# Build and upload to Fabric (staging)
python test_local_build.py --workspace-id YOUR_ID --environment-id YOUR_ID

# Build, upload, and auto-publish (immediate activation)
python test_local_build.py --workspace-id YOUR_ID --environment-id YOUR_ID --publish
```

See [tools/README.md](tools/README.md) for comprehensive testing and upload options.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│ Microsoft       │    │ FabricLA         │    │ Azure Log Analytics │
│ Fabric          │────│ Connector        │────│ Workspace           │
│ (REST APIs)     │    │ Framework        │    │ (Custom Tables)     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
              ┌──────▼──┐ ┌────▼───┐ ┌───▼────┐
              │ Fabric  │ │ Local  │ │ CI/CD  │
              │Notebooks│ │ Python │ │Pipeline│
              └─────────┘ └────────┘ └────────┘
```

## 📚 Documentation

- **[Local Testing Guide](tools/README.md)** - Development and upload tools
- **[Environment Setup Guide](docs/EnvironmentSetup.md)** - Fabric environment setup and dependency management
- **[Setup Scripts](setup/README.md)** - Automated Fabric runtime environment setup

## 🤝 Contributing

1. Clone the repository
2. Install in development mode: `pip install -e .`
3. Make changes and test locally
4. Use the local testing tools to validate

## 📄 License

MIT License - See LICENSE file for details

---