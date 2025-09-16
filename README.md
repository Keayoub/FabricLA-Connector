# FabricLA-Connector: Microsoft Fabric to Azure Log Analytics Framework

A comprehensive **Python framework** that collects operational data from Microsoft Fabric REST APIs and ingests it into **Azure Log Analytics** for monitoring, analysis, and alerting.

## 🚀 Quick Start

### **Install & Test Locally**
```bash
# Clone and install
git clone https://github.com/Keayoub/FabricLA-Connector.git
cd FabricLA-Connector
pip install -e .

# Test build and upload to Fabric
python test_local_build.py --workspace-id YOUR_WORKSPACE_ID --environment-id YOUR_ENV_ID
```

### **Authentication Setup**
```bash
# Simplest: Azure CLI login
az login

# Or set environment variables for service principal
export FABRIC_APP_ID="your-app-id"
export FABRIC_APP_SECRET="your-app-secret"  
export FABRIC_TENANT_ID="your-tenant-id"
```

## 📊 What This Framework Monitors

| **Data Source** | **Information Collected** | **Custom Table** |
|-----------------|---------------------------|------------------|
| **Pipelines & Dataflows** | Execution status, performance metrics, errors | `FabricPipelineRun_CL`, `FabricDataflowRun_CL` |
| **Dataset Refresh** | Refresh operations, duration, failure analysis | `FabricDatasetRefresh_CL`, `FabricDatasetMetadata_CL` |
| **User Activity** | Access patterns, security events, usage analytics | `FabricUserActivity_CL` |
| **Capacity Metrics** | Resource utilization, workload distribution | `FabricCapacityMetrics_CL`, `FabricCapacityWorkloads_CL` |

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
- `fabric_pipeline_dataflow_collector.ipynb` - Pipeline monitoring
- `fabric_dataset_refresh_monitoring.ipynb` - Dataset refresh tracking
- `fabric_user_activity_monitoring.ipynb` - User activity analytics
- `fabric_capacity_utilization_monitoring.ipynb` - Capacity monitoring

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
```bash
# Required environment variables
FABRIC_TENANT_ID=your-tenant-id
FABRIC_APP_ID=your-service-principal-id
FABRIC_APP_SECRET=your-service-principal-secret

# Azure Monitor configuration (from infrastructure deployment)
DCR_ENDPOINT_HOST=your-dce.monitor.azure.com
DCR_IMMUTABLE_ID=dcr-xxxxxxxxxxxxxxxx
```

### **3. Start Monitoring**

**Framework Approach (Recommended):**
```python
from fabricla_connector.workflows import run_full_monitoring_cycle

# Complete monitoring for all data sources
result = run_full_monitoring_cycle(
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
- **[Deployment Options](DEPLOYMENT_OPTIONS_GUIDE.md)** - Staging vs auto-publish
- **[Packaging Guide](PACKAGING_BEST_PRACTICES.md)** - Modern Python packaging

## 🤝 Contributing

1. Clone the repository
2. Install in development mode: `pip install -e .`
3. Make changes and test locally
4. Use the local testing tools to validate

## 📄 License

MIT License - See LICENSE file for details

---

**🚀 Ready to monitor your Microsoft Fabric environment?** Start with the Quick Start guide above!