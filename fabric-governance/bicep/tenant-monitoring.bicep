// ============================================================================
// Fabric Tenant Governance & Preview Feature Management Infrastructure
// ============================================================================
// This Bicep template deploys the Azure infrastructure required for monitoring
// Fabric tenant settings, preview features, and governance automation.
//
// Resources created:
// - Log Analytics Workspace (for storing tenant settings data)
// - Data Collection Endpoint (DCE) for logs ingestion
// - Data Collection Rule (DCR) for tenant settings stream
// - Custom Log Analytics Tables (DCR-based)
// - Action Group for alerts
// - Alert Rules for configuration changes
// ============================================================================

// Parameters
@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Name of the Log Analytics workspace')
param workspaceName string = 'fabric-governance-la'

@description('Log Analytics workspace SKU')
@allowed([
  'PerGB2018'
  'CapacityReservation'
])
param workspaceSku string = 'PerGB2018'

@description('Data retention in days (30-730)')
@minValue(30)
@maxValue(730)
param retentionInDays int = 90

@description('Environment tag (e.g., production, test)')
param environmentTag string = 'production'

@description('Email addresses for alert notifications (comma-separated)')
param alertEmailAddresses string = ''

// Variables
var dceNameVar = 'dce-${workspaceName}'
var dcrNameVar = 'dcr-${workspaceName}-tenantsettings'
var actionGroupName = 'ag-${workspaceName}-alerts'
var alertRulePrefix = 'alert-${workspaceName}'

// ============================================================================
// Log Analytics Workspace
// ============================================================================
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: workspaceName
  location: location
  properties: {
    sku: {
      name: workspaceSku
    }
    retentionInDays: retentionInDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
  tags: {
    Environment: environmentTag
    Purpose: 'FabricTenantGovernance'
    ManagedBy: 'Bicep'
  }
}

// ============================================================================
// Custom DCR-based Tables (using shared ARM template)
// ============================================================================
// Deploy custom tables using the shared ARM template in ../common/
// This ensures consistency between Bicep and Terraform deployments

module customTables '../common/tables-template.json' = {
  name: 'fabric-governance-tables-deployment'
  params: {
    workspaceName: logAnalyticsWorkspace.name
    retentionInDays: retentionInDays
  }
}

// ============================================================================
// Data Collection Endpoint (DCE)
// ============================================================================
resource dataCollectionEndpoint 'Microsoft.Insights/dataCollectionEndpoints@2022-06-01' = {
  name: dceNameVar
  location: location
  properties: {
    networkAcls: {
      publicNetworkAccess: 'Enabled'
    }
  }
  tags: {
    Environment: environmentTag
    Purpose: 'FabricTenantGovernance'
  }
}

// ============================================================================
// Data Collection Rule (DCR) using shared ARM template
// ============================================================================
// Deploy DCR using the shared ARM template in ../common/
// This ensures consistency between Bicep and Terraform deployments

module dataCollectionRule '../common/dcr-template.json' = {
  name: 'fabric-governance-dcr-deployment'
  params: {
    dcrName: dcrNameVar
    location: location
    dceResourceId: dataCollectionEndpoint.id
    lawResourceId: logAnalyticsWorkspace.id
  }
  dependsOn: [
    customTables // Ensure tables exist before DCR
  ]
}

// ============================================================================
// Action Group for Alerts
// ============================================================================
resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = if (!empty(alertEmailAddresses)) {
  name: actionGroupName
  location: 'global'
  properties: {
    groupShortName: 'FabricGov'
    enabled: true
    emailReceivers: [for email in split(alertEmailAddresses, ','): {
      name: 'Email-${replace(email, '@', '-at-')}'
      emailAddress: trim(email)
      useCommonAlertSchema: true
    }]
  }
  tags: {
    Environment: environmentTag
    Purpose: 'FabricTenantGovernance'
  }
}

// ============================================================================
// Alert Rule: New Preview Features Detected
// ============================================================================
resource alertNewPreviewFeatures 'Microsoft.Insights/scheduledQueryRules@2023-03-15-preview' = if (!empty(alertEmailAddresses)) {
  name: '${alertRulePrefix}-new-preview-features'
  location: location
  properties: {
    displayName: 'Fabric: New Preview Features Detected'
    description: 'Alert when new preview features are detected in tenant settings'
    severity: 2
    enabled: true
    evaluationFrequency: 'PT1H'
    windowSize: 'PT1H'
    scopes: [
      logAnalyticsWorkspace.id
    ]
    criteria: {
      allOf: [
        {
          query: '''
            FabricTenantSettings_CL
            | where TimeGenerated > ago(1h)
            | where IsPreviewFeature_b == true
            | summarize NewPreviews = dcount(SettingName_s) by TenantId_s
            | where NewPreviews > 0
          '''
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    actions: {
      actionGroups: [
        actionGroup.id
      ]
    }
  }
  tags: {
    Environment: environmentTag
    Purpose: 'FabricTenantGovernance'
  }
}

// ============================================================================
// Alert Rule: Preview Features Enabled in Production
// ============================================================================
resource alertPreviewEnabled 'Microsoft.Insights/scheduledQueryRules@2023-03-15-preview' = if (!empty(alertEmailAddresses)) {
  name: '${alertRulePrefix}-preview-enabled-prod'
  location: location
  properties: {
    displayName: 'Fabric: Preview Features Enabled in Production'
    description: 'Alert when preview features are enabled (should be disabled in PROD)'
    severity: 1
    enabled: true
    evaluationFrequency: 'PT30M'
    windowSize: 'PT30M'
    scopes: [
      logAnalyticsWorkspace.id
    ]
    criteria: {
      allOf: [
        {
          query: '''
            FabricTenantSettings_CL
            | where TimeGenerated > ago(30m)
            | where IsPreviewFeature_b == true and Enabled_b == true
            | summarize EnabledPreviews = dcount(SettingName_s) by TenantId_s
          '''
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    actions: {
      actionGroups: [
        actionGroup.id
      ]
    }
  }
  tags: {
    Environment: environmentTag
    Purpose: 'FabricTenantGovernance'
  }
}

// ============================================================================
// Outputs
// ============================================================================
output workspaceId string = logAnalyticsWorkspace.id
output workspaceName string = logAnalyticsWorkspace.name
output workspaceCustomerId string = logAnalyticsWorkspace.properties.customerId
output dceEndpoint string = dataCollectionEndpoint.properties.logsIngestion.endpoint
output dcrImmutableId string = dataCollectionRule.outputs.dcrImmutableId
output dcrId string = dataCollectionRule.outputs.dcrId
output actionGroupId string = !empty(alertEmailAddresses) ? actionGroup.id : ''
