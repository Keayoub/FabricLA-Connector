// NOTE: This module is NOT required for normal operation.
// Tables will be automatically created by Azure Monitor when data is first ingested via the DCR.
// 
// Use this module only if you need:
// - Custom retention policies different from the default
// - Specific table configurations before data ingestion
// - Pre-defined schema validation
//
// For most use cases, let Azure Monitor auto-create the tables.

param lawName string

// The module is deployed at resource-group scope; the module's resourceGroup() will be the target RG.
resource law 'Microsoft.OperationalInsights/workspaces@2025-02-01' existing = {
  scope: resourceGroup()
  name: lawName
}

resource pipelineRun 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricPipelineRun_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricPipelineRun_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'string' }
        { name: 'PipelineId', type: 'string' }
        { name: 'PipelineName', type: 'string' }
        { name: 'RunId', type: 'string' }
        { name: 'Status', type: 'string' }
        { name: 'StartTime', type: 'datetime' }
        { name: 'EndTime', type: 'datetime' }
        { name: 'DurationMs', type: 'long' }
        { name: 'InvokeType', type: 'string' }
        { name: 'JobType', type: 'string' }
        { name: 'RootActivityRunId', type: 'string' }
      ]
    }
  }
}

resource activityRun 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricPipelineActivityRun_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricPipelineActivityRun_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'string' }
        { name: 'PipelineName', type: 'string' }
        { name: 'ActivityName', type: 'string' }
        { name: 'ActivityType', type: 'string' }
        { name: 'RunId', type: 'string' }
        { name: 'Status', type: 'string' }
        { name: 'StartTimeUtc', type: 'datetime' }
        { name: 'EndTimeUtc', type: 'datetime' }
        { name: 'DurationMs', type: 'long' }
        { name: 'DataRead', type: 'long' }
        { name: 'DataWritten', type: 'long' }
        { name: 'RecordsProcessed', type: 'long' }
        { name: 'ExecutionStatistics', type: 'dynamic' }
        { name: 'ErrorCode', type: 'string' }
        { name: 'ErrorMessage', type: 'string' }
      ]
    }
  }
}

resource dataflowRun 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricDataflowRun_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricDataflowRun_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'string' }
        { name: 'DataflowId', type: 'string' }
        { name: 'DataflowName', type: 'string' }
        { name: 'RunId', type: 'string' }
        { name: 'Status', type: 'string' }
        { name: 'StartTime', type: 'datetime' }
        { name: 'EndTime', type: 'datetime' }
        { name: 'DurationMs', type: 'long' }
        { name: 'InvokeType', type: 'string' }
        { name: 'JobType', type: 'string' }
      ]
    }
  }
}

resource userActivity 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricUserActivity_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricUserActivity_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'string' }
        { name: 'ActivityId', type: 'string' }
        { name: 'UserId', type: 'string' }
        { name: 'UserEmail', type: 'string' }
        { name: 'ActivityType', type: 'string' }
        { name: 'CreationTime', type: 'datetime' }
        { name: 'ItemName', type: 'string' }
        { name: 'WorkspaceName', type: 'string' }
        { name: 'ItemType', type: 'string' }
        { name: 'ObjectId', type: 'string' }
      ]
    }
  }
}

resource accessRequests 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricAccessRequests_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricAccessRequests_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'RequestId', type: 'string' }
        { name: 'RequesterUserId', type: 'string' }
        { name: 'RequesterEmail', type: 'string' }
        { name: 'WorkspaceId', type: 'string' }
        { name: 'WorkspaceName', type: 'string' }
        { name: 'RequestType', type: 'string' }
        { name: 'Status', type: 'string' }
        { name: 'ApproverUserId', type: 'string' }
        { name: 'RequestedDate', type: 'datetime' }
        { name: 'ResponseDate', type: 'datetime' }
      ]
    }
  }
}

resource datasetRefresh 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricDatasetRefresh_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricDatasetRefresh_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'string' }
        { name: 'DatasetId', type: 'string' }
        { name: 'DatasetName', type: 'string' }
        { name: 'RefreshId', type: 'string' }
        { name: 'RefreshType', type: 'string' }
        { name: 'Status', type: 'string' }
        { name: 'StartTime', type: 'datetime' }
        { name: 'EndTime', type: 'datetime' }
        { name: 'DurationMs', type: 'long' }
        { name: 'ServicePrincipalId', type: 'string' }
        { name: 'ErrorCode', type: 'string' }
        { name: 'ErrorMessage', type: 'string' }
        { name: 'RequestId', type: 'string' }
      ]
    }
  }
}

resource datasetMetadata 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricDatasetMetadata_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricDatasetMetadata_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'string' }
        { name: 'DatasetId', type: 'string' }
        { name: 'DatasetName', type: 'string' }
        { name: 'Description', type: 'string' }
        { name: 'Type', type: 'string' }
        { name: 'CreatedDate', type: 'datetime' }
        { name: 'ModifiedDate', type: 'datetime' }
        { name: 'CreatedBy', type: 'string' }
        { name: 'ModifiedBy', type: 'string' }
      ]
    }
  }
}

resource capacityMetrics 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricCapacityMetrics_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricCapacityMetrics_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'CapacityId', type: 'string' }
        { name: 'WorkloadType', type: 'string' }
        { name: 'CpuPercentage', type: 'real' }
        { name: 'MemoryPercentage', type: 'real' }
        { name: 'ActiveRequests', type: 'int' }
        { name: 'QueuedRequests', type: 'int' }
        { name: 'Timestamp', type: 'datetime' }
      ]
    }
  }
}

resource capacityWorkloads 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricCapacityWorkloads_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricCapacityWorkloads_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'CapacityId', type: 'string' }
        { name: 'WorkloadName', type: 'string' }
        { name: 'State', type: 'string' }
        { name: 'MaxMemoryPercentage', type: 'int' }
        { name: 'MaxBackgroundRefreshes', type: 'int' }
      ]
    }
  }
}

resource capacityThrottling 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricCapacityThrottling_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricCapacityThrottling_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'CapacityId', type: 'string' }
        { name: 'WorkspaceId', type: 'string' }
        { name: 'ItemId', type: 'string' }
        { name: 'OperationType', type: 'string' }
        { name: 'ThrottlingReason', type: 'string' }
        { name: 'ThrottledTimeMs', type: 'int' }
        { name: 'BackgroundOperationId', type: 'string' }
      ]
    }
  }
}

resource fabricPermissions 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricPermissions_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 90  // Extended retention for compliance
    schema: {
      name: 'FabricPermissions_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'string' }
        { name: 'CapacityId', type: 'string' }
        { name: 'ItemId', type: 'string' }
        { name: 'ItemName', type: 'string' }
        { name: 'ItemType', type: 'string' }
        { name: 'PrincipalId', type: 'string' }
        { name: 'PrincipalType', type: 'string' }
        { name: 'PrincipalDisplayName', type: 'string' }
        { name: 'Role', type: 'string' }
        { name: 'AccessRight', type: 'string' }
        { name: 'AssignmentType', type: 'string' }
      ]
    }
  }
}

resource fabricDataLineage 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricDataLineage_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 90  // Extended retention for regulatory compliance
    schema: {
      name: 'FabricDataLineage_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'string' }
        { name: 'SourceDatasetId', type: 'string' }
        { name: 'SourceDatasetName', type: 'string' }
        { name: 'TargetDatasetId', type: 'string' }
        { name: 'TargetDatasetName', type: 'string' }
        { name: 'DataflowId', type: 'string' }
        { name: 'DataflowName', type: 'string' }
        { name: 'DatasourceId', type: 'string' }
        { name: 'DatasourceType', type: 'string' }
        { name: 'DependencyType', type: 'string' }
        { name: 'ConnectionDetails', type: 'dynamic' }
        { name: 'LineageType', type: 'string' }
      ]
    }
  }
}

resource fabricSemanticModels 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricSemanticModels_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 60  // Extended retention for BI optimization analysis
    schema: {
      name: 'FabricSemanticModels_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'string' }
        { name: 'DatasetId', type: 'string' }
        { name: 'DatasetName', type: 'string' }
        { name: 'RefreshId', type: 'string' }
        { name: 'RefreshType', type: 'string' }
        { name: 'Status', type: 'string' }
        { name: 'StartTime', type: 'datetime' }
        { name: 'EndTime', type: 'datetime' }
        { name: 'DurationSeconds', type: 'real' }
        { name: 'ServiceExceptionJson', type: 'string' }
        { name: 'UserCount', type: 'int' }
        { name: 'IsDirectQuery', type: 'boolean' }
        { name: 'MetricType', type: 'string' }
      ]
    }
  }
}

// Advanced Workloads Tables
resource fabricRealTimeIntelligence 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricRealTimeIntelligence_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricRealTimeIntelligence_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'string' }
        { name: 'EventstreamId', type: 'string' }
        { name: 'EventstreamName', type: 'string' }
        { name: 'KQLDatabaseId', type: 'string' }
        { name: 'KQLDatabaseName', type: 'string' }
        { name: 'Description', type: 'string' }
        { name: 'CreatedDate', type: 'datetime' }
        { name: 'LastUpdated', type: 'datetime' }
        { name: 'MetricType', type: 'string' }
      ]
    }
  }
}

resource fabricMirroring 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricMirroring_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricMirroring_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'string' }
        { name: 'MirrorId', type: 'string' }
        { name: 'MirrorName', type: 'string' }
        { name: 'Status', type: 'string' }
        { name: 'LastSyncTime', type: 'datetime' }
        { name: 'SyncDurationSeconds', type: 'real' }
        { name: 'SourceConnectionStatus', type: 'string' }
        { name: 'Description', type: 'string' }
        { name: 'CreatedDate', type: 'datetime' }
        { name: 'LastUpdated', type: 'datetime' }
        { name: 'MetricType', type: 'string' }
      ]
    }
  }
}

resource fabricMLAI 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricMLAI_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 60  // Extended retention for ML/AI governance
    schema: {
      name: 'FabricMLAI_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'string' }
        { name: 'ModelId', type: 'string' }
        { name: 'ModelName', type: 'string' }
        { name: 'ExperimentId', type: 'string' }
        { name: 'ExperimentName', type: 'string' }
        { name: 'Description', type: 'string' }
        { name: 'CreatedDate', type: 'datetime' }
        { name: 'LastUpdated', type: 'datetime' }
        { name: 'MetricType', type: 'string' }
      ]
    }
  }
}

// Operational Monitoring Tables

resource fabricOneLakeStorage 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricOneLakeStorage_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricOneLakeStorage_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'string' }
        { name: 'LakehouseId', type: 'string' }
        { name: 'LakehouseName', type: 'string' }
        { name: 'ItemType', type: 'string' }
        { name: 'CreatedDate', type: 'datetime' }
        { name: 'LastUpdated', type: 'datetime' }
        { name: 'TableCount', type: 'int' }
        { name: 'OneLakePath', type: 'string' }
        { name: 'SqlEndpointId', type: 'string' }
        { name: 'Description', type: 'string' }
      ]
    }
  }
}

resource fabricSparkJobs 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricSparkJobs_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricSparkJobs_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'guid' }
        { name: 'JobDefinitionId', type: 'string' }
        { name: 'JobDefinitionName', type: 'string' }
        { name: 'ItemType', type: 'string' }
        { name: 'CreatedDate', type: 'datetime' }
        { name: 'LastModified', type: 'datetime' }
        { name: 'Language', type: 'string' }
        { name: 'MainClass', type: 'string' }
        { name: 'MainFile', type: 'string' }
        { name: 'Arguments', type: 'dynamic' }
        { name: 'Libraries', type: 'dynamic' }
        { name: 'Description', type: 'string' }
      ]
    }
  }
}

resource fabricSparkJobRuns 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricSparkJobRuns_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricSparkJobRuns_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'guid' }
        { name: 'JobDefinitionId', type: 'string' }
        { name: 'JobDefinitionName', type: 'string' }
        { name: 'RunId', type: 'string' }
        { name: 'Status', type: 'string' }
        { name: 'StartTimeUtc', type: 'datetime' }
        { name: 'EndTimeUtc', type: 'datetime' }
        { name: 'DurationMs', type: 'long' }
        { name: 'JobType', type: 'string' }
        { name: 'ItemType', type: 'string' }
      ]
    }
  }
}

resource fabricNotebooks 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricNotebooks_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricNotebooks_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'guid' }
        { name: 'NotebookId', type: 'string' }
        { name: 'NotebookName', type: 'string' }
        { name: 'ItemType', type: 'string' }
        { name: 'CreatedDate', type: 'datetime' }
        { name: 'LastModified', type: 'datetime' }
        { name: 'Description', type: 'string' }
      ]
    }
  }
}

resource fabricNotebookRuns 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricNotebookRuns_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricNotebookRuns_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'string' }
        { name: 'NotebookId', type: 'string' }
        { name: 'NotebookName', type: 'string' }
        { name: 'RunId', type: 'string' }
        { name: 'Status', type: 'string' }
        { name: 'StartTimeUtc', type: 'datetime' }
        { name: 'EndTimeUtc', type: 'datetime' }
        { name: 'DurationMs', type: 'long' }
        { name: 'ItemType', type: 'string' }
      ]
    }
  }
}

resource fabricGitIntegration 'Microsoft.OperationalInsights/workspaces/tables@2025-02-01' = {
  parent: law
  name: 'FabricGitIntegration_CL'
  properties: {
    plan: 'Analytics'
    retentionInDays: 30
    schema: {
      name: 'FabricGitIntegration_CL'
      columns: [
        { name: 'TimeGenerated', type: 'datetime' }
        { name: 'WorkspaceId', type: 'guid' }
        { name: 'GitProvider', type: 'string' }
        { name: 'OrganizationName', type: 'string' }
        { name: 'ProjectName', type: 'string' }
        { name: 'RepositoryName', type: 'string' }
        { name: 'BranchName', type: 'string' }
        { name: 'DirectoryName', type: 'string' }
        { name: 'ConnectionId', type: 'string' }
        { name: 'ConnectionStatus', type: 'string' }
        { name: 'ItemType', type: 'string' }
      ]
    }
  }
}
