"""
Authentication functions for Microsoft Fabric APIs.

Provides Fabric-aware authentication with automatic fallback:
1. Fabric workspace identity (if running in Fabric)
2. Service principal (client credentials)
3. Environment variables or Key Vault
"""
import msal
import os
from azure.identity import ManagedIdentityCredential
from typing import Optional, Tuple


def acquire_token(tenant: str, client_id: str, client_secret: str, scope: str) -> str:
    """Acquire OAuth token for API access using client credentials"""
    authority = f"https://login.microsoftonline.com/{tenant}"
    app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
    result = app.acquire_token_for_client(scopes=[scope])
    if not result or "access_token" not in result:
        print(f"ERROR: Token acquisition failed for {scope}")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        print(f"   Description: {result.get('error_description', 'No description')}")
        raise RuntimeError(f"Failed to acquire token: {result}")
    
    token = result["access_token"]
    print(f"SUCCESS: Token acquired for {scope}: {token[:10]}...{token[-10:]}")
    return token


def acquire_token_managed_identity(scope: str) -> str:
    """Get token using managed identity (for Azure resources)"""
    try:
        credential = ManagedIdentityCredential()
        token = credential.get_token(scope)
        print(f"SUCCESS: Managed identity token acquired for {scope}: {token.token[:10]}...{token.token[-10:]}")
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
            print(f"[Auth] SUCCESS: Successfully acquired token via Fabric workspace identity")
            return token
        else:
            print(f"[Auth] WARNING:  Fabric workspace token not available, falling back to service principal")
            
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
                print("[Auth] SUCCESS: Using credentials from Fabric Key Vault integration")
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
        
        print(f"[Auth] ERROR: Missing credentials: {', '.join(missing)}")
        if running_in_fabric:
            print("[Auth] TIP: In Fabric, you can:")
            print("       1. Set up Key Vault integration with secrets named 'TenantId', 'ClientId', 'ClientSecret'")
            print("       2. Set values directly in environment variables")
            print("       3. Use workspace managed identity (if configured)")
        else:
            print("[Auth] TIP: Set missing values in your .env file")
            
        return None, None, None, False
    
    auth_source = "Fabric Key Vault" if running_in_fabric else "Environment Variables"
    print(f"[Auth] SUCCESS: Using credentials from {auth_source}")
    return final_tenant, final_client_id, final_secret, running_in_fabric
