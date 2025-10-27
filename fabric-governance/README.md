# Fabric Tenant Governance & Preview Feature Management

A comprehensive solution for managing Microsoft Fabric tenant settings, preview features, and governance controls to ensure safe TEST → PROD promotion workflows.

## 🎯 Overview

This solution helps Fabric Admins:
- **Monitor & Control Preview Features** across TEST and PROD tenants
- **Automate Tenant Settings Validation** before artifact promotion
- **Track Configuration Changes** with alerts and audit trails
- **Enforce Governance Policies** using security groups and API automation
- **Generate Compliance Reports** for tenant configuration drift

## 🚀 Key Capabilities

### 1. Preview Feature Management
- Export current tenant settings using the `GetTenantSettingsAsAdmin` API
- Compare TEST vs PROD configurations to identify drift
- Auto-disable preview features in PROD before artifact promotion
- Security group-based access control (e.g., `Preview-Testers` group)

### 2. Tenant Settings Monitoring
- Programmatic inspection of all tenant configurations
- Alert on newly introduced preview toggles
- Track changes over time in Power BI dashboards
- Export settings for version control and compliance

### 3. TEST → PROD Pipeline Automation
- Validate artifacts in TEST with preview features enabled
- Automatically disable previews before PROD promotion
- Script-based artifact deployment with safety checks
- Rollback capabilities for failed promotions

### 4. Compliance & Audit
- Daily snapshots of tenant settings stored in Azure Log Analytics
- Compare settings across environments and time periods
- Generate compliance reports for security reviews
- Track who changed what and when

## 📁 Solution Components

### 🔧 **PowerShell Scripts** (`/powershell/`)
| Script | Purpose | Key Features |
|--------|---------|--------------|
| `Get-FabricTenantSettings.ps1` | Export tenant settings | Full settings export, JSON output, comparison tools |
| `Compare-TenantSettings.ps1` | Compare TEST vs PROD | Identify drift, preview feature detection, reporting |
| `Disable-PreviewFeatures.ps1` | Disable preview toggles | Bulk disable, security group filtering, safe mode |
| `Monitor-TenantChanges.ps1` | Track configuration changes | Alert on new previews, scheduled monitoring, webhook integration |
| `Deploy-WithGovernance.ps1` | Safe TEST → PROD promotion | Pre-flight checks, automatic preview disable, rollback support |

### 📊 **Python Notebooks** (`/notebooks/`)
| Notebook | Purpose | Key Features |
|----------|---------|--------------|
| `fabric_tenant_settings_monitor.ipynb` | Collect & analyze tenant settings | API integration, Log Analytics ingestion, trend analysis |
| `preview_feature_dashboard.ipynb` | Preview feature tracking | Visual dashboards, risk scoring, recommendation engine |
| `tenant_compliance_reporter.ipynb` | Generate compliance reports | Policy validation, drift detection, audit trail |
| `automated_governance_pipeline.ipynb` | End-to-end automation | Scheduled runs, alert integration, self-healing |

### 🏗️ **Infrastructure** (`/bicep/` & `/terraform/`)
| Component | Technology | Purpose |
|-----------|------------|---------|
| `tenant-monitoring.bicep` | Bicep | Log Analytics, DCR, custom tables for tenant data |
| `terraform/main.tf` | Terraform | Complete infrastructure with Azure provider |
| `terraform/deploy.bat` | Windows Script | Automated Terraform deployment |
| `terraform/deploy.sh` | Bash Script | Automated Terraform deployment (Linux/macOS) |

### 📋 **Custom Log Analytics Tables**
- `FabricTenantSettings_CL` - Complete tenant settings snapshots
- `FabricPreviewFeatures_CL` - Preview feature status and changes
- `FabricGovernanceEvents_CL` - Audit trail of governance actions
- `FabricEnvironmentComparison_CL` - TEST vs PROD drift analysis

## 🔐 Prerequisites

### Required Permissions
- **Fabric Admin** role for tenant settings API access
- **Contributor** on Azure resource group for Log Analytics
- **Security Reader** for Azure AD security group management

### Azure Resources
- Azure Log Analytics workspace
- Data Collection Endpoint (DCE) and Rules (DCR)
- (Optional) Azure Key Vault for secure credential storage
- (Optional) Azure Automation for scheduled runs

### PowerShell Modules
```powershell
Install-Module -Name Az.Accounts -Scope CurrentUser
Install-Module -Name Az.OperationalInsights -Scope CurrentUser
Install-Module -Name MicrosoftFabricMgmt -Scope CurrentUser -AllowPrerelease
```

### Python Packages
```bash
pip install azure-identity azure-mgmt-loganalytics azure-monitor-ingestion
pip install semantic-link-sempy requests pandas plotly
```

## 📖 Quick Start

### Step 1: Deploy Infrastructure

**Using Bicep:**
```bash
# Navigate to bicep directory
cd bicep

# Deploy to Azure
az deployment group create \
  --resource-group fabric-governance-rg \
  --template-file tenant-monitoring.bicep \
  --parameters location=eastus \
  --parameters workspaceName=fabric-governance-la \
  --parameters environmentTag=production
```

**Using Terraform (Recommended):**
```bash
# Navigate to terraform directory
cd terraform

# Copy and edit configuration
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Deploy with automated script
# Windows:
deploy.bat

# Linux/macOS:
chmod +x deploy.sh
./deploy.sh

# Or manually:
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

See `terraform/README.md` for detailed Terraform deployment guide.

### Step 2: Configure Environment

Create `.env` file in the root directory:
```bash
# Azure Configuration
AZURE_TENANT_ID=your-tenant-id
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP=fabric-governance-rg

# Log Analytics Configuration
LOG_ANALYTICS_WORKSPACE_ID=your-workspace-id
LOG_ANALYTICS_WORKSPACE_NAME=fabric-governance-la

# Data Collection Configuration
AZURE_MONITOR_DCE_ENDPOINT=https://your-dce.eastus-ingest.monitor.azure.com
AZURE_MONITOR_DCR_IMMUTABLE_ID=dcr-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AZURE_MONITOR_STREAM_NAME=Custom-FabricTenantSettings_CL

# Fabric Configuration
FABRIC_TENANT_ID=your-fabric-tenant-id
FABRIC_TEST_CAPACITY_ID=your-test-capacity-id
FABRIC_PROD_CAPACITY_ID=your-prod-capacity-id

# Security Groups (Optional)
PREVIEW_TESTERS_GROUP_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
PROD_ADMINS_GROUP_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Notification Configuration (Optional)
ALERT_WEBHOOK_URL=https://your-webhook-url
ALERT_EMAIL_ADDRESSES=admin1@company.com,admin2@company.com
```

### Step 3: Export Current Tenant Settings

**Using PowerShell:**
```powershell
# Authenticate with Azure CLI first
az login

# Export current settings
.\powershell\Get-FabricTenantSettings.ps1 `
  -OutputPath ".\baseline\prod-tenant-settings.json" `
  -IncludePreviewFeatures `
  -Verbose
```

**Using Python Notebook:**
```python
# Run the tenant settings monitor notebook
# This will collect settings and send to Log Analytics
%run notebooks/fabric_tenant_settings_monitor.ipynb
```

### Step 4: Compare Environments

```powershell
# Compare TEST vs PROD settings
.\powershell\Compare-TenantSettings.ps1 `
  -TestSettingsPath ".\baseline\test-tenant-settings.json" `
  -ProdSettingsPath ".\baseline\prod-tenant-settings.json" `
  -OutputReport ".\reports\environment-comparison.html" `
  -HighlightPreviewFeatures
```

### Step 5: Set Up Monitoring

```powershell
# Configure daily monitoring with alerts
.\powershell\Monitor-TenantChanges.ps1 `
  -BaselineFile ".\baseline\prod-tenant-settings.json" `
  -AlertOnNewPreviews `
  -AlertOnSettingChanges `
  -WebhookUrl $env:ALERT_WEBHOOK_URL `
  -Schedule Daily
```

## 🔄 Usage Scenarios

### Scenario 1: Safe TEST → PROD Promotion

```powershell
# Automated promotion with governance checks
.\powershell\Deploy-WithGovernance.ps1 `
  -SourceWorkspace "TEST-Workspace" `
  -TargetWorkspace "PROD-Workspace" `
  -ValidateSettings `
  -DisablePreviewFeatures `
  -RequireApproval `
  -RollbackOnFailure `
  -NotifyOnComplete
```

### Scenario 2: Weekly Compliance Report

```python
# Run the compliance reporter notebook
# This generates a comprehensive report with:
# - Current tenant settings
# - Preview features enabled/disabled
# - Configuration drift from baseline
# - Recommended actions
%run notebooks/tenant_compliance_reporter.ipynb
```

### Scenario 3: Monitor New Preview Features

```powershell
# Get notified when Microsoft releases new preview toggles
.\powershell\Monitor-TenantChanges.ps1 `
  -MonitorNewPreviewFeatures `
  -CompareAgainstBaseline ".\baseline\known-features.json" `
  -AlertMethod Teams `
  -TeamsWebhookUrl $env:TEAMS_WEBHOOK
```

### Scenario 4: Bulk Disable Preview Features

```powershell
# Disable all preview features in PROD (before promotion)
.\powershell\Disable-PreviewFeatures.ps1 `
  -TenantId $env:FABRIC_TENANT_ID `
  -Environment Production `
  -ExcludeApprovedPreviews ".\config\approved-previews.json" `
  -DryRun:$false `
  -Verbose
```

## 📊 Log Analytics Queries

### Query 1: Preview Features Over Time
```kql
FabricPreviewFeatures_CL
| where TimeGenerated > ago(30d)
| summarize 
    EnabledCount = countif(IsEnabled == true),
    DisabledCount = countif(IsEnabled == false)
    by bin(TimeGenerated, 1d), Environment_s
| render timechart
```

### Query 2: Recent Tenant Setting Changes
```kql
FabricTenantSettings_CL
| where TimeGenerated > ago(7d)
| extend Changes = parse_json(SettingChanges_s)
| where array_length(Changes) > 0
| project TimeGenerated, SettingName_s, OldValue_s, NewValue_s, ChangedBy_s
| order by TimeGenerated desc
```

### Query 3: Environment Drift Detection
```kql
FabricEnvironmentComparison_CL
| where TimeGenerated > ago(1d)
| where HasDrift_b == true
| project 
    TimeGenerated, 
    SettingPath_s, 
    TestValue_s, 
    ProdValue_s, 
    IsPreviewFeature_b,
    RiskLevel_s
| order by RiskLevel_s desc, TimeGenerated desc
```

### Query 4: Governance Audit Trail
```kql
FabricGovernanceEvents_CL
| where TimeGenerated > ago(30d)
| where EventType_s in ("PreviewDisabled", "PromotionBlocked", "SettingReverted")
| summarize 
    EventCount = count(),
    UniqueActors = dcount(ActorId_s)
    by EventType_s, bin(TimeGenerated, 1d)
| render columnchart
```

## 🛡️ Best Practices

### 1. Preview Feature Management
- ✅ Use security groups to limit preview access to test teams
- ✅ Maintain an approved previews list for controlled rollouts
- ✅ Disable all non-approved previews in PROD
- ✅ Document preview features with risk assessments
- ❌ Never enable previews directly in PROD without TEST validation

### 2. Change Management
- ✅ Take daily snapshots of tenant settings
- ✅ Store baselines in version control (Git)
- ✅ Require approval for tenant setting changes
- ✅ Alert on unexpected configuration drift
- ❌ Don't make manual changes without logging

### 3. TEST → PROD Pipeline
- ✅ Always validate artifacts in TEST first
- ✅ Run automated tests before promotion
- ✅ Disable preview features before PROD deployment
- ✅ Use deployment pipelines for traceability
- ❌ Don't bypass governance checks

### 4. Monitoring & Alerts
- ✅ Set up real-time alerts for new preview toggles
- ✅ Review compliance reports weekly
- ✅ Monitor for unauthorized changes
- ✅ Track promotion success/failure rates
- ❌ Don't ignore drift warnings

## 🔧 Troubleshooting

### Issue: Unable to Access Tenant Settings API

**Symptoms:** 401/403 errors when calling `GetTenantSettingsAsAdmin`

**Solution:**
```bash
# Login with Azure CLI
az login

# Verify you have access to Fabric API
az account get-access-token --resource "https://api.fabric.microsoft.com"

# If needed, switch tenant
az login --tenant YOUR_TENANT_ID
```

### Issue: Preview Features Not Detected

**Symptoms:** Scripts don't identify preview toggles

**Solution:**
```powershell
# Update the preview features reference file
.\powershell\Update-PreviewFeaturesReference.ps1 `
  -RefreshFromAPI `
  -OutputPath ".\config\preview-features.json"
```

### Issue: Log Analytics Ingestion Failures

**Symptoms:** Data not appearing in custom tables

**Solution:**
```bash
# Validate DCR configuration
python notebooks/validate_dcr_configuration.py

# Test ingestion with sample data
python notebooks/test_log_ingestion.py --dry-run
```

## 📚 Additional Resources

- [Fabric Admin REST API Documentation](https://learn.microsoft.com/fabric/admin/admin-overview)
- [Tenant Settings API Reference](https://learn.microsoft.com/rest/api/fabric/admin/tenants/get-tenant-settings)
- [Azure Log Analytics DCR-based Custom Tables](https://learn.microsoft.com/azure/azure-monitor/logs/tutorial-logs-ingestion-portal)
- [Fabric Deployment Pipelines](https://learn.microsoft.com/fabric/cicd/deployment-pipelines/intro-to-deployment-pipelines)

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test your changes thoroughly
4. Submit a pull request with clear description

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues, questions, or feature requests, please:
- Open an issue on GitHub
- Contact the Fabric Admin team
- Review the troubleshooting guide above
