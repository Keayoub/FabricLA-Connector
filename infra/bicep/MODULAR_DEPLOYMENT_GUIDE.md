# Modular Bicep Deployment Guide for Fabric Monitoring

## Overview

This Bicep deployment supports **modular deployment** - you can choose exactly which monitoring components to deploy based on your needs. This solves Azure's 10-dataFlow limit per DCR by splitting monitoring into separate, focused DCRs.

## Why Modular Deployment?

**Azure Limitation:** Each Data Collection Rule (DCR) can have a maximum of 10 dataFlows.  
**Original Problem:** The monolithic DCR had 26 streams, causing deployment failures.  
**Solution:** Split into 4 independent DCR modules, each under the 10-stream limit.

## Available Monitoring Modules

### 1. 🔥 **Spark Monitoring** (8 streams)

**Enabled by default:** `deploySparkMonitoring: true`

**Streams:**
- `FabricSparkLivySession_CL` - Livy session metadata
- `FabricSparkLogs_CL` - Spark driver/executor logs
- `FabricSparkHistoryMetrics_CL` - Job/stage metrics
- `FabricSparkResourceUsage_CL` - CPU, memory, disk usage
- `FabricSparkJobs_CL` - Spark job definitions
- `FabricSparkJobRuns_CL` - Spark job execution history
- `FabricNotebooks_CL` - Notebook metadata
- `FabricNotebookRuns_CL` - Notebook execution tracking

**Use cases:**
- Monitor Spark job performance and execution
- Track resource utilization (CPU, memory, disk)
- Analyze Spark failures and bottlenecks
- Optimize Spark configurations

---

### 2. 📊 **Pipeline & Dataflow Monitoring** (4 streams)

**Disabled by default:** `deployPipelineMonitoring: false`

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

**Disabled by default:** `deployCapacityMonitoring: false`

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

**Disabled by default:** `deployAdminMonitoring: false`

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

---

## Quick Start

### Prerequisites

1. **Azure CLI** installed and authenticated
2. **Bicep CLI** installed (comes with Azure CLI 2.20+)
3. **Log Analytics Workspace** already created
4. **Required permissions:**
   - Contributor on the resource group
   - Log Analytics Contributor on the workspace

### Step 1: Configure Parameters

Copy the example parameters file and update with your values:

```bash
cp params.example.json params.json
```

Edit `params.json` and update:

```json
{
  "parameters": {
    "lawId": {
      "value": "/subscriptions/YOUR-SUB-ID/resourceGroups/YOUR-RG/providers/Microsoft.OperationalInsights/workspaces/YOUR-WORKSPACE"
    },
    "workspaceName": {
      "value": "your-workspace-name"
    },
    "location": {
      "value": "canadacentral"
    },
    "deploySparkMonitoring": {
      "value": true
    },
    "deployPipelineMonitoring": {
      "value": false
    },
    "deployCapacityMonitoring": {
      "value": false
    },
    "deployAdminMonitoring": {
      "value": false
    }
  }
}
```

### Step 2: Validate the Deployment

```bash
az deployment group validate \
  --resource-group YOUR-RESOURCE-GROUP \
  --template-file main.bicep \
  --parameters @params.json
```

### Step 3: Deploy

```bash
az deployment group create \
  --resource-group YOUR-RESOURCE-GROUP \
  --template-file main.bicep \
  --parameters @params.json \
  --name fabric-monitoring-deployment
```

### Step 4: Get Outputs

After deployment, retrieve the DCR immutable IDs and DCE endpoint:

```bash
az deployment group show \
  --resource-group YOUR-RESOURCE-GROUP \
  --name fabric-monitoring-deployment \
  --query properties.outputs
```

Save these values - you'll need them for your `.env` file:
- `dceLogsIngestionEndpoint` → `AZURE_MONITOR_DCE_ENDPOINT`
- `dcrSparkImmutableId` → `AZURE_MONITOR_DCR_IMMUTABLE_ID` (if using Spark monitoring)

---

## Deployment Scenarios

### Scenario 1: Spark Monitoring Only (Default)

**Perfect for:** Teams focused on Spark performance optimization

```json
{
  "deploySparkMonitoring": { "value": true },
  "deployPipelineMonitoring": { "value": false },
  "deployCapacityMonitoring": { "value": false },
  "deployAdminMonitoring": { "value": false }
}
```

### Scenario 2: ETL Pipeline Monitoring

**Perfect for:** Data engineering teams monitoring data pipelines

```json
{
  "deploySparkMonitoring": { "value": false },
  "deployPipelineMonitoring": { "value": true },
  "deployCapacityMonitoring": { "value": false },
  "deployAdminMonitoring": { "value": false }
}
```

### Scenario 3: Full Observability

**Perfect for:** Platform teams managing complete Fabric environments

```json
{
  "deploySparkMonitoring": { "value": true },
  "deployPipelineMonitoring": { "value": true },
  "deployCapacityMonitoring": { "value": true },
  "deployAdminMonitoring": { "value": true }
}
```

### Scenario 4: Compliance & Governance

**Perfect for:** Security and compliance teams

```json
{
  "deploySparkMonitoring": { "value": false },
  "deployPipelineMonitoring": { "value": false },
  "deployCapacityMonitoring": { "value": false },
  "deployAdminMonitoring": { "value": true }
}
```

---

## Updating Your Deployment

To add or remove monitoring modules:

1. Update `params.json` with the new deployment flags
2. Re-run the deployment:

```bash
az deployment group create \
  --resource-group YOUR-RESOURCE-GROUP \
  --template-file main.bicep \
  --parameters @params.json \
  --name fabric-monitoring-update
```

Bicep handles incremental updates - it will:
- ✅ Create new DCRs for enabled modules
- ✅ Keep existing DCRs unchanged
- ⚠️ **Note:** Disabling a module doesn't delete the DCR (manual cleanup required)

---

## Outputs Reference

After deployment, the following outputs are available:

| Output Name | Description | Usage |
|-------------|-------------|-------|
| `dceId` | Data Collection Endpoint resource ID | Azure resource reference |
| `dceLogsIngestionEndpoint` | DCE ingestion endpoint URL | Set as `AZURE_MONITOR_DCE_ENDPOINT` in `.env` |
| `dcrSparkImmutableId` | Spark DCR immutable ID | Set as `AZURE_MONITOR_DCR_IMMUTABLE_ID` for Spark monitoring |
| `dcrPipelineImmutableId` | Pipeline DCR immutable ID | Use for pipeline monitoring notebooks |
| `dcrCapacityImmutableId` | Capacity DCR immutable ID | Use for capacity monitoring notebooks |
| `dcrAdminImmutableId` | Admin DCR immutable ID | Use for admin/governance notebooks |
| `deployedModules` | Object showing which modules were deployed | Quick status check |
| `allTableNames` | Array of all 25 table names | Reference for KQL queries |

---

## Troubleshooting

### Issue: "Deployment validation failed - exceeds dataFlow limit"

**Cause:** Trying to deploy a DCR with more than 10 dataFlows

**Solution:** Make sure you're using the modular templates, not the old monolithic DCR template

### Issue: "Module output is null"

**Cause:** Trying to access outputs from a DCR that wasn't deployed

**Solution:** Check the `deployedModules` output to see which modules are active

### Issue: "Table already exists"

**Cause:** Tables were created in a previous deployment

**Solution:** This is expected - Bicep will skip existing tables (idempotent)

---

## Cost Considerations

Each DCR has minimal cost (typically < $5/month). The main costs are:

1. **Log Analytics ingestion:** ~$2.76/GB ingested
2. **Log Analytics retention:** ~$0.12/GB/month (after 31-day free tier)
3. **Data Collection Endpoint:** Negligible (< $1/month)

**Tip:** Start with one module and add more as needed to control costs.

---

## Comparing with Terraform

Both Bicep and Terraform implementations support the same modular deployment model:

| Feature | Bicep | Terraform |
|---------|-------|-----------|
| Modular DCRs | ✅ | ✅ |
| Conditional deployment | ✅ `if` conditions | ✅ `count` conditions |
| Parameters | ✅ `params.json` | ✅ `terraform.tfvars` |
| State management | ❌ (Azure-native) | ✅ `.tfstate` |
| Preview/Plan | ✅ `validate` | ✅ `plan` |
| IDE support | ✅ VS Code extension | ✅ VS Code extension |

**Choose Bicep if:** You prefer Azure-native tooling, simpler syntax, no state files  
**Choose Terraform if:** You use multi-cloud, need state management, prefer HCL

---

## Next Steps

1. ✅ **Deploy infrastructure** using this guide
2. ✅ **Configure notebooks** with DCR IDs from outputs
3. ✅ **Start collecting data** by running the monitoring notebooks
4. ✅ **Build dashboards** in Log Analytics to visualize your data
5. ✅ **Set up alerts** for critical monitoring scenarios

For notebook configuration, see: [../../notebooks/README.md](../../notebooks/README.md)

---

## Additional Resources

- [Azure DCR Documentation](https://learn.microsoft.com/azure/azure-monitor/essentials/data-collection-rule-overview)
- [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Log Analytics Custom Logs](https://learn.microsoft.com/azure/azure-monitor/logs/tutorial-logs-ingestion-portal)
- [Fabric Monitoring Best Practices](../../docs/MONITORING_BEST_PRACTICES.md)
