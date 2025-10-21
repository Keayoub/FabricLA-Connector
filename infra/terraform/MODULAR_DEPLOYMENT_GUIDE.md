# Modular DCR Deployment Guide

## Overview

The Fabric monitoring infrastructure now supports **modular deployment** - you can choose exactly which monitoring components to deploy based on your needs. This solves Azure's 10-dataFlow limit per DCR by splitting monitoring into separate, focused DCRs.

## Why Modular Deployment?

**Azure Limitation:** Each Data Collection Rule (DCR) can have a maximum of 10 dataFlows.  
**Original Problem:** The monolithic DCR had 26 streams, causing deployment failures.  
**Solution:** Split into 4 independent DCR modules, each under the 10-stream limit.

## Available Monitoring Modules

### 1. 🔥 **Spark Monitoring** (8 streams)

**Enabled by default:** `deploy_spark_monitoring = true`

**Streams:**

- `FabricSparkLivySession_CL` - Livy session metadata (Phase 1)
- `FabricSparkLogs_CL` - Spark driver/executor logs (Phase 1)
- `FabricSparkHistoryMetrics_CL` - Job/stage metrics from history server (Phase 1)
- `FabricSparkResourceUsage_CL` - CPU, memory, disk usage (Phase 4)
- `FabricSparkJobs_CL` - Spark job definitions
- `FabricSparkJobRuns_CL` - Spark job execution history
- `FabricNotebooks_CL` - Notebook metadata
- `FabricNotebookRuns_CL` - Notebook execution tracking

**Use cases:**

- Monitor Spark job performance and execution
- Track resource utilization (CPU, memory, disk)
- Analyze Spark failures and bottlenecks
- Optimize Spark configurations
- Notebook execution monitoring
- Spark job lifecycle tracking

---

### 2. 📊 **Pipeline & Dataflow Monitoring** (4 streams)

**Disabled by default:** `deploy_pipeline_monitoring = false`

**Streams:**

- `FabricPipelineRun_CL` - Pipeline execution tracking
- `FabricPipelineActivityRun_CL` - Activity-level details
- `FabricDataflowRun_CL` - Dataflow refresh monitoring
- `FabricUserActivity_CL` - User actions and operations

**Use cases:**

- Track ETL pipeline health
- Monitor dataflow refreshes
- Audit user activities
- Analyze pipeline bottlenecks

---

### 3. 💾 **Capacity & Workspace Monitoring** (7 streams)
**Disabled by default:** `deploy_capacity_monitoring = false`

**Streams:**
- `FabricDatasetRefresh_CL` - Dataset refresh status
- `FabricDatasetMetadata_CL` - Dataset size and structure
- `FabricCapacityMetrics_CL` - Capacity utilization metrics
- `FabricCapacityWorkloads_CL` - Workload resource usage
- `FabricWorkspaceEvents_CL` - Workspace-level events
- `FabricItemDetails_CL` - Inventory of workspace items
- `FabricOneLakeStorage_CL` - OneLake storage metrics

**Use cases:**
- Monitor capacity consumption
- Track dataset refresh patterns
- Analyze storage growth
- Workspace inventory management

---

### 4. 🔐 **Admin & Governance Monitoring** (6 streams)

**Disabled by default:** `deploy_admin_monitoring = false`

**Streams:**

- `FabricGitIntegration_CL` - Git sync status
- `FabricPermissions_CL` - Access control audit
- `FabricDataLineage_CL` - Data flow lineage
- `FabricSemanticModels_CL` - Semantic model metadata
- `FabricRealTimeIntelligence_CL` - Real-time analytics events
- `FabricMirroring_CL` - Database mirroring status

**Use cases:**

- Security and compliance auditing
- Git integration monitoring
- Data lineage tracking
- Governance and compliance reporting
- Semantic model management
- Database mirroring status

---

## Quick Start Deployment Scenarios

### Scenario 1: Spark Monitoring Only (Recommended for Testing Phase 1 & 4)

**Goal:** Deploy only Spark monitoring for Phase 1 & 4 testing.

```hcl
# terraform.tfvars
deploy_infrastructure    = true
deploy_tables           = true
deploy_spark_monitoring = true

deploy_pipeline_monitoring = false
deploy_capacity_monitoring = false
deploy_admin_monitoring    = false
```

**Deployment:**
```cmd
cd c:\Dvlp\fabric-la-connector\infra\terraform
terraform apply
```

**Outputs you'll get:**
- `data_collection_endpoint_logs_ingestion_endpoint` - DCE URL
- `dcr_spark_immutable_id` - DCR ID for Spark monitoring
- `log_analytics_workspace_name` - Where data is stored

---

### Scenario 2: Complete Monitoring (All Modules)

**Goal:** Deploy all monitoring capabilities.

```hcl
# terraform.tfvars
deploy_infrastructure    = true
deploy_tables           = true
deploy_spark_monitoring    = true
deploy_pipeline_monitoring = true
deploy_capacity_monitoring = true
deploy_admin_monitoring    = true
```

**Result:** 4 separate DCRs deployed, each handling its own monitoring domain.

---

### Scenario 3: Selective Monitoring

**Goal:** Only Pipeline and Capacity monitoring (no Spark or Admin).

```hcl
# terraform.tfvars
deploy_infrastructure      = true
deploy_tables             = true
deploy_pipeline_monitoring = true
deploy_capacity_monitoring = true

deploy_spark_monitoring = false
deploy_admin_monitoring = false
```

---

## Deployment Steps

### Step 1: Configure Variables

Create `infra/terraform/terraform.tfvars`:

```hcl
# Base infrastructure (required)
deploy_infrastructure = true
deploy_tables        = true

# Choose monitoring modules
deploy_spark_monitoring    = true   # Phase 1 & 4 Spark monitoring
deploy_pipeline_monitoring = false  # Pipeline & dataflow tracking
deploy_capacity_monitoring = false  # Capacity & workspace metrics
deploy_admin_monitoring    = false  # Governance & audit

# Optional: Service principal for ingestion (if using MSI, leave empty)
service_principal_object_id = ""
```

### Step 2: Initialize Terraform

```cmd
cd c:\Dvlp\fabric-la-connector\infra\terraform
terraform init
```

### Step 3: Review Deployment Plan

```cmd
terraform plan
```

**Check the plan shows:**
- ✅ Resources to create (based on your enabled modules)
- ✅ Correct DCR templates being used
- ✅ No errors about 10-dataFlow limits

### Step 4: Deploy

```cmd
terraform apply
```

Type `yes` when prompted.

### Step 5: Capture Outputs

Terraform will output configuration for each deployed module:

```
Outputs:

data_collection_endpoint_logs_ingestion_endpoint = "https://dce-fabric-monitoring-xxxxx.canadacentral-1.ingest.monitor.azure.com"
dcr_spark_immutable_id = "dcr-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
deployed_monitoring_modules = {
  admin_monitoring    = false
  capacity_monitoring = false
  pipeline_monitoring = false
  spark_monitoring    = true
}
log_analytics_workspace_name = "law-fabric-monitoring"
resource_group_name = "rg-fabric-monitoring"
```

---

## Using the Deployed DCRs

### Configuration by Module

Each monitoring module requires its own DCR ID. Create `.env` files for each:

#### Spark Monitoring Configuration
```env
# .env.spark
AZURE_MONITOR_DCE_ENDPOINT=<data_collection_endpoint_logs_ingestion_endpoint>
AZURE_MONITOR_DCR_IMMUTABLE_ID=<dcr_spark_immutable_id>
AZURE_MONITOR_STREAM_NAME=Custom-FabricSparkLivySession_CL
LOG_ANALYTICS_TABLE=FabricSparkLivySession_CL
```

#### Pipeline Monitoring Configuration
```env
# .env.pipeline
AZURE_MONITOR_DCE_ENDPOINT=<data_collection_endpoint_logs_ingestion_endpoint>
AZURE_MONITOR_DCR_IMMUTABLE_ID=<dcr_pipeline_immutable_id>
AZURE_MONITOR_STREAM_NAME=Custom-FabricPipelineRun_CL
LOG_ANALYTICS_TABLE=FabricPipelineRun_CL
```

#### Capacity Monitoring Configuration
```env
# .env.capacity
AZURE_MONITOR_DCE_ENDPOINT=<data_collection_endpoint_logs_ingestion_endpoint>
AZURE_MONITOR_DCR_IMMUTABLE_ID=<dcr_capacity_immutable_id>
AZURE_MONITOR_STREAM_NAME=Custom-FabricCapacityMetrics_CL
LOG_ANALYTICS_TABLE=FabricCapacityMetrics_CL
```

#### Admin Monitoring Configuration
```env
# .env.admin
AZURE_MONITOR_DCE_ENDPOINT=<data_collection_endpoint_logs_ingestion_endpoint>
AZURE_MONITOR_DCR_IMMUTABLE_ID=<dcr_admin_immutable_id>
AZURE_MONITOR_STREAM_NAME=Custom-FabricPermissions_CL
LOG_ANALYTICS_TABLE=FabricPermissions_CL
```

---

## Deployment Architecture

```
Azure Resource Group: rg-fabric-monitoring
│
├── Log Analytics Workspace (law-fabric-monitoring)
│   └── 22 Custom Tables (_CL suffix)
│
├── Data Collection Endpoint (dce-fabric-monitoring)
│   └── Single ingestion endpoint for all DCRs
│
└── Data Collection Rules (DCRs)
    ├── dcr-fabric-monitoring-spark      ✅ 4 streams  (Spark)
    ├── dcr-fabric-monitoring-pipeline   ✅ 4 streams  (Pipelines)
    ├── dcr-fabric-monitoring-capacity   ✅ 7 streams  (Capacity)
    └── dcr-fabric-monitoring-admin      ✅ 10 streams (Admin/Gov)
```

**Key benefits:**
- ✅ Each DCR under 10-stream limit
- ✅ Independent deployment and scaling
- ✅ All use same DCE and Log Analytics workspace
- ✅ Granular RBAC possible per DCR

---

## Cost Optimization

**Deploy only what you need:**
- **Testing Phase 1 & 4:** Only Spark monitoring (~$5-10/month)
- **Production (selective):** Spark + Pipeline + Capacity (~$20-30/month)
- **Full governance:** All modules (~$40-60/month)

**Cost factors:**
- Data ingestion volume (per GB)
- Log Analytics retention (30 days default)
- Number of active DCRs

---

## Troubleshooting

### Problem: Terraform fails with "deploy_spark_dcr not found"

**Solution:** The variable was renamed. Use:
```hcl
deploy_spark_monitoring = true  # ✅ Correct
# deploy_spark_dcr = true       # ❌ Old name
```

### Problem: Want to add a module after initial deployment

**Solution:** Update `terraform.tfvars`, then:
```cmd
terraform apply
```

Terraform will add only the new DCR(s) without affecting existing ones.

### Problem: Want to remove a module

**Solution:** Set its variable to `false` in `terraform.tfvars`, then:
```cmd
terraform apply
```

Terraform will destroy that DCR (data in Log Analytics remains).

---

## Migration from Legacy DCR

If you previously deployed the monolithic DCR (22 streams):

1. **Set `deploy_main_dcr = false`** (it's already default)
2. **Enable new modular DCRs** based on your needs
3. **Run `terraform apply`** to deploy new DCRs
4. **Update collector configurations** to use new DCR IDs
5. **Optional:** Manually delete old failing DCR from Azure Portal

---

## Summary

| Module | Streams | Default | Use Case |
|--------|---------|---------|----------|
| Spark Monitoring | 8 | ✅ Enabled | Spark sessions, jobs, notebooks, resource tracking |
| Pipeline Monitoring | 4 | ❌ Disabled | ETL tracking, user activity |
| Capacity Monitoring | 7 | ❌ Disabled | Resource management, cost optimization |
| Admin Monitoring | 6 | ❌ Disabled | Governance, compliance, lineage |

**Recommendation for your current phase:**  
Deploy **Spark Monitoring only** to test Phase 1 & 4, then enable others as needed.

**Next step:** Run `terraform apply` with Spark monitoring enabled! 🚀
