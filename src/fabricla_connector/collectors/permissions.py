"""
Access Permissions collector for workspace configuration monitoring.
"""
import requests
from typing import Iterator, Dict, Any
from fabricla_connector.api import get_fabric_token


class AccessPermissionsCollector:
    """
    Collector for workspace access permissions and configuration.
    
    This collector retrieves workspace configuration including:
    - Workspace settings (OneLake Access Point, Git integration, etc.)
    - Capacity assignment
    - Security settings
    - Compliance and data classification
    """
    
    def __init__(self, workspace_id: str):
        """
        Initialize Access Permissions collector.
        
        Args:
            workspace_id: Fabric workspace ID
        """
        self.workspace_id = workspace_id
    
    def collect_workspace_config(self) -> Iterator[Dict[str, Any]]:
        """
        Collect workspace configuration data.
        
        Yields:
            Workspace configuration records
        """
        token = get_fabric_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try admin endpoint first
        url = f"https://api.fabric.microsoft.com/v1/admin/workspaces/{self.workspace_id}"
        response = requests.get(url, headers=headers)
        
        is_fallback = False
        if response.status_code == 403:
            # Fallback to regular workspace endpoint for non-admin users
            print(f"[Permissions] Admin endpoint returned 403, trying fallback endpoint")
            url = f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}"
            response = requests.get(url, headers=headers)
            is_fallback = True
        
        if response.status_code != 200:
            print(f"[Permissions] Failed to get workspace config: {response.status_code}")
            return
        
        data = response.json()
        
        # Map API response to schema
        config = {
            "WorkspaceId": self.workspace_id,
            "WorkspaceName": data.get("displayName", ""),
            "WorkspaceType": data.get("type", ""),
            "State": data.get("state", ""),
            "CapacityId": data.get("capacityId", ""),
            "OneLakeAccessEnabled": data.get("oneLakeAccessEnabled", False),
            "OneLakeAccessPointEnabled": data.get("settings", {}).get("oneLakeAccessPointEnabled", False),
            "PublicInternetAccess": data.get("settings", {}).get("publicInternetAccess", ""),
            "ReadOnlyState": data.get("settings", {}).get("readOnlyState", False),
            "ManagedVirtualNetwork": data.get("settings", {}).get("managedVirtualNetwork", ""),
            "GitEnabled": data.get("settings", {}).get("gitEnabled", False),
            "GitConnectionId": data.get("gitConnection", {}).get("gitConnectionId", ""),
            "GitRepositoryUrl": data.get("gitConnection", {}).get("repositoryUrl", ""),
            "DataClassification": data.get("dataClassification", ""),
            "SensitivityLabel": data.get("sensitivityLabel", {}).get("labelId", ""),
            "IsCompliant": data.get("complianceFlags", {}).get("isCompliant", False),
            "IsOnDedicatedCapacity": data.get("isOnDedicatedCapacity", False),
            "CreatedDate": data.get("createdDate", ""),
            "ModifiedDate": data.get("modifiedDate", ""),
            "Description": data.get("description", ""),
            "MetricType": "WorkspaceConfig"  # Fixed metric type for workspace configuration
        }
        
        # Add note if using fallback endpoint
        if is_fallback:
            config["Note"] = "Limited data - requires admin permissions for full workspace config"
        
        yield config
