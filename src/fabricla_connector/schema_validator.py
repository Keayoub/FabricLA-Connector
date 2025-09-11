from typing import Dict, Any, List

def validate_notebook_execution_schema(record: Dict[str, Any]) -> None:
    required = ["TimeGenerated", "WorkspaceId", "NotebookId", "NotebookName", "ExecutionCount", "LastRunTime", "Status"]
    for key in required:
        if key not in record:
            raise ValueError(f"Missing key in Notebook Execution schema: {key}")

def validate_semantic_model_schema(record: Dict[str, Any]) -> None:
    required = ["TimeGenerated", "WorkspaceId", "SemanticModelId", "SemanticModelName", "RefreshCount", "LastRefreshTime", "Status"]
    for key in required:
        if key not in record:
            raise ValueError(f"Missing key in Semantic Model schema: {key}")

def validate_workspace_permissions_schema(record: Dict[str, Any]) -> None:
    required = ["TimeGenerated", "WorkspaceId", "UserId", "UserName", "Role", "AssignmentTime"]
    for key in required:
        if key not in record:
            raise ValueError(f"Missing key in Workspace Permissions schema: {key}")

def validate_datamart_schema(record: Dict[str, Any]) -> None:
    required = ["TimeGenerated", "WorkspaceId", "DatamartId", "DatamartName", "TableCount", "RowCount", "LastRefreshTime"]
    for key in required:
        if key not in record:
            raise ValueError(f"Missing key in Datamart schema: {key}")

def validate_deployment_pipeline_schema(record: Dict[str, Any]) -> None:
    required = ["TimeGenerated", "PipelineId", "PipelineName", "OperationCount", "LastRunTime", "Status"]
    for key in required:
        if key not in record:
            raise ValueError(f"Missing key in Deployment Pipeline schema: {key}")

def validate_app_analytics_schema(record: Dict[str, Any]) -> None:
    required = ["TimeGenerated", "WorkspaceId", "AppId", "AppName", "UserCount", "LastAccessed"]
    for key in required:
        if key not in record:
            raise ValueError(f"Missing key in App Analytics schema: {key}")

def validate_import_monitoring_schema(record: Dict[str, Any]) -> None:
    required = ["TimeGenerated", "WorkspaceId", "ImportId", "ImportName", "RowCount", "Status", "LastImportTime"]
    for key in required:
        if key not in record:
            raise ValueError(f"Missing key in Import Monitoring schema: {key}")
"""
Validates payloads against DCR mapping schema.
"""
def validate_payload(records: List[Dict[str, Any]]) -> None:
    if not isinstance(records, list):
        raise ValueError('Payload must be a list of records')
    # Add more validation logic here

def validate_eventhouse_schema(record: Dict[str, Any]) -> None:
    required = ["TimeGenerated", "WorkspaceId", "DatabaseId", "DatabaseName", "TableCount", "DataSizeMB", "QueryCount", "IngestionStatus"]
    for key in required:
        if key not in record:
            raise ValueError(f"Missing key in EventHouse schema: {key}")

def validate_lakehouse_schema(record: Dict[str, Any]) -> None:
    required = ["TimeGenerated", "WorkspaceId", "LakehouseId", "LakehouseName", "TableCount", "FilesCount", "StorageSizeGB", "LastRefreshTime"]
    for key in required:
        if key not in record:
            raise ValueError(f"Missing key in Lakehouse schema: {key}")

def validate_gateway_schema(record: Dict[str, Any]) -> None:
    required = ["TimeGenerated", "GatewayId", "GatewayName", "Status", "Version", "DataSourceCount", "LastHeartbeat", "LoadPercentage"]
    for key in required:
        if key not in record:
            raise ValueError(f"Missing key in Gateway schema: {key}")

def validate_report_analytics_schema(record: Dict[str, Any]) -> None:
    required = ["TimeGenerated", "ReportId", "ReportName", "WorkspaceId", "ViewCount", "UniqueUsers", "AvgLoadTimeMs", "LastAccessed"]
    for key in required:
        if key not in record:
            raise ValueError(f"Missing key in Report Analytics schema: {key}")
