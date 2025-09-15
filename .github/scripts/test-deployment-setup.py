#!/usr/bin/env python3
"""
Test script to validate GitHub Actions deployment setup.

This script helps verify that all required secrets and configurations
are properly set up before running the automated deployment workflow.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Optional

def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_success(text: str) -> None:
    """Print success message."""
    print(f"✅ {text}")

def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"⚠️  {text}")

def print_error(text: str) -> None:
    """Print error message."""
    print(f"❌ {text}")

def check_required_secrets() -> Dict[str, bool]:
    """Check if required GitHub secrets are set."""
    print_header("GitHub Secrets Validation")
    
    required_secrets = [
        "FABRIC_TENANT_ID",
        "FABRIC_CLIENT_ID", 
        "FABRIC_CLIENT_SECRET",
        "FABRIC_WORKSPACE_ID"
    ]
    
    optional_secrets = [
        "DCE_ENDPOINT_HOST",
        "DCR_IMMUTABLE_ID"
    ]
    
    results = {}
    
    print("Required secrets:")
    for secret in required_secrets:
        value = os.getenv(secret)
        if value and value.strip():
            print_success(f"{secret}: Set")
            results[secret] = True
        else:
            print_error(f"{secret}: Not set or empty")
            results[secret] = False
    
    print("\nOptional secrets:")
    for secret in optional_secrets:
        value = os.getenv(secret)
        if value and value.strip():
            print_success(f"{secret}: Set")
        else:
            print_warning(f"{secret}: Not set (optional)")
    
    return results

def validate_secret_format(secrets: Dict[str, bool]) -> Dict[str, bool]:
    """Validate secret format and structure."""
    print_header("Secret Format Validation")
    
    format_results = {}
    
    # Validate tenant ID format (GUID)
    tenant_id = os.getenv("FABRIC_TENANT_ID", "")
    if tenant_id:
        if len(tenant_id) == 36 and tenant_id.count('-') == 4:
            print_success("FABRIC_TENANT_ID: Valid GUID format")
            format_results["tenant_id_format"] = True
        else:
            print_error("FABRIC_TENANT_ID: Invalid GUID format (should be xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)")
            format_results["tenant_id_format"] = False
    
    # Validate client ID format (GUID)
    client_id = os.getenv("FABRIC_CLIENT_ID", "")
    if client_id:
        if len(client_id) == 36 and client_id.count('-') == 4:
            print_success("FABRIC_CLIENT_ID: Valid GUID format")
            format_results["client_id_format"] = True
        else:
            print_error("FABRIC_CLIENT_ID: Invalid GUID format")
            format_results["client_id_format"] = False
    
    # Validate workspace ID format (GUID)
    workspace_id = os.getenv("FABRIC_WORKSPACE_ID", "")
    if workspace_id:
        if len(workspace_id) == 36 and workspace_id.count('-') == 4:
            print_success("FABRIC_WORKSPACE_ID: Valid GUID format")
            format_results["workspace_id_format"] = True
        else:
            print_error("FABRIC_WORKSPACE_ID: Invalid GUID format")
            format_results["workspace_id_format"] = False
    
    # Validate client secret (should be non-empty string)
    client_secret = os.getenv("FABRIC_CLIENT_SECRET", "")
    if client_secret:
        if len(client_secret) >= 10:  # Reasonable minimum length
            print_success("FABRIC_CLIENT_SECRET: Valid length")
            format_results["client_secret_format"] = True
        else:
            print_error("FABRIC_CLIENT_SECRET: Too short (minimum 10 characters)")
            format_results["client_secret_format"] = False
    
    return format_results

def test_authentication() -> bool:
    """Test authentication with Microsoft Fabric API."""
    print_header("Authentication Test")
    
    try:
        import msal
        import requests
    except ImportError as e:
        print_error(f"Missing required dependencies: {e}")
        print("Install with: pip install msal requests")
        return False
    
    tenant_id = os.getenv("FABRIC_TENANT_ID")
    client_id = os.getenv("FABRIC_CLIENT_ID")
    client_secret = os.getenv("FABRIC_CLIENT_SECRET")
    
    if not all([tenant_id, client_id, client_secret]):
        print_error("Missing required authentication secrets")
        return False
    
    try:
        # Create MSAL app
        app = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=f"https://login.microsoftonline.com/{tenant_id}"
        )
        
        # Try to acquire token
        scopes = ["https://api.fabric.microsoft.com/.default"]
        result = app.acquire_token_for_client(scopes=scopes)
        
        if "access_token" in result:
            print_success("Authentication successful")
            
            # Test API call
            headers = {"Authorization": f"Bearer {result['access_token']}"}
            response = requests.get(
                "https://api.fabric.microsoft.com/v1/workspaces",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                print_success("Fabric API access successful")
                return True
            else:
                print_error(f"Fabric API access failed: {response.status_code}")
                return False
        else:
            print_error(f"Authentication failed: {result.get('error_description', 'Unknown error')}")
            return False
            
    except Exception as e:
        print_error(f"Authentication test failed: {e}")
        return False

def check_workflow_files() -> bool:
    """Check if workflow files exist and are valid."""
    print_header("Workflow Files Check")
    
    workflow_file = ".github/workflows/build-and-upload-to-fabric.yml"
    script_file = ".github/scripts/upload-to-fabric.py"
    
    files_ok = True
    
    if os.path.exists(workflow_file):
        print_success("Workflow file exists")
        try:
            import yaml
            with open(workflow_file, 'r') as f:
                yaml.safe_load(f)
            print_success("Workflow YAML is valid")
        except Exception as e:
            print_error(f"Workflow YAML validation failed: {e}")
            files_ok = False
    else:
        print_error("Workflow file not found")
        files_ok = False
    
    if os.path.exists(script_file):
        print_success("Upload script exists")
        if os.access(script_file, os.X_OK):
            print_success("Upload script is executable")
        else:
            print_warning("Upload script is not executable")
    else:
        print_error("Upload script not found")
        files_ok = False
    
    return files_ok

def generate_setup_commands() -> None:
    """Generate setup commands for the user."""
    print_header("Setup Commands")
    
    print("To set up the deployment workflow:")
    print()
    print("1. Create service principal:")
    print("   az ad sp create-for-rbac --name 'FabricLA-Connector-Deploy' \\")
    print("     --role 'Contributor' \\")
    print("     --scopes '/subscriptions/{subscription-id}'")
    print()
    print("2. Configure GitHub secrets:")
    print("   - Go to repository Settings > Secrets and variables > Actions")
    print("   - Add the following secrets:")
    
    secrets = [
        ("FABRIC_TENANT_ID", "Azure AD tenant ID from service principal output"),
        ("FABRIC_CLIENT_ID", "Service principal appId"),
        ("FABRIC_CLIENT_SECRET", "Service principal password"), 
        ("FABRIC_WORKSPACE_ID", "Target Fabric workspace ID")
    ]
    
    for secret, description in secrets:
        print(f"     - {secret}: {description}")
    
    print()
    print("3. Grant workspace permissions:")
    print("   - Go to Fabric workspace settings")
    print("   - Add service principal with Contributor or Admin role")
    print()
    print("4. Test deployment:")
    print("   - Push to main branch or manually trigger workflow")
    print("   - Check Actions tab for deployment status")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Validate GitHub Actions deployment setup"
    )
    parser.add_argument(
        "--skip-auth-test",
        action="store_true",
        help="Skip authentication test (useful when dependencies are not installed)"
    )
    
    args = parser.parse_args()
    
    print_header("FabricLA-Connector Deployment Setup Validation")
    
    # Check secrets
    secrets_ok = check_required_secrets()
    all_secrets_set = all(secrets_ok.values())
    
    # Check secret formats
    format_results = validate_secret_format(secrets_ok)
    formats_ok = all(format_results.values())
    
    # Check workflow files
    files_ok = check_workflow_files()
    
    # Test authentication if requested and secrets are available
    auth_ok = True
    if not args.skip_auth_test and all_secrets_set and formats_ok:
        auth_ok = test_authentication()
    elif args.skip_auth_test:
        print_header("Authentication Test")
        print_warning("Authentication test skipped (--skip-auth-test flag)")
    
    # Summary
    print_header("Validation Summary")
    
    if all_secrets_set:
        print_success("All required secrets are set")
    else:
        print_error("Some required secrets are missing")
    
    if formats_ok:
        print_success("All secret formats are valid")
    else:
        print_error("Some secrets have invalid formats")
    
    if files_ok:
        print_success("All workflow files are present and valid")
    else:
        print_error("Some workflow files are missing or invalid")
    
    if auth_ok or args.skip_auth_test:
        if not args.skip_auth_test:
            print_success("Authentication test passed")
    else:
        print_error("Authentication test failed")
    
    overall_success = all_secrets_set and formats_ok and files_ok and (auth_ok or args.skip_auth_test)
    
    if overall_success:
        print()
        print_success("✨ Setup validation passed! You're ready to use the deployment workflow.")
        print()
        print("Next steps:")
        print("- Push to main/develop branch to trigger automatic deployment")
        print("- Or go to Actions tab and manually trigger the workflow")
        print("- Check Actions tab for deployment progress and results")
    else:
        print()
        print_error("❌ Setup validation failed. Please fix the issues above.")
        generate_setup_commands()
        sys.exit(1)

if __name__ == "__main__":
    main()