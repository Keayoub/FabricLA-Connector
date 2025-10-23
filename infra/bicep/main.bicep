// ============================================================================
// Fabric Monitoring - Modular Bicep Deployment
// ============================================================================
// This template supports modular deployment of Fabric monitoring components
// Choose which monitoring modules to deploy based on your needs
// ============================================================================

// Required parameters
param lawId string // required: full resourceId('/subscriptions/.../resourceGroups/{rg}/providers/Microsoft.OperationalInsights/workspaces/{workspaceName}')
param workspaceName string // required: Log Analytics Workspace name
param location string = resourceGroup().location

// Data Collection Endpoint configuration
param dceName string = 'dce-fabric-monitoring'

// ============================================================================
// Modular Deployment Options
// ============================================================================
// Choose which monitoring components to deploy
// Each DCR stays under Azure's 10-dataFlow limit

@description('Deploy Spark Monitoring DCR (Livy Sessions, Logs, Metrics, Resource Usage, Jobs, Notebooks - 8 streams)')
param deploySparkMonitoring bool = true

@description('Deploy Pipeline & Dataflow Monitoring DCR (Pipeline runs, Activity runs, Dataflow refreshes, User activity - 4 streams)')
param deployPipelineMonitoring bool = false

@description('Deploy Capacity & Workspace Monitoring DCR (Dataset refresh, Capacity metrics, Workspace events, OneLake storage - 7 streams)')
param deployCapacityMonitoring bool = false

@description('Deploy Admin & Governance Monitoring DCR (Git integration, Permissions, Data lineage, Semantic models - 6 streams)')
param deployAdminMonitoring bool = false

// DCR names for each module
param dcrSparkName string = 'dcr-fabric-spark-monitoring'
param dcrPipelineName string = 'dcr-fabric-pipeline-monitoring'
param dcrCapacityName string = 'dcr-fabric-capacity-monitoring'
param dcrAdminName string = 'dcr-fabric-admin-monitoring'

// Data Collection Endpoint (DCE)
resource dce 'Microsoft.Insights/dataCollectionEndpoints@2022-06-01' = {
  name: dceName
  location: location
  properties: {
    networkAcls: {
      publicNetworkAccess: 'Enabled'
    }
  }
}

// Create all Log Analytics custom tables using the tables module
module fabricTables 'tables-module.bicep' = {
  name: 'deployFabricTables'
  params: {
    lawName: workspaceName
  }
}

// ============================================================================
// Data Collection Rules (DCR) - Modular Deployment
// ============================================================================
// Deploy only the DCRs you need based on the deployment flags
// Each DCR stays under Azure's 10-dataFlow limit

// 1. Spark Monitoring DCR (8 streams)
module dcrSparkModule '../common/dcr-spark-monitoring-template.json' = if (deploySparkMonitoring) {
  name: 'deploySparkDCR'
  params: {
    dcrName: dcrSparkName
    location: location
    dceResourceId: dce.id
    lawResourceId: lawId
  }
  dependsOn: [
    fabricTables
  ]
}

// 2. Pipeline & Dataflow Monitoring DCR (4 streams)
module dcrPipelineModule '../common/dcr-pipeline-monitoring-template.json' = if (deployPipelineMonitoring) {
  name: 'deployPipelineDCR'
  params: {
    dcrName: dcrPipelineName
    location: location
    dceResourceId: dce.id
    lawResourceId: lawId
  }
  dependsOn: [
    fabricTables
  ]
}

// 3. Capacity & Workspace Monitoring DCR (7 streams)
module dcrCapacityModule '../common/dcr-capacity-monitoring-template.json' = if (deployCapacityMonitoring) {
  name: 'deployCapacityDCR'
  params: {
    dcrName: dcrCapacityName
    location: location
    dceResourceId: dce.id
    lawResourceId: lawId
  }
  dependsOn: [
    fabricTables
  ]
}

// 4. Admin & Governance Monitoring DCR (6 streams)
module dcrAdminModule '../common/dcr-admin-monitoring-template.json' = if (deployAdminMonitoring) {
  name: 'deployAdminDCR'
  params: {
    dcrName: dcrAdminName
    location: location
    dceResourceId: dce.id
    lawResourceId: lawId
  }
  dependsOn: [
    fabricTables
  ]
}

// ============================================================================
// Outputs
// ============================================================================

// Data Collection Endpoint
output dceId string = dce.id
output dceLogsIngestionEndpoint string = dce.properties.logsIngestion.endpoint

// DCR Immutable IDs (only output if deployed)
// Note: Outputs will show 'not-deployed' for modules that weren't deployed
output dcrSparkImmutableId string = deploySparkMonitoring ? dcrSparkModule!.outputs.dcrImmutableId : 'not-deployed'
output dcrPipelineImmutableId string = deployPipelineMonitoring ? dcrPipelineModule!.outputs.dcrImmutableId : 'not-deployed'
output dcrCapacityImmutableId string = deployCapacityMonitoring ? dcrCapacityModule!.outputs.dcrImmutableId : 'not-deployed'
output dcrAdminImmutableId string = deployAdminMonitoring ? dcrAdminModule!.outputs.dcrImmutableId : 'not-deployed'

// Deployment status
output deployedModules object = {
  sparkMonitoring: deploySparkMonitoring
  pipelineMonitoring: deployPipelineMonitoring
  capacityMonitoring: deployCapacityMonitoring
  adminMonitoring: deployAdminMonitoring
}

// Table names for reference
output allTableNames array = [
  // Spark Monitoring (8 tables)
  'FabricSparkLivySession_CL'
  'FabricSparkLogs_CL'
  'FabricSparkHistoryMetrics_CL'
  'FabricSparkResourceUsage_CL'
  'FabricSparkJobs_CL'
  'FabricSparkJobRuns_CL'
  'FabricNotebooks_CL'
  'FabricNotebookRuns_CL'
  // Pipeline & Dataflow (4 tables)
  'FabricPipelineRun_CL'
  'FabricPipelineActivityRun_CL'
  'FabricDataflowRun_CL'
  'FabricUserActivity_CL'
  // Capacity & Workspace (7 tables)
  'FabricDatasetRefresh_CL'
  'FabricDatasetMetadata_CL'
  'FabricCapacityMetrics_CL'
  'FabricCapacityWorkloads_CL'
  'FabricWorkspaceEvents_CL'
  'FabricItemDetails_CL'
  'FabricOneLakeStorage_CL'
  // Admin & Governance (6 tables)
  'FabricGitIntegration_CL'
  'FabricPermissions_CL'
  'FabricDataLineage_CL'
  'FabricSemanticModels_CL'
  'FabricRealTimeIntelligence_CL'
  'FabricMirroring_CL'
]
