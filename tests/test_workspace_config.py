"""
Tests for workspace configuration collection
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fabricla_connector.collectors import AccessPermissionsCollector
from fabricla_connector import workflows


@pytest.fixture
def mock_workspace_config_response():
    """Mock successful workspace config API response"""
    return {
        "displayName": "Test Workspace",
        "type": "Workspace",
        "state": "Active",
        "capacityId": "test-capacity-id",
        "oneLakeAccessEnabled": True,
        "settings": {
            "oneLakeAccessPointEnabled": True,
            "readOnlyState": False,
            "dataAccessRoles": ["Reader", "Contributor"],
            "publicInternetAccess": "Enabled",
            "managedVirtualNetwork": "Disabled",
            "gitEnabled": True,
            "defaultDataLakeStorageGen2": "enabled"
        },
        "gitConnection": {
            "gitConnectionId": "git-conn-123",
            "repositoryUrl": "https://github.com/test/repo"
        },
        "dataClassification": "Confidential",
        "sensitivityLabel": {
            "labelId": "label-123"
        },
        "complianceFlags": {
            "isCompliant": True
        },
        "isOnDedicatedCapacity": True,
        "createdDate": "2025-01-01T00:00:00Z",
        "modifiedDate": "2025-10-07T00:00:00Z",
        "description": "Test workspace for monitoring"
    }


@pytest.fixture
def mock_workspace_config_minimal():
    """Mock minimal workspace config (non-admin fallback)"""
    return {
        "displayName": "Test Workspace",
        "type": "Workspace",
        "capacityId": "test-capacity-id",
        "description": "Test workspace"
    }


def test_collect_workspace_config_success(mock_workspace_config_response):
    """Test successful workspace configuration collection"""
    with patch('fabricla_connector.api.get_fabric_token') as mock_token, \
         patch('fabricla_connector.collectors.permissions.requests.get') as mock_get:
        
        mock_token.return_value = "test-token"
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_workspace_config_response
        mock_get.return_value = mock_response
        
        # Create collector and collect data
        collector = AccessPermissionsCollector("test-workspace-id")
        configs = list(collector.collect_workspace_config())
        
        # Assertions
        assert len(configs) == 1
        config = configs[0]
        
        # Verify workspace details
        assert config["WorkspaceId"] == "test-workspace-id"
        assert config["WorkspaceName"] == "Test Workspace"
        assert config["WorkspaceType"] == "Workspace"
        assert config["State"] == "Active"
        assert config["CapacityId"] == "test-capacity-id"
        
        # Verify OAP settings
        assert config["OneLakeAccessEnabled"] is True
        assert config["OneLakeAccessPointEnabled"] is True
        
        # Verify security settings
        assert config["PublicInternetAccess"] == "Enabled"
        assert config["ReadOnlyState"] is False
        assert config["ManagedVirtualNetwork"] == "Disabled"
        
        # Verify Git integration
        assert config["GitEnabled"] is True
        assert config["GitConnectionId"] == "git-conn-123"
        assert config["GitRepositoryUrl"] == "https://github.com/test/repo"
        
        # Verify compliance
        assert config["DataClassification"] == "Confidential"
        assert config["SensitivityLabel"] == "label-123"
        
        # Verify metadata
        assert config["IsOnDedicatedCapacity"] is True
        assert config["MetricType"] == "WorkspaceConfig"


def test_collect_workspace_config_fallback(mock_workspace_config_minimal):
    """Test workspace config collection with non-admin fallback"""
    with patch('fabricla_connector.api.get_fabric_token') as mock_token, \
         patch('fabricla_connector.collectors.permissions.requests.get') as mock_get:
        
        mock_token.return_value = "test-token"
        
        # Mock 403 response on admin endpoint, success on fallback
        responses = [
            Mock(status_code=403),  # Admin endpoint
            Mock(status_code=200, json=lambda: mock_workspace_config_minimal)  # Fallback
        ]
        mock_get.side_effect = responses
        
        # Create collector and collect data
        collector = AccessPermissionsCollector("test-workspace-id")
        configs = list(collector.collect_workspace_config())
        
        # Assertions
        assert len(configs) == 1
        config = configs[0]
        
        # Verify limited data
        assert config["WorkspaceId"] == "test-workspace-id"
        assert config["WorkspaceName"] == "Test Workspace"
        assert config["WorkspaceType"] == "Workspace"
        assert config["CapacityId"] == "test-capacity-id"
        assert config["MetricType"] == "WorkspaceConfig"
        assert "Note" in config
        assert "admin permissions" in config["Note"]


def test_collect_workspace_config_error_handling():
    """Test error handling in workspace config collection"""
    with patch('fabricla_connector.api.get_fabric_token') as mock_token, \
         patch('fabricla_connector.collectors.permissions.requests.get') as mock_get:
        
        mock_token.return_value = "test-token"
        
        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        # Create collector and collect data
        collector = AccessPermissionsCollector("test-workspace-id")
        configs = list(collector.collect_workspace_config())
        
        # Should handle error gracefully
        assert len(configs) == 0


def test_collect_and_ingest_workspace_config_workflow():
    """Test complete workflow for workspace config collection and ingestion"""
    with patch('fabricla_connector.collectors.AccessPermissionsCollector') as mock_collector_class, \
         patch('fabricla_connector.ingestion.post_rows_to_dcr') as mock_ingest, \
         patch('fabricla_connector.config.get_ingestion_config') as mock_config:
        
        # Mock collector
        mock_collector = Mock()
        mock_collector.collect_workspace_config.return_value = [
            {
                "WorkspaceId": "test-ws",
                "WorkspaceName": "Test",
                "OneLakeAccessEnabled": True,
                "OneLakeAccessPointEnabled": True,
                "MetricType": "WorkspaceConfig"
            }
        ]
        mock_collector_class.return_value = mock_collector
        
        # Mock ingestion config
        mock_config.return_value = {
            "dce_endpoint": "https://test-dce.monitor.azure.com",
            "dcr_immutable_id": "dcr-test-123",
            "stream_name": "Custom-FabricWorkspaceConfig_CL"
        }
        
        # Mock ingestion result
        mock_ingest.return_value = {"uploaded_row_count": 1}
        
        # Run workflow
        results = workflows.collect_and_ingest_workspace_config(
            workspace_id="test-ws",
            stream_name="Custom-FabricWorkspaceConfig_CL"
        )
        
        # Assertions
        assert results["workspace_config"]["collected"] == 1
        assert results["workspace_config"]["ingested"] == 1
        assert len(results["errors"]) == 0
        
        # Verify ingestion was called with correct parameters
        mock_ingest.assert_called_once()
        call_args = mock_ingest.call_args[1]
        assert call_args["stream_name"] == "Custom-FabricWorkspaceConfig_CL"
        assert len(call_args["records"]) == 1


def test_workspace_config_oap_disabled():
    """Test workspace config when OAP is disabled"""
    with patch('fabricla_connector.api.get_fabric_token') as mock_token, \
         patch('fabricla_connector.collectors.permissions.requests.get') as mock_get:
        
        mock_token.return_value = "test-token"
        
        # Mock workspace without OAP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "displayName": "Non-OAP Workspace",
            "type": "Workspace",
            "state": "Active",
            "capacityId": "capacity-123",
            "oneLakeAccessEnabled": False,
            "settings": {
                "oneLakeAccessPointEnabled": False,
                "publicInternetAccess": "Disabled"
            },
            "isOnDedicatedCapacity": False
        }
        mock_get.return_value = mock_response
        
        # Create collector and collect data
        collector = AccessPermissionsCollector("test-workspace-id")
        configs = list(collector.collect_workspace_config())
        
        # Assertions
        assert len(configs) == 1
        config = configs[0]
        
        # Verify OAP is disabled
        assert config["OneLakeAccessEnabled"] is False
        assert config["OneLakeAccessPointEnabled"] is False
        assert config["PublicInternetAccess"] == "Disabled"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
