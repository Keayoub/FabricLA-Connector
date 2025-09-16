#!/usr/bin/env python3
"""
Enhanced upload script with optional publish functionality.

This script uploads a Python wheel (.whl) file to a Fabric Environment
and optionally publishes it immediately.

Usage:
    # Upload to staging only (current behavior)
    python tools/upload_wheel_to_fabric_enhanced.py \
        --workspace-id YOUR_WORKSPACE_ID \
        --environment-id YOUR_ENV_ID \
        --file dist/fabricla_connector-1.0.0-py3-none-any.whl

    # Upload and publish immediately  
    python tools/upload_wheel_to_fabric_enhanced.py \
        --workspace-id YOUR_WORKSPACE_ID \
        --environment-id YOUR_ENV_ID \
        --file dist/fabricla_connector-1.0.0-py3-none-any.whl \
        --publish

Authentication options:
    --token BEARER_TOKEN                    # Bearer token
    --client-id ID --client-secret SECRET   # Service principal
    # Or use DefaultAzureCredential (az login)
"""

import argparse
import os
import sys
import time
import json
import requests
from typing import Dict, Any, Optional

def safe_print(*args, **kwargs):
    """Print function that handles encoding issues on Windows."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fall back to ASCII-only output
        ascii_args = []
        for arg in args:
            if isinstance(arg, str):
                # Remove or replace all Unicode characters
                arg = arg.encode('ascii', 'replace').decode('ascii')
            ascii_args.append(arg)
        print(*ascii_args, **kwargs)

try:
    from azure.identity import DefaultAzureCredential, ClientSecretCredential
    AZURE_IDENTITY_AVAILABLE = True
except ImportError:
    AZURE_IDENTITY_AVAILABLE = False

class FabricEnvironmentManager:
    """Enhanced Fabric Environment manager with upload and publish capabilities."""
    
    def __init__(self, workspace_id: str, environment_id: str, 
                 token: str = None, client_id: str = None, 
                 client_secret: str = None, tenant_id: str = None):
        self.workspace_id = workspace_id
        self.environment_id = environment_id
        self.base_url = "https://api.fabric.microsoft.com/v1"
        
        # Authentication
        self.token = self._get_token(token, client_id, client_secret, tenant_id)
        
        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        })
    
    def _get_token(self, token: str, client_id: str, client_secret: str, tenant_id: str) -> str:
        """Get authentication token using various methods."""
        
        if token:
            safe_print("🔑 Using provided bearer token")
            return token
        
        if client_id and client_secret and tenant_id:
            if not AZURE_IDENTITY_AVAILABLE:
                raise Exception("azure-identity package required for service principal auth")
            
            safe_print("🔑 Using service principal authentication")
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            return credential.get_token("https://api.fabric.microsoft.com/.default").token
        
        if AZURE_IDENTITY_AVAILABLE:
            safe_print("🔑 Using DefaultAzureCredential (Azure CLI)")
            credential = DefaultAzureCredential()
            return credential.get_token("https://api.fabric.microsoft.com/.default").token
        
        raise Exception("No authentication method available. Provide token or install azure-identity")
    
    def upload_wheel(self, wheel_path: str) -> Dict[str, Any]:
        """Upload wheel file to staging libraries."""
        
        if not os.path.exists(wheel_path):
            raise FileNotFoundError(f"Wheel file not found: {wheel_path}")
        
        wheel_name = os.path.basename(wheel_path)
        wheel_size = os.path.getsize(wheel_path)
        
        safe_print(f"📦 Uploading {wheel_name} ({wheel_size / 1024:.1f} KB)")
        
        url = f"{self.base_url}/workspaces/{self.workspace_id}/environments/{self.environment_id}/staging/libraries"
        
        with open(wheel_path, 'rb') as f:
            files = {'file': (wheel_name, f, 'application/zip')}
            
            # Remove Content-Type for multipart upload
            headers = {k: v for k, v in self.session.headers.items() if k.lower() != 'content-type'}
            
            response = self.session.post(url, files=files, headers=headers, timeout=120)
        
        if response.status_code == 200:
            safe_print(f"✅ Upload successful: {wheel_name} (staged)")
            return {
                'success': True,
                'message': f'Library {wheel_name} uploaded to staging',
                'status_code': response.status_code,
                'wheel_name': wheel_name
            }
        else:
            error_msg = f"Upload failed: HTTP {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {response.text}"
            
            safe_print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'status_code': response.status_code
            }
    
    def publish_environment(self) -> Dict[str, Any]:
        """Publish the environment to make staging changes effective."""
        
        safe_print("🚀 Publishing environment...")
        
        url = f"{self.base_url}/workspaces/{self.workspace_id}/environments/{self.environment_id}/staging/publish"
        
        response = self.session.post(url, timeout=120)
        
        if response.status_code in [200, 202]:
            safe_print("✅ Publish initiated successfully")
            
            # Check if it's a long-running operation
            if response.status_code == 202:
                operation_id = response.headers.get('x-ms-operation-id')
                safe_print(f"📊 Long-running operation ID: {operation_id}")
                
                # Wait for completion (optional)
                return self._wait_for_publish_completion(operation_id)
            
            return {
                'success': True,
                'message': 'Environment published successfully',
                'status_code': response.status_code
            }
        else:
            error_msg = f"Publish failed: HTTP {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {response.text}"
            
            safe_print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'status_code': response.status_code
            }
    
    def _wait_for_publish_completion(self, operation_id: str, max_wait: int = 300) -> Dict[str, Any]:
        """Wait for publish operation to complete."""
        
        if not operation_id:
            return {'success': True, 'message': 'Publish completed (no operation ID)'}
        
        operation_url = f"{self.base_url}/operations/{operation_id}"
        safe_print(f"⏳ Waiting for publish completion (max {max_wait}s)...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                response = self.session.get(operation_url)
                if response.status_code == 200:
                    operation_status = response.json()
                    status = operation_status.get('status', 'Unknown')
                    
                    if status == 'Succeeded':
                        safe_print("✅ Publish completed successfully")
                        return {
                            'success': True,
                            'message': 'Environment published and active',
                            'operation_status': operation_status
                        }
                    elif status == 'Failed':
                        error_msg = operation_status.get('error', 'Unknown error')
                        safe_print(f"❌ Publish failed: {error_msg}")
                        return {
                            'success': False,
                            'error': f'Publish operation failed: {error_msg}',
                            'operation_status': operation_status
                        }
                    elif status in ['Running', 'NotStarted']:
                        safe_print(f"⏳ Status: {status}")
                        time.sleep(10)
                    else:
                        safe_print(f"⚠️ Unknown status: {status}")
                        time.sleep(10)
                else:
                    safe_print(f"⚠️ Unable to check operation status: HTTP {response.status_code}")
                    time.sleep(10)
            except Exception as e:
                safe_print(f"⚠️ Error checking operation status: {e}")
                time.sleep(10)
        
        safe_print("⏰ Timeout waiting for publish completion")
        return {
            'success': False,
            'error': 'Timeout waiting for publish completion',
            'message': 'Check Fabric UI for publish status'
        }

def main():
    parser = argparse.ArgumentParser(description='Upload wheel to Fabric Environment with optional publish')
    parser.add_argument('--workspace-id', required=True, help='Fabric workspace ID')
    parser.add_argument('--environment-id', required=True, help='Fabric environment ID')
    parser.add_argument('--file', required=True, help='Path to wheel file')
    parser.add_argument('--publish', action='store_true', help='Publish environment after upload')
    
    # Authentication options
    parser.add_argument('--token', help='Bearer token for authentication')
    parser.add_argument('--client-id', help='Service principal client ID')
    parser.add_argument('--client-secret', help='Service principal client secret')
    parser.add_argument('--tenant-id', help='Azure tenant ID')
    
    args = parser.parse_args()
    
    try:
        # Initialize manager
        manager = FabricEnvironmentManager(
            workspace_id=args.workspace_id,
            environment_id=args.environment_id,
            token=args.token,
            client_id=args.client_id,
            client_secret=args.client_secret,
            tenant_id=args.tenant_id
        )
        
        # Upload wheel
        upload_result = manager.upload_wheel(args.file)
        
        if not upload_result['success']:
            sys.exit(1)
        
        # Publish if requested
        if args.publish:
            safe_print("🔄 Auto-publish enabled")
            publish_result = manager.publish_environment()
            
            if not publish_result['success']:
                safe_print("⚠️ Upload succeeded but publish failed")
                safe_print("💡 Package is in staging - you can publish manually from Fabric UI")
                sys.exit(1)
            else:
                safe_print("🎉 Upload and publish completed successfully!")
        else:
            safe_print("📋 Package uploaded to staging")
            safe_print("💡 Use Fabric UI or add --publish flag to make it active")
        
        safe_print(f"🎯 Workspace: {args.workspace_id}")
        safe_print(f"🎯 Environment: {args.environment_id}")
        
    except Exception as e:
        safe_print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()