# Environment Configuration Guide

This guide explains how to set up your environment variables for the Fabric LA Connector.

## 📁 Files Created

1. **`.env.example`** (root) - Template with all variables and instructions
2. **`.env`** (root) - Your actual configuration (already populated with Terraform outputs)
3. **`notebooks/.env.example`** (notebooks) - Updated with correct variable names

## 🚀 Quick Start

### Option 1: Already Deployed (Recommended)

Your `.env` file is already created with the Terraform outputs! Just update the Fabric workspace details:

```bash
# Edit .env file and update these lines:
FABRIC_WORKSPACE_ID=your-actual-workspace-id
FABRIC_WORKSPACE_NAME=your-actual-workspace-name
FABRIC_APP_ID=your-fabric-app-id
FABRIC_APP_SECRET=your-fabric-app-secret
```

### Option 2: Fresh Setup

If you need to recreate the `.env` file:

1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Get Terraform outputs:**
   ```bash
   cd infra/terraform
   terraform output -json
   ```

3. **Update .env with these mappings:**
   
   | `.env` Variable | Terraform Output Key |
   |----------------|---------------------|
   | `AZURE_MONITOR_DCE_ENDPOINT` | `data_collection_endpoint_logs_ingestion_endpoint` |
   | `AZURE_MONITOR_DCR_IMMUTABLE_ID` | `dcr_spark_immutable_id` |
   | `LOG_ANALYTICS_WORKSPACE_NAME` | `log_analytics_workspace_name` |
   | `AZURE_TENANT_ID` | `tenant_id` |
   | `AZURE_SUBSCRIPTION_ID` | From `az account show` |

4. **Add your Fabric workspace details:**
   - Get Workspace ID from Fabric Portal URL
   - Create App Registration in Azure AD for Fabric API access

## 🔑 Variable Reference

### Required for Ingestion Testing

```bash
# Azure Monitor (from Terraform outputs)
AZURE_MONITOR_DCE_ENDPOINT=https://dce-fabric-monitoring-xxxx.canadacentral-1.ingest.monitor.azure.com
AZURE_MONITOR_DCR_IMMUTABLE_ID=dcr-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LOG_ANALYTICS_WORKSPACE_NAME=law-fabric-monitoring

# Stream names (predefined - don't change)
AZURE_MONITOR_STREAM_LIVY_SESSION=Custom-FabricSparkLivySession_CL
AZURE_MONITOR_STREAM_SPARK_LOGS=Custom-FabricSparkLogs_CL
AZURE_MONITOR_STREAM_HISTORY_METRICS=Custom-FabricSparkHistoryMetrics_CL
AZURE_MONITOR_STREAM_RESOURCE_USAGE=Custom-FabricSparkResourceUsage_CL
```

### Required for Fabric Data Collection

```bash
# Fabric Workspace
FABRIC_WORKSPACE_ID=your-workspace-guid
FABRIC_WORKSPACE_NAME=your-workspace-name
FABRIC_TENANT_ID=your-tenant-id

# Fabric Authentication (Azure AD App)
FABRIC_APP_ID=your-app-registration-client-id
FABRIC_APP_SECRET=your-app-registration-secret
```

### Optional Configuration

```bash
# Collection behavior
FABRIC_LOOKBACK_HOURS=24
FABRIC_COLLECT_ACTIVITY_RUNS=true
FABRIC_METRICS_INTERVAL_MINUTES=15
FABRIC_CAPACITY_ID=your-capacity-id
FABRIC_RUNTIME_VERSION=1.3

# Key Vault (for secret management)
AZURE_KEY_VAULT_URI=https://your-keyvault.vault.azure.net/
AZURE_KEY_VAULT_SECRET_NAME=fabric-app-secret
```

## 🧪 Test Your Configuration

### 1. Test Ingestion (No Fabric Data Required)

Open and run `test_ingestion.ipynb`:

```python
# This tests:
# - Azure authentication
# - DCE connectivity
# - DCR data upload
# - Schema validation
```

**Expected result:** ✅ Upload successful!

### 2. Verify in Log Analytics (2-5 minutes later)

```kql
FabricSparkLivySession_CL
| where TimeGenerated > ago(10m)
| where SessionName == "IngestionTest-Notebook"
| take 10
```

### 3. Test Fabric Data Collection

Once Fabric variables are set:

```python
from fabricla_connector import collectors

# Test Phase 1 - Livy Sessions
collectors.collect_livy_sessions()

# Test Phase 4 - Resource Usage
collectors.collect_resource_usage()
```

## 🔐 Authentication Methods

The connector uses `DefaultAzureCredential` which tries (in order):

1. **Environment Variables** - `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`
2. **Managed Identity** - For Azure VMs, Functions, etc.
3. **Visual Studio Code** - Signed-in account
4. **Azure CLI** - `az login`
5. **Azure PowerShell** - `Connect-AzAccount`

**For local testing:** Run `az login` before using the notebooks.

## 📊 Current Deployment Status

Your infrastructure is deployed with:

- ✅ **DCE:** `dce-fabric-monitoring-lede`
- ✅ **DCR:** `dcr-fabric-monitoring-spark` (8 streams)
- ✅ **Workspace:** `law-fabric-monitoring`
- ✅ **Module:** Spark Monitoring (Livy Sessions, Logs, Metrics, Resource Usage, Jobs, Notebooks)

## 🆘 Troubleshooting

### "Missing required environment variables"
- Check `.env` file exists in project root
- Verify variable names match exactly (case-sensitive)
- Run `load_dotenv()` returns `True`

### "Authentication failed"
- Run `az login` in terminal
- Or set service principal variables
- Check Azure subscription is active

### "Upload failed with 4xx error"
- Verify DCR immutable ID is correct
- Check stream name matches DCR configuration
- Ensure service principal has "Monitoring Metrics Publisher" role

### "No data in Log Analytics"
- Wait 2-5 minutes after upload
- Check correct workspace name
- Verify table name: `FabricSparkLivySession_CL` (with `_CL` suffix)

## 📚 Next Steps

1. ✅ Test ingestion with `test_ingestion.ipynb`
2. ⏳ Wait 2-5 minutes, query Log Analytics
3. 🔧 Update Fabric workspace variables
4. 🚀 Start collecting real data
5. 📊 Set up dashboards and alerts

---

**Need help?** Check the main `README.md` or `docs/TERRAFORM_DEPLOYMENT_GUIDE.md`
