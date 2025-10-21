terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~>2.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Get current client configuration
data "azurerm_client_config" "current" {}

# Variables for customization
variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-fabric-monitoring"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "Canada Central"
}

variable "log_analytics_workspace_name" {
  description = "Name of the Log Analytics workspace"
  type        = string
  default     = "law-fabric-monitoring"
}

variable "data_collection_endpoint_name" {
  description = "Name of the Data Collection Endpoint"
  type        = string
  default     = "dce-fabric-monitoring"
}

variable "data_collection_rule_name" {
  description = "Name of the Data Collection Rule"
  type        = string
  default     = "dcr-fabric-monitoring"
}

# Modular deployment options - choose what to deploy
# DCR deployment options - granular control
variable "deploy_main_dcr" {
  description = "Deploy main DCR (22 streams - WILL FAIL due to 10-stream limit, needs splitting)"
  type        = bool
  default     = false
}

variable "deploy_spark_monitoring" {
  description = "Deploy Spark Monitoring DCR (Livy Sessions, Logs, Metrics, Resource Usage, Jobs, Notebooks - 8 streams)"
  type        = bool
  default     = false
}

variable "deploy_pipeline_monitoring" {
  description = "Deploy Pipeline & Dataflow Monitoring (subset of main DCR)"
  type        = bool
  default     = false
}

variable "deploy_capacity_monitoring" {
  description = "Deploy Capacity & Workspace Monitoring (subset of main DCR)"
  type        = bool
  default     = false
}

variable "deploy_admin_monitoring" {
  description = "Deploy Admin Monitoring (Git, Permissions, Lineage, Semantic Models, Real-time, Mirroring - 6 streams)"
  type        = bool
  default     = false
}

# Resource Group
resource "azurerm_resource_group" "log_analytics_rg" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    Environment = "Production"
    Purpose     = "Fabric Monitoring"
    CreatedBy   = "Terraform"
  }
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "la" {
  name                = var.log_analytics_workspace_name
  location            = azurerm_resource_group.log_analytics_rg.location
  resource_group_name = azurerm_resource_group.log_analytics_rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = {
    Environment = "Production"
    Purpose     = "Fabric Monitoring"
    CreatedBy   = "Terraform"
  }
}

# Custom Log Analytics Tables for Fabric Monitoring
# Deploy tables using external ARM template (consistent with DCR approach)
resource "azurerm_resource_group_template_deployment" "fabric_tables" {
  name                = "fabric-tables-deployment"
  resource_group_name = azurerm_resource_group.log_analytics_rg.name
  deployment_mode     = "Incremental"

  template_content = file("${path.module}/../common/tables-template.json")
  parameters_content = jsonencode({
    workspaceName = {
      value = azurerm_log_analytics_workspace.la.name
    }
  })
}

# Data Collection Endpoint
resource "azurerm_monitor_data_collection_endpoint" "dce" {
  name                = var.data_collection_endpoint_name
  location            = azurerm_resource_group.log_analytics_rg.location
  resource_group_name = azurerm_resource_group.log_analytics_rg.name

  tags = {
    Environment = "Production"
    Purpose     = "Fabric Monitoring"
    CreatedBy   = "Terraform"
  }
}

# Data Collection Rule for existing workloads (using ARM template)
# Note: Azure DCR has a 10 dataFlows limit. This DCR has 22 streams and WILL FAIL validation.
# Only enable this if you split the template into multiple DCRs first.
resource "azurerm_resource_group_template_deployment" "dcr" {
  count               = var.deploy_main_dcr ? 1 : 0
  name                = "fabric-dcr-deployment"
  resource_group_name = azurerm_resource_group.log_analytics_rg.name
  deployment_mode     = "Incremental"

  template_content = file("${path.module}/../common/dcr-template.json")

  parameters_content = jsonencode({
    dcrName = {
      value = var.data_collection_rule_name
    }
    location = {
      value = azurerm_resource_group.log_analytics_rg.location
    }
    dceResourceId = {
      value = azurerm_monitor_data_collection_endpoint.dce.id
    }
    lawResourceId = {
      value = azurerm_log_analytics_workspace.la.id
    }
  })

  depends_on = [
    azurerm_monitor_data_collection_endpoint.dce,
    azurerm_log_analytics_workspace.la,
    azurerm_resource_group_template_deployment.fabric_tables
  ]
}

# ============================================================================
# MODULAR DCR DEPLOYMENTS - Each component can be deployed independently
# ============================================================================
# Streams: FabricSparkLivySession, FabricSparkLogs, FabricSparkHistoryMetrics, FabricSparkResourceUsage,
#          FabricSparkJobs, FabricSparkJobRuns, FabricNotebooks, FabricNotebookRuns (8 streams)
resource "azurerm_resource_group_template_deployment" "dcr_spark" {
  count               = var.deploy_spark_monitoring ? 1 : 0
  name                = "fabric-dcr-spark-deployment"
  resource_group_name = azurerm_resource_group.log_analytics_rg.name
  deployment_mode     = "Incremental"

  template_content = file("${path.module}/../common/dcr-spark-monitoring-template.json")

  parameters_content = jsonencode({
    dcrName = {
      value = "${var.data_collection_rule_name}-spark"
    }
    location = {
      value = azurerm_resource_group.log_analytics_rg.location
    }
    dceResourceId = {
      value = azurerm_monitor_data_collection_endpoint.dce.id
    }
    lawResourceId = {
      value = azurerm_log_analytics_workspace.la.id
    }
  })

  depends_on = [
    azurerm_monitor_data_collection_endpoint.dce,
    azurerm_log_analytics_workspace.la,
    azurerm_resource_group_template_deployment.fabric_tables
  ]
}

# DCR Module 2: Pipeline & Dataflow Monitoring
# Streams: FabricPipelineRun, FabricPipelineActivityRun, FabricDataflowRun, FabricUserActivity
resource "azurerm_resource_group_template_deployment" "dcr_pipeline" {
  count               = var.deploy_pipeline_monitoring ? 1 : 0
  name                = "fabric-dcr-pipeline-deployment"
  resource_group_name = azurerm_resource_group.log_analytics_rg.name
  deployment_mode     = "Incremental"

  template_content = file("${path.module}/../common/dcr-pipeline-monitoring-template.json")

  parameters_content = jsonencode({
    dcrName = {
      value = "${var.data_collection_rule_name}-pipeline"
    }
    location = {
      value = azurerm_resource_group.log_analytics_rg.location
    }
    dceResourceId = {
      value = azurerm_monitor_data_collection_endpoint.dce.id
    }
    lawResourceId = {
      value = azurerm_log_analytics_workspace.la.id
    }
  })

  depends_on = [
    azurerm_monitor_data_collection_endpoint.dce,
    azurerm_log_analytics_workspace.la,
    azurerm_resource_group_template_deployment.fabric_tables
  ]
}

# DCR Module 3: Capacity & Workspace Monitoring
# Streams: FabricDatasetRefresh, FabricDatasetMetadata, FabricCapacityMetrics, 
#          FabricCapacityWorkloads, FabricWorkspaceEvents, FabricItemDetails, FabricOneLakeStorage
resource "azurerm_resource_group_template_deployment" "dcr_capacity" {
  count               = var.deploy_capacity_monitoring ? 1 : 0
  name                = "fabric-dcr-capacity-deployment"
  resource_group_name = azurerm_resource_group.log_analytics_rg.name
  deployment_mode     = "Incremental"

  template_content = file("${path.module}/../common/dcr-capacity-monitoring-template.json")

  parameters_content = jsonencode({
    dcrName = {
      value = "${var.data_collection_rule_name}-capacity"
    }
    location = {
      value = azurerm_resource_group.log_analytics_rg.location
    }
    dceResourceId = {
      value = azurerm_monitor_data_collection_endpoint.dce.id
    }
    lawResourceId = {
      value = azurerm_log_analytics_workspace.la.id
    }
  })

  depends_on = [
    azurerm_monitor_data_collection_endpoint.dce,
    azurerm_log_analytics_workspace.la,
    azurerm_resource_group_template_deployment.fabric_tables
  ]
}

# DCR Module 4: Admin & Governance Monitoring
# Streams: FabricGitIntegration, FabricPermissions, FabricDataLineage, FabricSemanticModels,
#          FabricRealTimeIntelligence, FabricMirroring (6 streams)
resource "azurerm_resource_group_template_deployment" "dcr_admin" {
  count               = var.deploy_admin_monitoring ? 1 : 0
  name                = "fabric-dcr-admin-deployment"
  resource_group_name = azurerm_resource_group.log_analytics_rg.name
  deployment_mode     = "Incremental"

  template_content = file("${path.module}/../common/dcr-admin-monitoring-template.json")

  parameters_content = jsonencode({
    dcrName = {
      value = "${var.data_collection_rule_name}-admin"
    }
    location = {
      value = azurerm_resource_group.log_analytics_rg.location
    }
    dceResourceId = {
      value = azurerm_monitor_data_collection_endpoint.dce.id
    }
    lawResourceId = {
      value = azurerm_log_analytics_workspace.la.id
    }
  })

  depends_on = [
    azurerm_monitor_data_collection_endpoint.dce,
    azurerm_log_analytics_workspace.la,
    azurerm_resource_group_template_deployment.fabric_tables
  ]
}

# Service Principal configuration
variable "service_principal_object_id" {
  description = "Object ID of the existing service principal to grant DCR permissions"
  type        = string
  default     = ""
}

# ============================================================================
# ROLE ASSIGNMENTS - Monitoring Metrics Publisher for each DCR module
# ============================================================================

# Role Assignment: Main DCR (if deployed)
resource "azurerm_role_assignment" "dcr_monitoring_metrics_publisher" {
  count                = var.service_principal_object_id != "" && var.deploy_main_dcr ? 1 : 0
  scope                = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${azurerm_resource_group.log_analytics_rg.name}/providers/Microsoft.Insights/dataCollectionRules/${var.data_collection_rule_name}"
  role_definition_name = "Monitoring Metrics Publisher"
  principal_id         = var.service_principal_object_id
  principal_type       = "ServicePrincipal"

  depends_on = [azurerm_resource_group_template_deployment.dcr]
}

# Role Assignment: Spark Monitoring DCR
resource "azurerm_role_assignment" "dcr_spark_monitoring_metrics_publisher" {
  count                = var.service_principal_object_id != "" && var.deploy_spark_monitoring ? 1 : 0
  scope                = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${azurerm_resource_group.log_analytics_rg.name}/providers/Microsoft.Insights/dataCollectionRules/${var.data_collection_rule_name}-spark"
  role_definition_name = "Monitoring Metrics Publisher"
  principal_id         = var.service_principal_object_id
  principal_type       = "ServicePrincipal"

  depends_on = [azurerm_resource_group_template_deployment.dcr_spark]
}

# Role Assignment: Pipeline Monitoring DCR
resource "azurerm_role_assignment" "dcr_pipeline_monitoring_metrics_publisher" {
  count                = var.service_principal_object_id != "" && var.deploy_pipeline_monitoring ? 1 : 0
  scope                = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${azurerm_resource_group.log_analytics_rg.name}/providers/Microsoft.Insights/dataCollectionRules/${var.data_collection_rule_name}-pipeline"
  role_definition_name = "Monitoring Metrics Publisher"
  principal_id         = var.service_principal_object_id
  principal_type       = "ServicePrincipal"

  depends_on = [azurerm_resource_group_template_deployment.dcr_pipeline]
}

# Role Assignment: Capacity Monitoring DCR
resource "azurerm_role_assignment" "dcr_capacity_monitoring_metrics_publisher" {
  count                = var.service_principal_object_id != "" && var.deploy_capacity_monitoring ? 1 : 0
  scope                = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${azurerm_resource_group.log_analytics_rg.name}/providers/Microsoft.Insights/dataCollectionRules/${var.data_collection_rule_name}-capacity"
  role_definition_name = "Monitoring Metrics Publisher"
  principal_id         = var.service_principal_object_id
  principal_type       = "ServicePrincipal"

  depends_on = [azurerm_resource_group_template_deployment.dcr_capacity]
}

# Role Assignment: Admin Monitoring DCR
resource "azurerm_role_assignment" "dcr_admin_monitoring_metrics_publisher" {
  count                = var.service_principal_object_id != "" && var.deploy_admin_monitoring ? 1 : 0
  scope                = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${azurerm_resource_group.log_analytics_rg.name}/providers/Microsoft.Insights/dataCollectionRules/${var.data_collection_rule_name}-admin"
  role_definition_name = "Monitoring Metrics Publisher"
  principal_id         = var.service_principal_object_id
  principal_type       = "ServicePrincipal"

  depends_on = [azurerm_resource_group_template_deployment.dcr_admin]
}

# ============================================================================
# OUTPUTS - DCR IDs and Immutable IDs for each deployed module
# ============================================================================

# Base Infrastructure Outputs
output "resource_group_name" {
  value       = azurerm_resource_group.log_analytics_rg.name
  description = "The name of the resource group"
}

output "log_analytics_workspace_id" {
  value       = azurerm_log_analytics_workspace.la.id
  description = "The ID of the Log Analytics workspace"
}

output "log_analytics_workspace_name" {
  value       = azurerm_log_analytics_workspace.la.name
  description = "The name of the Log Analytics workspace"
}

output "data_collection_endpoint_id" {
  value       = azurerm_monitor_data_collection_endpoint.dce.id
  description = "The ID of the Data Collection Endpoint"
}

output "data_collection_endpoint_logs_ingestion_endpoint" {
  value       = azurerm_monitor_data_collection_endpoint.dce.logs_ingestion_endpoint
  description = "The logs ingestion endpoint URL for the DCE"
}

# Main DCR Outputs (Legacy - disabled by default)
output "data_collection_rule_id" {
  value       = var.deploy_main_dcr ? "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${azurerm_resource_group.log_analytics_rg.name}/providers/Microsoft.Insights/dataCollectionRules/${var.data_collection_rule_name}" : "Not deployed (deploy_main_dcr=false)"
  description = "The ID of the Data Collection Rule (main - legacy, has 22 streams)"
}

output "data_collection_rule_immutable_id" {
  value       = var.deploy_main_dcr ? jsondecode(azurerm_resource_group_template_deployment.dcr[0].output_content)["dcrImmutableId"]["value"] : "Not deployed (deploy_main_dcr=false)"
  description = "The immutable ID of the Data Collection Rule (main, used for API calls)"
}

# Spark Monitoring DCR Outputs
output "dcr_spark_id" {
  value       = var.deploy_spark_monitoring ? "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${azurerm_resource_group.log_analytics_rg.name}/providers/Microsoft.Insights/dataCollectionRules/${var.data_collection_rule_name}-spark" : "Not deployed"
  description = "Resource ID of Spark Monitoring DCR"
}

output "dcr_spark_immutable_id" {
  value       = var.deploy_spark_monitoring ? jsondecode(azurerm_resource_group_template_deployment.dcr_spark[0].output_content)["dcrImmutableId"]["value"] : "Not deployed"
  description = "Immutable ID for Spark Monitoring DCR (use in API calls)"
}

# Pipeline Monitoring DCR Outputs
output "dcr_pipeline_id" {
  value       = var.deploy_pipeline_monitoring ? "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${azurerm_resource_group.log_analytics_rg.name}/providers/Microsoft.Insights/dataCollectionRules/${var.data_collection_rule_name}-pipeline" : "Not deployed"
  description = "Resource ID of Pipeline Monitoring DCR"
}

output "dcr_pipeline_immutable_id" {
  value       = var.deploy_pipeline_monitoring ? jsondecode(azurerm_resource_group_template_deployment.dcr_pipeline[0].output_content)["dcrImmutableId"]["value"] : "Not deployed"
  description = "Immutable ID for Pipeline Monitoring DCR (use in API calls)"
}

# Capacity Monitoring DCR Outputs
output "dcr_capacity_id" {
  value       = var.deploy_capacity_monitoring ? "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${azurerm_resource_group.log_analytics_rg.name}/providers/Microsoft.Insights/dataCollectionRules/${var.data_collection_rule_name}-capacity" : "Not deployed"
  description = "Resource ID of Capacity Monitoring DCR"
}

output "dcr_capacity_immutable_id" {
  value       = var.deploy_capacity_monitoring ? jsondecode(azurerm_resource_group_template_deployment.dcr_capacity[0].output_content)["dcrImmutableId"]["value"] : "Not deployed"
  description = "Immutable ID for Capacity Monitoring DCR (use in API calls)"
}

# Admin Monitoring DCR Outputs
output "dcr_admin_id" {
  value       = var.deploy_admin_monitoring ? "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${azurerm_resource_group.log_analytics_rg.name}/providers/Microsoft.Insights/dataCollectionRules/${var.data_collection_rule_name}-admin" : "Not deployed"
  description = "Resource ID of Admin Monitoring DCR"
}

output "dcr_admin_immutable_id" {
  value       = var.deploy_admin_monitoring ? jsondecode(azurerm_resource_group_template_deployment.dcr_admin[0].output_content)["dcrImmutableId"]["value"] : "Not deployed"
  description = "Immutable ID for Admin Monitoring DCR (use in API calls)"
}

# Deployment Summary
output "deployed_monitoring_modules" {
  value = {
    spark_monitoring    = var.deploy_spark_monitoring
    pipeline_monitoring = var.deploy_pipeline_monitoring
    capacity_monitoring = var.deploy_capacity_monitoring
    admin_monitoring    = var.deploy_admin_monitoring
  }
  description = "Summary of which monitoring modules are deployed"
}

output "service_principal_role_assignment" {
  value       = var.service_principal_object_id != "" ? "Monitoring Metrics Publisher role assigned to service principal ${var.service_principal_object_id}" : "No service principal provided - set service_principal_object_id variable"
  description = "Status of the service principal role assignment"
}

output "tenant_id" {
  value       = data.azurerm_client_config.current.tenant_id
  description = "The tenant ID for authentication"
}

