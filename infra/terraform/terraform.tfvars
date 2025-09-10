# Fabric Monitoring - Terraform Variables
# Customize these values for your environment

# Required: Your service principal object ID
# Get it with: az ad sp show --id "your-client-id" --query "id" -o tsv
service_principal_object_id = "REDACTED-SP-OBJECT-ID"

# Optional: Customize resource names and location
location                      = "Canada Central"
resource_group_name           = "rg-fabric-monitoring"
log_analytics_workspace_name  = "law-fabric-monitoring"
data_collection_endpoint_name = "dce-fabric-monitoring"
data_collection_rule_name     = "dcr-fabric-monitoring"
