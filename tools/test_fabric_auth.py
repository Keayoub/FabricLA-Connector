#!/usr/bin/env python3
"""
Test script for Fabric Environment API authentication methods.

This script tests the various authentication methods supported by the upload_wheel_to_fabric.py script
without actually uploading files. It validates token acquisition and basic API connectivity.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the tools directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from upload_wheel_to_fabric import FabricEnvironmentUploader
except ImportError:
    print("❌ Error: Could not import FabricEnvironmentUploader from upload_wheel_to_fabric.py")
    print("   Make sure you're running this script from the tools directory or the project root.")
    sys.exit(1)


def test_bearer_token_auth(workspace_id: str, environment_id: str, token: str) -> bool:
    """Test bearer token authentication."""
    print("🔑 Testing Bearer Token Authentication...")
    
    try:
        uploader = FabricEnvironmentUploader(
            workspace_id=workspace_id,
            environment_id=environment_id,
            token=token
        )
        
        # Try to get basic environment info (without uploading)
        url = f"{uploader.base_url}/workspaces/{workspace_id}/environments/{environment_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        import requests
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("✅ Bearer token authentication successful")
            return True
        elif response.status_code == 401:
            print("❌ Bearer token authentication failed: Unauthorized (401)")
            print(f"   Response: {response.text[:200]}")
            return False
        elif response.status_code == 403:
            print("❌ Bearer token authentication failed: Forbidden (403)")
            print(f"   Response: {response.text[:200]}")
            return False
        else:
            print(f"⚠️  Bearer token test returned unexpected status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Bearer token authentication failed with exception: {e}")
        return False


def test_service_principal_auth(workspace_id: str, environment_id: str, 
                               client_id: str, client_secret: str, tenant_id: str) -> bool:
    """Test service principal authentication."""
    print("🔑 Testing Service Principal Authentication...")
    
    try:
        uploader = FabricEnvironmentUploader(
            workspace_id=workspace_id,
            environment_id=environment_id,
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id
        )
        
        # Try to get a token
        token = uploader._get_token_with_client_credentials(client_id, client_secret, tenant_id)
        
        if token:
            print("✅ Service principal token acquisition successful")
            
            # Test basic API call
            url = f"{uploader.base_url}/workspaces/{workspace_id}/environments/{environment_id}"
            headers = {"Authorization": f"Bearer {token}"}
            
            import requests
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print("✅ Service principal API call successful")
                return True
            else:
                print(f"⚠️  Service principal API call returned status: {response.status_code}")
                return False
        else:
            print("❌ Service principal token acquisition failed")
            return False
            
    except Exception as e:
        print(f"❌ Service principal authentication failed with exception: {e}")
        return False


def test_default_credential_auth(workspace_id: str, environment_id: str) -> bool:
    """Test DefaultAzureCredential authentication."""
    print("🔑 Testing DefaultAzureCredential Authentication...")
    
    try:
        uploader = FabricEnvironmentUploader(
            workspace_id=workspace_id,
            environment_id=environment_id
        )
        
        # Try to get a token using DefaultAzureCredential
        token = uploader._get_token_with_default_credential()
        
        if token:
            print("✅ DefaultAzureCredential token acquisition successful")
            
            # Test basic API call
            url = f"{uploader.base_url}/workspaces/{workspace_id}/environments/{environment_id}"
            headers = {"Authorization": f"Bearer {token}"}
            
            import requests
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print("✅ DefaultAzureCredential API call successful")
                return True
            else:
                print(f"⚠️  DefaultAzureCredential API call returned status: {response.status_code}")
                return False
        else:
            print("❌ DefaultAzureCredential token acquisition failed")
            return False
            
    except Exception as e:
        print(f"❌ DefaultAzureCredential authentication failed with exception: {e}")
        print("   This might be expected if you're not in an environment with Azure credentials")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Fabric Environment API authentication methods")
    parser.add_argument("--workspace-id", required=True, help="Fabric workspace ID")
    parser.add_argument("--environment-id", required=True, help="Fabric environment ID")
    
    # Authentication options
    parser.add_argument("--token", help="Bearer token for simple authentication")
    parser.add_argument("--client-id", help="Azure AD client ID for service principal auth")
    parser.add_argument("--client-secret", help="Azure AD client secret for service principal auth")
    parser.add_argument("--tenant-id", help="Azure AD tenant ID for service principal auth")
    
    args = parser.parse_args()
    
    print("🧪 Fabric Environment API Authentication Test")
    print("=" * 50)
    print(f"Workspace ID: {args.workspace_id}")
    print(f"Environment ID: {args.environment_id}")
    print()
    
    success_count = 0
    test_count = 0
    
    # Test bearer token authentication if provided
    if args.token:
        test_count += 1
        if test_bearer_token_auth(args.workspace_id, args.environment_id, args.token):
            success_count += 1
        print()
    
    # Test service principal authentication if provided
    if args.client_id and args.client_secret and args.tenant_id:
        test_count += 1
        if test_service_principal_auth(
            args.workspace_id, args.environment_id,
            args.client_id, args.client_secret, args.tenant_id
        ):
            success_count += 1
        print()
    
    # Always test DefaultAzureCredential
    test_count += 1
    if test_default_credential_auth(args.workspace_id, args.environment_id):
        success_count += 1
    print()
    
    # Summary
    print("📊 Test Summary")
    print("=" * 20)
    print(f"Tests run: {test_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {test_count - success_count}")
    
    if success_count == test_count:
        print("🎉 All authentication methods are working!")
        sys.exit(0)
    elif success_count > 0:
        print("⚠️  Some authentication methods are working")
        sys.exit(0)
    else:
        print("❌ No authentication methods are working")
        sys.exit(1)


if __name__ == "__main__":
    main()