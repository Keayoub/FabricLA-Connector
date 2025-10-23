# FabricLA-Connector: Microsoft Fabric to Azure Log Analytics Framework

A comprehensive **Python framework** that collects operational data from Microsoft Fabric REST APIs and ingests it into **Azure Log Analytics** for monitoring, analysis, and alerting.

## âœ¨ **NEW: Intelligent Monitoring with Smart Detection**

The framework now includes **intelligent monitoring capabilities** that automatically detect Microsoft's workspace monitoring and adapt collection strategy to avoid conflicts while maximizing unique value.

### **ðŸ§  Smart Features**
- **Automatic Conflict Detection**: Detects Microsoft's workspace monitoring via REST API
- **Intelligent Strategy Selection**: Auto-chooses the best collection strategy
- **Backwards Compatibility**: Works with customers not using workspace monitoring
- **Unique Value Focus**: Prioritizes data not covered by Microsoft's official monitoring

### **ðŸ“‹ Quick Intelligent Start**
```python
from fabricla_connector import run_intelligent_monitoring_cycle

# One-line intelligent monitoring - adapts automatically
result = run_intelligent_monitoring_cycle(
    workspace_id="your-workspace-id",
    capacity_id="your-capacity-id"  # Optional
)
```

## ðŸš€ Quick Start

### **Install & Test Locally**
```bash
# Clone and install
git clone https://github.com/Keayoub/FabricLA-Connector.git
cd FabricLA-Connector
pip install -e .

# Test intelligent monitoring
python -c "from fabricla_connector import run_intelligent_monitoring_cycle; print('âœ… Intelligent monitoring ready')"
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

### **ðŸ”§ Fabric Runtime Environment Setup**

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

## ðŸ“Š What This Framework Monitors

| **Data Source** | **Information Collected** | **Custom Table** |
|-----------------|---------------------------|------------------|
| **Pipelines & Dataflows** | Execution status, performance metrics, errors | `FabricPipelineRun_CL`, `FabricDataflowRun_CL` |
| **Dataset Refresh** | Refresh operations, duration, failure analysis | `FabricDatasetRefresh_CL`, `FabricDatasetMetadata_CL` |
| **User Activity** | Access patterns, security events, usage analytics | `FabricUserActivity_CL` |
| **Capacity Metrics** | Resource utilization, workload distribution | `FabricCapacityMetrics_CL`, `FabricCapacityWorkloads_CL` |
| **ðŸ†• Workspace Configuration** | OAP settings, security policies, Git integration, compliance | `FabricWorkspaceConfig_CL` |
| **Spark Execution** | Spark applications, logs, metrics, network traffic | `FabricSparkApplications_CL`, `FabricSparkLogs_CL` |
| **Access Permissions** | User roles, item permissions, capacity assignments | `FabricPermissions_CL` |

## ðŸ”§ Technical Positioning: Complementary Monitoring Architecture

### **Microsoft's Native Monitoring Capabilities**

Microsoft provides several official monitoring solutions with different technical scopes:

#### **[Workspace Monitoring (Preview)](https://learn.microsoft.com/en-us/fabric/admin/monitoring-workspace)**
- **Technical Implementation**: Creates EventHouse database in workspace
- **Data Retention**: 30 days (non-configurable)  
- **Coverage**: User activities, semantic model operations, Real-Time Intelligence logs
- **Access Method**: KQL queries against workspace EventHouse
- **Limitations**: Preview feature, limited retention, specific data sources only

#### **[Fabric Unified Admin Monitoring (FUAM)](https://github.com/microsoft/fabric-toolbox/tree/main/monitoring/fabric-unified-admin-monitoring)**
- **Technical Implementation**: PowerBI reports with Fabric Admin APIs
- **Scope**: Tenant-wide administrative oversight
- **Coverage**: Cross-workspace governance, user management, security monitoring
- **Access Method**: PowerBI dashboards and reports
- **Target**: Fabric administrators and executives

### **FabricLA-Connector Technical Differentiation**

#### **Architectural Differences**
```python
# Microsoft Workspace Monitoring
# - EventHouse database (30-day retention)  
# - Native KQL queries
# - Limited to specific data sources

# FabricLA-Connector
# - Azure Log Analytics (configurable retention)
# - Custom DCR schemas with validation
# - Programmable collection logic
# - Full Azure Monitor ecosystem integration
```

#### **Technical Implementation Patterns**

```python
# Intelligent conflict detection
from fabricla_connector.monitoring_detection import WorkspaceMonitoringDetector

detector = WorkspaceMonitoringDetector()
status = detector.detect_workspace_monitoring(workspace_id, token)

if status.workspace_monitoring_enabled:
    # Skip user activity collection - covered by Microsoft
    # Focus on unique operational data
    collect_sources = ['pipeline_execution', 'capacity_utilization']
else:
    # Collect all sources - no Microsoft monitoring present
    collect_sources = ['user_activity', 'dataset_refresh', 'pipeline_execution', 'capacity_utilization']
```

### **Integration Patterns**

#### **Complementary Deployment Architecture**
```yaml
# Recommended architecture for comprehensive monitoring

Microsoft Workspace Monitoring:
  purpose: Native user activity and semantic model monitoring
  retention: 30 days
  query_interface: EventHouse KQL
  
FabricLA-Connector:
  purpose: Operational monitoring and automation
  retention: 2+ years (configurable)
  query_interface: Log Analytics KQL
  alerting: Azure Monitor rules
  automation: Logic Apps, Functions, GitHub Actions
  
FUAM (Optional):
  purpose: Administrative dashboards
  scope: Tenant-wide governance
  interface: PowerBI reports
```

#### **FabricLA-Connector Value Analysis**

*This connector is designed as **complementary** to existing Microsoft solutions, adding operational capabilities not available elsewhere.*

| **Unique Value Added** | **Existing Microsoft Solutions** | **FabricLA-Connector Enhancement** |
|------------------------|----------------------------------|-----------------------------------|
| **Pipeline Execution Monitoring** | âŒ No native real-time pipeline monitoring | âœ… Real-time execution tracking, activity-level details, failure analysis |
| **Programmable Collection Logic** | âŒ Fixed schemas and collection patterns | âœ… Python framework, custom business rules, conditional collection |
| **Azure Monitor Integration** | âŒ Limited Log Analytics integration | âœ… Full DCR/DCE implementation, custom schemas, Azure alerting |
| **CI/CD & Infrastructure as Code** | âŒ Manual setup and configuration | âœ… Bicep/Terraform templates, Python package, GitHub Actions |
| **Long-term Operational Trends** | âš ï¸ 30-day retention in Workspace Monitoring | âœ… Multi-year retention, historical trend analysis |
| **Custom Capacity Metrics** | âš ï¸ Limited capacity visibility | âœ… Workspace-level utilization, custom thresholds, cost tracking |
| **Intelligent Conflict Avoidance** | âŒ No coordination between solutions | âœ… Auto-detects Microsoft monitoring, adapts collection strategy |
| **Developer Automation** | âŒ Admin-focused tools only | âœ… Python SDK, notebook templates, programmatic workflows |

#### **Complementary Usage Patterns**

| **Technical Scenario** | **Microsoft Native Solutions** | **+ FabricLA-Connector Value** |
|------------------------|--------------------------------|------------------------------|
| **User Activity Monitoring** | Use Workspace Monitoring (native) | Adds long-term retention + custom analysis |
| **Administrative Oversight** | Use FUAM (tenant-wide) | Adds workspace-specific operational details |
| **Fabric-to-Log Analytics** | Use native integration (basic) | Adds custom schemas, real-time collection, programmable logic |
| **Executive Reporting** | Use PowerBI + FUAM templates | Adds operational KPIs, pipeline SLAs, capacity optimization |
| **DevOps Workflows** | No native solution | Provides full CI/CD integration, automated monitoring deployment |
| **Custom Business Logic** | No native solution | Enables custom collection rules, conditional logic, business-specific metrics |
| **Multi-year Analytics** | Limited to 30-day retention | Provides configurable retention, historical trend analysis |
| **Real-time Alerting** | Basic PowerBI alerts | Azure Monitor action groups, Logic Apps, custom automation |

### **Technical References**
- **Microsoft Fabric Toolbox**: https://github.com/microsoft/fabric-toolbox
- **Workspace Monitoring Documentation**: https://learn.microsoft.com/en-us/fabric/admin/monitoring-workspace
- **Fabric Admin APIs**: https://learn.microsoft.com/en-us/rest/api/fabric/admin
- **Azure Monitor Logs Ingestion**: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/logs-ingestion-api-overview

## ðŸ”§ Framework Components

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

## ðŸ“‹ Complete Setup Guide

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

## ðŸ§ª Local Development

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

## ðŸ—ï¸ Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Microsoft       â”‚    â”‚ FabricLA         â”‚    â”‚ Azure Log Analytics â”‚
â”‚ Fabric          â”‚â”€â”€â”€â”€â”‚ Connector        â”‚â”€â”€â”€â”€â”‚ Workspace           â”‚
â”‚ (REST APIs)     â”‚    â”‚ Framework        â”‚    â”‚ (Custom Tables)     â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                              â”‚
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚         â”‚         â”‚
              â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â” â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â” â”Œâ”€â”€â”€â–¼â”€â”€â”€â”€â”
              â”‚ Fabric  â”‚ â”‚ Local  â”‚ â”‚ CI/CD  â”‚
              â”‚Notebooksâ”‚ â”‚ Python â”‚ â”‚Pipelineâ”‚
              â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## ðŸ“š Documentation

- **[Local Testing Guide](tools/README.md)** - Development and upload tools
- **[Deployment Options](DEPLOYMENT_OPTIONS_GUIDE.md)** - Staging vs auto-publish
- **[Packaging Guide](PACKAGING_BEST_PRACTICES.md)** - Modern Python packaging

## ðŸ¤ Contributing

1. Clone the repository
2. Install in development mode: `pip install -e .`
3. Make changes and test locally
4. Use the local testing tools to validate

## ðŸ“„ License

MIT License - See LICENSE file for details

---

**ðŸš€ Ready to monitor your Microsoft Fabric environment?** Start with the Quick Start guide above!