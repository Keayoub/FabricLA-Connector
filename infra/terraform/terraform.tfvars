# Fabric Monitoring - Terraform Variables
# Customize these values for your environment

# Required: Your service principal object ID
# Get it with: az ad sp show --id "your-client-id" --query "id" -o tsv
service_principal_object_id = "1f7e1986-d488-434c-8e4c-b8aa90a71977"

# Optional: Customize resource names and location
location                      = "Canada Central"
resource_group_name           = "rg-fabric-monitoring"
log_analytics_workspace_name  = "law-fabric-monitoring"
data_collection_endpoint_name = "dce-fabric-monitoring"
data_collection_rule_name     = "dcr-fabric-monitoring"
deploy_main_dcr               = false
deploy_spark_monitoring       = true
deploy_pipeline_monitoring    = false
deploy_capacity_monitoring    = false
deploy_admin_monitoring       = false