"""
API authentication and Fabric REST API calls for FabricLA-Connector.
"""
import msal
import requests
import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential, ClientSecretCredential
from typing import Optional, Tuple

def acquire_token(tenant: str, client_id: str, client_secret: str, scope: str) -> str:
    """Acquire OAuth token for API access using client credentials"""
    authority = f"https://login.microsoftonline.com/{tenant}"
    app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
    result = app.acquire_token_for_client(scopes=[scope])
    if not result or "access_token" not in result:
        print(f"❌ Token acquisition failed for {scope}")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        print(f"   Description: {result.get('error_description', 'No description')}")
        raise RuntimeError(f"Failed to acquire token: {result}")
    
    token = result["access_token"]
    print(f"✅ Token acquired for {scope}: {token[:10]}...{token[-10:]}")
    return token

def acquire_token_managed_identity(scope: str) -> str:
    """Get token using managed identity (for Azure resources)"""
    try:
        credential = ManagedIdentityCredential()
        token = credential.get_token(scope)
        print(f"✅ Managed identity token acquired for {scope}: {token.token[:10]}...{token.token[-10:]}")
        return token.token
    except Exception as e:
        raise RuntimeError(f"Failed to get managed identity token for {scope}: {e}")

def get_fabric_token(scope: str = "https://api.fabric.microsoft.com/.default") -> str:
    """
    Get authentication token with Fabric-aware logic:
    1. Try Fabric workspace identity (if available)
    2. Fall back to service principal authentication
    3. Support both local and Fabric environments
    """
    
    # First, try Fabric's built-in authentication if available
    try:
        import notebookutils
        print(f"[Auth] Attempting Fabric workspace identity for {scope}")
        
        # Use Fabric's credential system if available
        token = notebookutils.credentials.getSecret("System", "AccessToken")
        if token:
            print(f"[Auth] ✅ Successfully acquired token via Fabric workspace identity")
            return token
        else:
            print(f"[Auth] ⚠️  Fabric workspace token not available, falling back to service principal")
            
    except (ImportError, AttributeError, Exception) as e:
        print(f"[Auth] Fabric authentication not available: {str(e)[:100]}")
        print(f"[Auth] Using service principal authentication")
    
    # Fall back to standard service principal authentication
    tenant_id, client_id, client_secret, _ = get_credentials_fabric_aware()
    if not all([tenant_id, client_id, client_secret]):
        raise RuntimeError("No valid credentials found for token acquisition")
    
    return acquire_token(tenant_id, client_id, client_secret, scope)

def get_credentials_fabric_aware() -> Tuple[Optional[str], Optional[str], Optional[str], bool]:
    """
    Get authentication credentials with Fabric runtime awareness
    Returns tuple: (tenant_id, client_id, client_secret, use_fabric_auth)
    """
    
    # Check if running in Fabric
    try:
        import notebookutils
        running_in_fabric = True
        
        # Try to get credentials from Fabric Key Vault integration
        try:
            fabric_tenant = notebookutils.credentials.getSecret("Fabric", "TenantId")
            fabric_client_id = notebookutils.credentials.getSecret("Fabric", "ClientId") 
            fabric_secret = notebookutils.credentials.getSecret("Fabric", "ClientSecret")
            
            if fabric_tenant and fabric_client_id:
                print("[Auth] ✅ Using credentials from Fabric Key Vault integration")
                return fabric_tenant, fabric_client_id, fabric_secret, True
                
        except Exception as e:
            print(f"[Auth] Fabric Key Vault not configured: {str(e)[:100]}")
            
    except ImportError:
        running_in_fabric = False
    
    # Use environment variables
    final_tenant = os.getenv("FABRIC_TENANT_ID")
    final_client_id = os.getenv("FABRIC_APP_ID") 
    final_secret = os.getenv("FABRIC_APP_SECRET")
    
    if not all([final_tenant, final_client_id, final_secret]):
        missing = []
        if not final_tenant: missing.append("tenant_id/FABRIC_TENANT_ID")
        if not final_client_id: missing.append("client_id/FABRIC_APP_ID")
        if not final_secret: missing.append("client_secret/FABRIC_APP_SECRET")
        
        print(f"[Auth] ❌ Missing credentials: {', '.join(missing)}")
        if running_in_fabric:
            print("[Auth] 💡 In Fabric, you can:")
            print("       1. Set up Key Vault integration with secrets named 'TenantId', 'ClientId', 'ClientSecret'")
            print("       2. Set values directly in environment variables")
            print("       3. Use workspace managed identity (if configured)")
        else:
            print("[Auth] 💡 Set missing values in your .env file")
            
        return None, None, None, False
    
    auth_source = "Fabric Key Vault" if running_in_fabric else "Environment Variables"
    print(f"[Auth] ✅ Using credentials from {auth_source}")
    return final_tenant, final_client_id, final_secret, running_in_fabric

def get_secret_from_key_vault(vault_uri: str, secret_name: str) -> str:
    """Get secret from Azure Key Vault using managed identity"""
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_uri, credential=credential)
    secret = client.get_secret(secret_name).value
    if secret is None:
        raise RuntimeError(f"Secret '{secret_name}' not found or has no value in Key Vault '{vault_uri}'.")
    return secret

FABRIC_API = "https://api.fabric.microsoft.com/v1"

def get_capacities(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{FABRIC_API}/capacities", headers=headers, timeout=60)
    response.raise_for_status()
    return response.json().get("value", [])

def get_workspaces(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{FABRIC_API}/workspaces", headers=headers, timeout=60)
    response.raise_for_status()
    return response.json().get("value", [])

def get_workspace_items(workspace_id: str, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{FABRIC_API}/workspaces/{workspace_id}/items", headers=headers, timeout=60)
    if response.status_code == 200:
        return response.json().get("value", [])
    return []

# === Dataset API helpers ===
def list_workspace_datasets(workspace_id: str, token: str):
    url = f"{FABRIC_API}/workspaces/{workspace_id}/datasets"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=60)
    if r.status_code == 200:
        return r.json().get("value", [])
    return []

def get_dataset_metadata(dataset_id: str, token: str):
    url = f"{FABRIC_API}/datasets/{dataset_id}"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=60)
    if r.status_code == 200:
        return r.json()
    return {}

def get_dataset_refresh_history(dataset_id: str, token: str, top: int = 200):
    url = f"{FABRIC_API}/datasets/{dataset_id}/refreshes?$top={top}"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=60)
    if r.status_code == 200:
        return r.json().get("value", [])
    return []

# === Utility functions ===
import datetime as dt
def parse_iso(s: str):
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    parsed = dt.datetime.fromisoformat(s)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed

def within_lookback(start_iso: str, end_iso: str, lookback_minutes: int) -> bool:
    edge = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc) - dt.timedelta(minutes=int(lookback_minutes))
    t = parse_iso(end_iso) or parse_iso(start_iso)
    return (t is not None) and (t >= edge)

# === Pipeline API helpers ===
def list_item_job_instances(workspace_id: str, item_id: str, token: str):
    url = f"{FABRIC_API}/workspaces/{workspace_id}/items/{item_id}/jobs/instances"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=60)
    if r.status_code == 200:
        data = r.json()
        return data.get("value", [])
    return []

def query_pipeline_activity_runs(workspace_id: str, job_instance_id: str, token: str, last_after_iso: str, last_before_iso: str):
    url = f"{FABRIC_API}/workspaces/{workspace_id}/datapipelines/pipelineruns/{job_instance_id}/queryactivityruns"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {
        "filters": [],
        "orderBy": [{"orderBy": "ActivityRunStart", "order": "DESC"}],
        "lastUpdatedAfter": last_after_iso,
        "lastUpdatedBefore": last_before_iso,
    }
    r = requests.post(url, headers=headers, json=body, timeout=60)
    if r.status_code == 200:
        data = r.json()
        return data.get("value") or data.get("activityRuns") or data.get("items") or []
    return []

# === Mappers (stubs, to be implemented in collectors.py) ===
def map_dataset_refresh(workspace_id, dataset_id, dataset_name, refresh):
    # Should be implemented in collectors.py
    pass

def map_dataset_metadata(workspace_id, dataset):
    # Should be implemented in collectors.py
    pass

def map_pipeline_run(workspace_id, item_id, run):
    # Should be implemented in collectors.py
    pass

def map_activity_run(workspace_id, pipeline_id, pipeline_run_id, act):
    # Should be implemented in collectors.py
    pass