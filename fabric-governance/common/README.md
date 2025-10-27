# Common ARM Templates

This folder contains **shared ARM templates** used by both Bicep and Terraform deployments for the Fabric Tenant Governance solution.

## 📦 Files

| File | Purpose | Used By |
|------|---------|---------|
| **tables-template.json** | Defines 4 custom Log Analytics tables with DCR-based schemas | Bicep + Terraform |
| **dcr-template.json** | Defines Data Collection Rule with 4 stream declarations | Bicep + Terraform |

## 🎯 Why Shared Templates?

### Single Source of Truth
- ✅ One definition for table schemas
- ✅ One definition for DCR streams
- ✅ Consistency between deployment methods
- ✅ Easier maintenance and updates

### DRY Principle
- ❌ No duplication between Bicep and Terraform
- ✅ Change once, applies to both
- ✅ Reduced risk of schema drift

## 📊 Tables Defined

### 1. FabricTenantSettings_CL
Complete tenant settings snapshots with preview feature detection.

**Columns:**
- TimeGenerated (datetime)
- TenantId (string)
- SettingName (string)
- Title (string)
- Enabled (boolean)
- CanSpecifySecurityGroups (boolean)
- TenantSettingGroup (string)
- IsPreviewFeature (boolean)
- PreviewIndicators (string)
- CollectionTimestamp (datetime)

### 2. FabricPreviewFeatures_CL
Preview feature tracking and change detection.

**Columns:**
- TimeGenerated (datetime)
- TenantId (string)
- SettingName (string)
- Title (string)
- IsEnabled (boolean)
- WasEnabled (boolean)
- ChangeDetected (boolean)
- Environment (string)
- RiskLevel (string)

### 3. FabricGovernanceEvents_CL
Governance action audit trail.

**Columns:**
- TimeGenerated (datetime)
- TenantId (string)
- EventType (string)
- EventDescription (string)
- ActorId (string)
- TargetResource (string)
- Success (boolean)
- ErrorMessage (string)

### 4. FabricEnvironmentComparison_CL
TEST vs PROD drift analysis.

**Columns:**
- TimeGenerated (datetime)
- SettingPath (string)
- TestValue (string)
- ProdValue (string)
- HasDrift (boolean)
- IsPreviewFeature (boolean)
- RiskLevel (string)

## 🔧 DCR Configuration

### Stream Declarations
The DCR template defines 4 independent streams:

1. **Custom-FabricTenantSettings_CL**
2. **Custom-FabricPreviewFeatures_CL**
3. **Custom-FabricGovernanceEvents_CL**
4. **Custom-FabricEnvironmentComparison_CL**

### Data Flows
Each stream maps to its corresponding custom table:
- Stream → Log Analytics Workspace → Custom Table
- Transform: `source` (no transformation)
- Output: Same as stream name

## 🏗️ Usage

### In Bicep

```bicep
// Reference from bicep/tenant-monitoring.bicep
// (Bicep can inline or reference ARM templates)
```

### In Terraform

```hcl
# Reference from terraform/main.tf
resource "azurerm_resource_group_template_deployment" "custom_tables" {
  template_content = file("${path.module}/../common/tables-template.json")
  # ...
}

resource "azurerm_resource_group_template_deployment" "dcr" {
  template_content = file("${path.module}/../common/dcr-template.json")
  # ...
}
```

## 🔄 Updating Templates

When updating these templates:

1. **Test thoroughly** - Changes affect both Bicep and Terraform
2. **Update schema versions** - Keep API versions current
3. **Validate JSON** - Ensure valid ARM template syntax
4. **Test both deployment methods** - Verify Bicep and Terraform work
5. **Update documentation** - Keep README and FILE_INDEX current

### Schema Changes

If you modify table schemas:
- ✅ Add new columns at the end
- ❌ Don't remove existing columns (Log Analytics limitation)
- ✅ Update Python/PowerShell scripts to match new schema
- ✅ Test data ingestion after deployment

## 📝 ARM Template Parameters

### tables-template.json
```json
{
  "workspaceName": "string",      // Name of Log Analytics workspace
  "retentionInDays": "int"        // Data retention (30-730 days)
}
```

### dcr-template.json
```json
{
  "dcrName": "string",           // Name of the DCR
  "location": "string",          // Azure region
  "dceResourceId": "string",     // DCE resource ID
  "lawResourceId": "string"      // Log Analytics workspace resource ID
}
```

## 🔒 Best Practices

### Versioning
- Use semantic versioning for major schema changes
- Document breaking changes in comments
- Keep API versions up-to-date

### Testing
- Validate JSON syntax before committing
- Deploy to test environment first
- Verify data ingestion after changes

### Documentation
- Document all column purposes
- Explain any custom transformations
- Note dependencies between templates

## 📚 References

- [ARM Template Syntax](https://learn.microsoft.com/azure/azure-resource-manager/templates/syntax)
- [Log Analytics Custom Tables](https://learn.microsoft.com/azure/azure-monitor/logs/create-custom-table)
- [Data Collection Rules](https://learn.microsoft.com/azure/azure-monitor/essentials/data-collection-rule-overview)
- [Logs Ingestion API](https://learn.microsoft.com/azure/azure-monitor/logs/logs-ingestion-api-overview)

---

**Version**: 1.0.0  
**Last Updated**: January 2025  
**Maintained By**: Fabric Governance Team
