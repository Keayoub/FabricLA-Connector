# Fabric Tenant Governance - Quick Start Guide

This guide will help you get started with Fabric tenant governance and preview feature management in **15 minutes**.

## Prerequisites Checklist

- [ ] **Fabric Administrator** role in your tenant
- [ ] **Azure subscription** with Contributor access
- [ ] **Azure CLI** installed ([Download](https://aka.ms/installazurecliwindows))
- [ ] **PowerShell 5.1+** or **PowerShell Core 7+**
- [ ] **Python 3.8+** installed (for notebooks)

## Quick Start Steps

### Step 1: Deploy Infrastructure (5 minutes)

1. Open Command Prompt or PowerShell
2. Navigate to the project directory:
   ```cmd
   cd c:\Dvlp\fabric-samples\fabric-governance
   ```

3. Run the deployment script:
   ```cmd
   deploy-infrastructure.bat
   ```

4. Follow the prompts:
   - Resource group name: `fabric-governance-rg`
   - Region: `eastus` (or your preferred region)
   - Workspace name: `fabric-governance-la`
   - Environment: `production`
   - Alert emails: `your-email@company.com`

5. **Save the output values** - you'll need them for configuration!

### Step 2: Configure Environment (2 minutes)

1. Copy the example environment file:
   ```cmd
   copy .env.example .env
   ```

2. Edit `.env` and paste the values from Step 1:
   ```ini
   AZURE_MONITOR_DCE_ENDPOINT=<from deployment output>
   AZURE_MONITOR_DCR_IMMUTABLE_ID=<from deployment output>
   LOG_ANALYTICS_WORKSPACE_ID=<from deployment output>
   ```

3. Add your Fabric tenant ID:
   ```ini
   FABRIC_TENANT_ID=<your-fabric-tenant-id>
   ```

### Step 3: Install Python Dependencies (3 minutes)

```cmd
pip install -r requirements.txt
```

If you're using a Fabric notebook environment, the dependencies may already be available.

### Step 4: Export Baseline Settings (2 minutes)

**Option A: Using PowerShell**

```powershell
# Login with Azure CLI first
az login

# Export tenant settings
.\powershell\Get-FabricTenantSettings.ps1 `
  -OutputPath ".\baseline\prod-tenant-settings.json" `
  -IncludePreviewFeatures `
  -Verbose
```

**Option B: Using Python Notebook**

1. Open `notebooks\fabric_tenant_settings_monitor.ipynb` in VS Code or Fabric
2. Run all cells
3. Check the output and Log Analytics

### Step 5: Test the Pipeline (3 minutes)

Run the automated governance pipeline:

```cmd
python scripts\automated_governance_pipeline.py --mode monitor
```

Check the output for:
- ✓ Authentication success
- ✓ Settings retrieved
- ✓ Preview features identified
- ✓ Data ingested to Log Analytics

## What's Next?

### View Your Data in Log Analytics

1. Open Azure Portal → your Log Analytics workspace
2. Go to **Logs** blade
3. Run this query:

```kql
FabricTenantSettings_CL
| where TimeGenerated > ago(1h)
| where IsPreviewFeature_b == true
| summarize count() by Enabled_b
| render piechart
```

### Set Up Scheduled Monitoring

**Option 1: Windows Task Scheduler**
```cmd
schtasks /create /tn "FabricGovernanceMonitor" /tr "python scripts\automated_governance_pipeline.py --mode monitor" /sc daily /st 09:00
```

**Option 2: Azure Automation**
- Upload the Python script to Azure Automation
- Create a schedule (e.g., daily at 9 AM)
- Configure managed identity with Fabric Admin permissions

### Compare TEST vs PROD Environments

1. Export settings from TEST environment
2. Export settings from PROD environment
3. Run comparison:

```powershell
.\powershell\Compare-TenantSettings.ps1 `
  -TestSettingsPath ".\baseline\test-settings.json" `
  -ProdSettingsPath ".\baseline\prod-settings.json" `
  -OutputReport ".\reports\comparison.html" `
  -HighlightPreviewFeatures
```

4. Open `reports\comparison.html` in browser

## Common Issues & Solutions

### Issue: "Access Denied" when calling API

**Solution:** Verify you have Fabric Administrator role:

```bash
# Login with Azure CLI
az login

# Verify you can get a Fabric API token
az account get-access-token --resource "https://api.fabric.microsoft.com"
```

### Issue: "DCE Endpoint not found"

**Solution:** Verify the deployment completed successfully:
```cmd
az deployment group show --resource-group fabric-governance-rg --name fabric-governance-deployment --query properties.outputs
```

### Issue: Python dependencies installation fails

**Solution:** Upgrade pip and try again:
```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### Issue: No data in Log Analytics

**Solution:** Check data ingestion:
1. Verify DCR immutable ID is correct
2. Check if stream name matches: `Custom-FabricTenantSettings_CL`
3. Wait 5-10 minutes (initial ingestion delay)
4. Run this query to check ingestion status:

```kql
_LogOperation
| where TimeGenerated > ago(1h)
| where Detail contains "FabricTenantSettings"
```

## Useful Commands

### Export settings to CSV
```powershell
.\powershell\Get-FabricTenantSettings.ps1 -OutputPath "settings.csv" -Format CSV
```

### Export settings to HTML report
```powershell
.\powershell\Get-FabricTenantSettings.ps1 -OutputPath "settings.html" -Format HTML
```

### Monitor with alerts enabled
```cmd
python scripts\automated_governance_pipeline.py --mode monitor --config .env
```

### Run in CI/CD pipeline (fail on drift)
```cmd
set FAIL_ON_DRIFT=true
python scripts\automated_governance_pipeline.py --mode monitor
```

## Key Features Summary

| Feature | PowerShell | Python | Notebook |
|---------|-----------|--------|----------|
| Export tenant settings | ✅ | ✅ | ✅ |
| Identify preview features | ✅ | ✅ | ✅ |
| Compare environments | ✅ | ✅ | ❌ |
| Send to Log Analytics | ❌ | ✅ | ✅ |
| Generate HTML reports | ✅ | ❌ | ❌ |
| Scheduled automation | ✅ | ✅ | ❌ |
| Alert integration | ❌ | ✅ | ✅ |

## Best Practices

1. **Daily Monitoring**: Run the pipeline daily to catch changes early
2. **Baseline Versioning**: Store baseline files in Git with dates
3. **Preview Control**: Never enable previews in PROD without TEST validation
4. **Alert Configuration**: Set up Teams/email webhooks for critical alerts
5. **Documentation**: Document all approved preview features with justifications

## Support

- 📖 Full documentation: `README.md`
- 🐛 Issues: Open GitHub issue
- 💬 Questions: Contact Fabric Admin team
- 📊 Monitoring: Check Log Analytics dashboards

## Success Checklist

After completing this guide, you should have:

- [x] Infrastructure deployed in Azure
- [x] Environment configured (.env file)
- [x] Python dependencies installed
- [x] Baseline settings exported
- [x] First monitoring run completed
- [x] Data visible in Log Analytics
- [x] Alerts configured (optional)
- [x] Scheduled monitoring set up (optional)

**Congratulations! 🎉 Your Fabric tenant governance is now operational.**

---

*For advanced scenarios, see the full README.md and detailed documentation.*
