# ============================================================================
# Fabric Tenant Governance & Preview Feature Management Infrastructure
# Terraform Implementation
# ============================================================================
# This Terraform configuration deploys the Azure infrastructure required for
# monitoring Fabric tenant settings, preview features, and governance automation.
#
# Resources created:
# - Log Analytics Workspace (for storing tenant settings data)
# - Data Collection Endpoint (DCE) for logs ingestion
# - Data Collection Rule (DCR) for tenant settings stream
# - Custom Log Analytics Tables (DCR-based)
# - Action Group for alerts
# - Alert Rules for configuration changes
# ============================================================================

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Get current client configuration
data "azurerm_client_config" "current" {}

# ============================================================================
# Variables
# ============================================================================

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-fabric-governance"
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "eastus"
}

variable "workspace_name" {
  description = "Name of the Log Analytics workspace"
  type        = string
  default     = "fabric-governance-la"
}

variable "workspace_sku" {
  description = "Log Analytics workspace SKU"
  type        = string
  default     = "PerGB2018"
  validation {
    condition     = contains(["PerGB2018", "CapacityReservation"], var.workspace_sku)
    error_message = "Workspace SKU must be either PerGB2018 or CapacityReservation."
  }
}

variable "retention_in_days" {
  description = "Data retention in days (30-730)"
  type        = number
  default     = 90
  validation {
    condition     = var.retention_in_days >= 30 && var.retention_in_days <= 730
    error_message = "Retention must be between 30 and 730 days."
  }
}

variable "environment_tag" {
  description = "Environment tag (e.g., production, test)"
  type        = string
  default     = "production"
}

variable "alert_email_addresses" {
  description = "Email addresses for alert notifications (comma-separated)"
  type        = string
  default     = ""
}

variable "enable_alerts" {
  description = "Enable alert rules and action group"
  type        = bool
  default     = true
}

# ============================================================================
# Local Variables
# ============================================================================

locals {
  dce_name          = "dce-${var.workspace_name}"
  dcr_name          = "dcr-${var.workspace_name}-tenantsettings"
  action_group_name = "ag-${var.workspace_name}-alerts"
  alert_rule_prefix = "alert-${var.workspace_name}"
  
  # Parse email addresses
  email_addresses = var.alert_email_addresses != "" ? split(",", var.alert_email_addresses) : []
  
  # Common tags
  common_tags = {
    Environment = var.environment_tag
    Purpose     = "FabricTenantGovernance"
    ManagedBy   = "Terraform"
  }
}

# ============================================================================
# Resource Group
# ============================================================================

resource "azurerm_resource_group" "governance" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.common_tags
}

# ============================================================================
# Log Analytics Workspace
# ============================================================================

resource "azurerm_log_analytics_workspace" "governance" {
  name                = var.workspace_name
  location            = azurerm_resource_group.governance.location
  resource_group_name = azurerm_resource_group.governance.name
  sku                 = var.workspace_sku
  retention_in_days   = var.retention_in_days

  tags = local.common_tags
}

# ============================================================================
# Custom DCR-based Tables
# ============================================================================
# Note: Custom tables are deployed using ARM template due to Terraform provider limitations
# The azurerm provider doesn't fully support custom table schema definitions yet
# Template is shared between Bicep and Terraform in ../common/ directory

resource "azurerm_resource_group_template_deployment" "custom_tables" {
  name                = "fabric-governance-tables-deployment"
  resource_group_name = azurerm_resource_group.governance.name
  deployment_mode     = "Incremental"

  template_content = file("${path.module}/../common/tables-template.json")
  
  parameters_content = jsonencode({
    workspaceName = {
      value = azurerm_log_analytics_workspace.governance.name
    }
    retentionInDays = {
      value = var.retention_in_days
    }
  })

  depends_on = [
    azurerm_log_analytics_workspace.governance
  ]
}

# ============================================================================
# Data Collection Endpoint (DCE)
# ============================================================================

resource "azurerm_monitor_data_collection_endpoint" "governance" {
  name                = local.dce_name
  location            = azurerm_resource_group.governance.location
  resource_group_name = azurerm_resource_group.governance.name

  public_network_access_enabled = true

  tags = local.common_tags
}

# ============================================================================
# Data Collection Rule (DCR) for Tenant Settings
# ============================================================================
# Note: DCR is deployed using ARM template due to complex stream declarations
# and transformation rules that aren't fully supported in Terraform provider
# Template is shared between Bicep and Terraform in ../common/ directory

resource "azurerm_resource_group_template_deployment" "dcr" {
  name                = "fabric-governance-dcr-deployment"
  resource_group_name = azurerm_resource_group.governance.name
  deployment_mode     = "Incremental"

  template_content = file("${path.module}/../common/dcr-template.json")
  
  parameters_content = jsonencode({
    dcrName = {
      value = local.dcr_name
    }
    location = {
      value = azurerm_resource_group.governance.location
    }
    dceResourceId = {
      value = azurerm_monitor_data_collection_endpoint.governance.id
    }
    lawResourceId = {
      value = azurerm_log_analytics_workspace.governance.id
    }
  })

  depends_on = [
    azurerm_monitor_data_collection_endpoint.governance,
    azurerm_resource_group_template_deployment.custom_tables
  ]
}

# ============================================================================
# Action Group for Alerts
# ============================================================================

resource "azurerm_monitor_action_group" "governance" {
  count               = var.enable_alerts && length(local.email_addresses) > 0 ? 1 : 0
  name                = local.action_group_name
  resource_group_name = azurerm_resource_group.governance.name
  short_name          = "FabricGov"

  dynamic "email_receiver" {
    for_each = local.email_addresses
    content {
      name                    = "Email-${replace(trimspace(email_receiver.value), "@", "-at-")}"
      email_address           = trimspace(email_receiver.value)
      use_common_alert_schema = true
    }
  }

  tags = local.common_tags
}

# ============================================================================
# Alert Rule: New Preview Features Detected
# ============================================================================

resource "azurerm_monitor_scheduled_query_rules_alert_v2" "new_preview_features" {
  count               = var.enable_alerts && length(local.email_addresses) > 0 ? 1 : 0
  name                = "${local.alert_rule_prefix}-new-preview-features"
  location            = azurerm_resource_group.governance.location
  resource_group_name = azurerm_resource_group.governance.name

  display_name = "Fabric: New Preview Features Detected"
  description  = "Alert when new preview features are detected in tenant settings"
  severity     = 2
  enabled      = true

  evaluation_frequency = "PT1H"
  window_duration      = "PT1H"
  scopes               = [azurerm_log_analytics_workspace.governance.id]

  criteria {
    query = <<-QUERY
      FabricTenantSettings_CL
      | where TimeGenerated > ago(1h)
      | where IsPreviewFeature_b == true
      | summarize NewPreviews = dcount(SettingName_s) by TenantId_s
      | where NewPreviews > 0
    QUERY

    time_aggregation_method = "Count"
    operator                = "GreaterThan"
    threshold               = 0

    failing_periods {
      minimum_failing_periods_to_trigger_alert = 1
      number_of_evaluation_periods             = 1
    }
  }

  action {
    action_groups = [azurerm_monitor_action_group.governance[0].id]
  }

  auto_mitigation_enabled = true

  tags = local.common_tags
}

# ============================================================================
# Alert Rule: Preview Features Enabled in Production
# ============================================================================

resource "azurerm_monitor_scheduled_query_rules_alert_v2" "preview_enabled_prod" {
  count               = var.enable_alerts && length(local.email_addresses) > 0 ? 1 : 0
  name                = "${local.alert_rule_prefix}-preview-enabled-prod"
  location            = azurerm_resource_group.governance.location
  resource_group_name = azurerm_resource_group.governance.name

  display_name = "Fabric: Preview Features Enabled in Production"
  description  = "Alert when preview features are enabled (should be disabled in PROD)"
  severity     = 1
  enabled      = true

  evaluation_frequency = "PT30M"
  window_duration      = "PT30M"
  scopes               = [azurerm_log_analytics_workspace.governance.id]

  criteria {
    query = <<-QUERY
      FabricTenantSettings_CL
      | where TimeGenerated > ago(30m)
      | where IsPreviewFeature_b == true and Enabled_b == true
      | summarize EnabledPreviews = dcount(SettingName_s) by TenantId_s
    QUERY

    time_aggregation_method = "Count"
    operator                = "GreaterThan"
    threshold               = 0

    failing_periods {
      minimum_failing_periods_to_trigger_alert = 1
      number_of_evaluation_periods             = 1
    }
  }

  action {
    action_groups = [azurerm_monitor_action_group.governance[0].id]
  }

  auto_mitigation_enabled = true

  tags = local.common_tags
}

# ============================================================================
# Outputs
# ============================================================================

output "workspace_id" {
  description = "Resource ID of the Log Analytics workspace"
  value       = azurerm_log_analytics_workspace.governance.id
}

output "workspace_name" {
  description = "Name of the Log Analytics workspace"
  value       = azurerm_log_analytics_workspace.governance.name
}

output "workspace_customer_id" {
  description = "Customer ID (workspace ID) for Log Analytics"
  value       = azurerm_log_analytics_workspace.governance.workspace_id
  sensitive   = true
}

output "dce_endpoint" {
  description = "Data Collection Endpoint logs ingestion URI"
  value       = azurerm_monitor_data_collection_endpoint.governance.logs_ingestion_endpoint
}

output "dce_id" {
  description = "Resource ID of the Data Collection Endpoint"
  value       = azurerm_monitor_data_collection_endpoint.governance.id
}

output "dcr_immutable_id" {
  description = "Immutable ID of the Data Collection Rule (use this in API calls)"
  value       = jsondecode(azurerm_resource_group_template_deployment.dcr.output_content).dcrImmutableId.value
}

output "dcr_id" {
  description = "Resource ID of the Data Collection Rule"
  value       = jsondecode(azurerm_resource_group_template_deployment.dcr.output_content).dcrId.value
}

output "action_group_id" {
  description = "Resource ID of the Action Group"
  value       = var.enable_alerts && length(local.email_addresses) > 0 ? azurerm_monitor_action_group.governance[0].id : null
}

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.governance.name
}

output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    resource_group     = azurerm_resource_group.governance.name
    location           = azurerm_resource_group.governance.location
    workspace          = azurerm_log_analytics_workspace.governance.name
    dce_endpoint       = azurerm_monitor_data_collection_endpoint.governance.logs_ingestion_endpoint
    alerts_enabled     = var.enable_alerts && length(local.email_addresses) > 0
    environment        = var.environment_tag
  }
}
