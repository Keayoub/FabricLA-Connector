#!/usr/bin/env python3
"""
Local Testing Script for FabricLA-Connector

This script helps you build and test the FabricLA-Connector package locally,
including building the wheel and uploading it to your Fabric environment.

Usage:
    python test_local_build.py --workspace-id <id> --environment-id <id> [auth options]

Authentication Options:
    --token <token>                     Use bearer token
    --client-id <id> --client-secret <secret> --tenant-id <id>  Use service principal
    (no auth args)                     Use DefaultAzureCredential
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
from typing import Optional, Tuple

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_step(step: str, description: str = ""):
    """Print a step with formatting."""
    print(f"{Colors.BLUE}{Colors.BOLD}🔨 {step}{Colors.END}")
    if description:
        print(f"   {description}")
    print()

def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def check_prerequisites() -> bool:
    """Check if all prerequisites are installed."""
    print_step("Checking Prerequisites")
    
    success = True
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        print_success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print_error(f"Python {python_version.major}.{python_version.minor} is too old. Need Python 3.8+")
        success = False
    
    # Check if pip is available
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      capture_output=True, check=True, text=True)
        print_success("pip is available")
    except subprocess.CalledProcessError:
        print_error("pip is not available")
        success = False
    
    # Check if build tools are available
    try:
        subprocess.run([sys.executable, "-m", "build", "--version"], 
                      capture_output=True, check=True, text=True)
        print_success("build tools are available")
    except subprocess.CalledProcessError:
        print_warning("build package not found, will install it")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "build"], 
                          check=True, capture_output=True)
            print_success("Installed build package")
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to install build package: {e}")
            success = False
    
    return success

def clean_build_artifacts() -> bool:
    """Clean previous build artifacts."""
    print_step("Cleaning Build Artifacts")
    
    project_root = Path(__file__).parent
    artifacts = ['dist', 'build', 'src/fabricla_connector.egg-info']
    
    for artifact in artifacts:
        artifact_path = project_root / artifact
        if artifact_path.exists():
            if artifact_path.is_dir():
                shutil.rmtree(artifact_path)
                print_success(f"Removed directory: {artifact}")
            else:
                artifact_path.unlink()
                print_success(f"Removed file: {artifact}")
        else:
            print(f"   {artifact} (not found)")
    
    return True

def install_dependencies() -> bool:
    """Install package dependencies."""
    print_step("Installing Dependencies")
    
    try:
        # Install in editable mode for development
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], 
                      check=True, cwd=Path(__file__).parent)
        print_success("Installed package in editable mode")
        
        # Install additional dependencies for upload
        subprocess.run([sys.executable, "-m", "pip", "install", "azure-identity", "requests"], 
                      check=True)
        print_success("Installed upload dependencies")
        
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False

def build_wheel() -> Optional[Path]:
    """Build the wheel package."""
    print_step("Building Wheel Package")
    
    project_root = Path(__file__).parent
    
    try:
        # Build the wheel
        result = subprocess.run([sys.executable, "-m", "build", "--wheel"], 
                               cwd=project_root, capture_output=True, text=True, check=True)
        
        print_success("Wheel built successfully")
        
        # Find the wheel file
        dist_dir = project_root / "dist"
        wheel_files = list(dist_dir.glob("*.whl"))
        
        if wheel_files:
            wheel_path = wheel_files[0]  # Get the most recent wheel
            print_success(f"Wheel location: {wheel_path}")
            print(f"   Size: {wheel_path.stat().st_size / 1024:.1f} KB")
            return wheel_path
        else:
            print_error("No wheel file found in dist directory")
            return None
            
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to build wheel: {e}")
        if e.stderr:
            print(f"   Error details: {e.stderr}")
        return None

def validate_wheel(wheel_path: Path) -> bool:
    """Validate the built wheel."""
    print_step("Validating Wheel Package")
    
    try:
        # Use wheel command to show wheel info
        result = subprocess.run([sys.executable, "-m", "wheel", "unpack", "--dest", "temp_validation", str(wheel_path)], 
                               capture_output=True, text=True, check=True, 
                               cwd=wheel_path.parent)
        
        # Clean up temp directory
        temp_dir = wheel_path.parent / "temp_validation"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        print_success("Wheel structure is valid")
        return True
        
    except subprocess.CalledProcessError:
        # If wheel command is not available, try a basic validation
        try:
            import zipfile
            with zipfile.ZipFile(wheel_path, 'r') as wheel_zip:
                files = wheel_zip.namelist()
                
                # Check for essential files
                has_init = any('__init__.py' in f for f in files)
                has_metadata = any('METADATA' in f for f in files)
                
                if has_init and has_metadata:
                    print_success("Basic wheel validation passed")
                    return True
                else:
                    print_error("Wheel missing essential files")
                    return False
                    
        except Exception as e:
            print_error(f"Failed to validate wheel: {e}")
            return False

def upload_to_fabric(wheel_path: Path, workspace_id: str, environment_id: str, 
                    token: Optional[str] = None, client_id: Optional[str] = None,
                    client_secret: Optional[str] = None, tenant_id: Optional[str] = None,
                    publish: bool = False) -> bool:
    """Upload wheel to Fabric environment."""
    print_step("Uploading to Fabric Environment")
    
    # Use the unified upload script
    upload_script = Path(__file__).parent / "tools" / "upload_wheel_to_fabric.py"
    
    if not upload_script.exists():
        print_error(f"Upload script not found: {upload_script}")
        return False
    
    cmd = [
        sys.executable, str(upload_script),
        "--workspace-id", workspace_id,
        "--environment-id", environment_id,
        "--file", str(wheel_path)
    ]
    
    # Add publish flag if requested
    if publish:
        cmd.append("--publish")
        print("   🚀 Auto-publish enabled - package will be immediately active")
    else:
        print("   📦 Upload to staging only - manual publish required")
    
    # Add authentication arguments
    if token:
        cmd.extend(["--token", token])
        print("   Using bearer token authentication")
    elif client_id and client_secret and tenant_id:
        cmd.extend([
            "--client-id", client_id,
            "--client-secret", client_secret,
            "--tenant-id", tenant_id
        ])
        print("   Using service principal authentication")
    else:
        print("   Using DefaultAzureCredential authentication")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print_success("Upload completed successfully")
        
        if result.stdout:
            print("   Upload output:")
            for line in result.stdout.strip().split('\n'):
                print(f"     {line}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Upload failed: {e}")
        if e.stdout:
            print("   Output:")
            for line in e.stdout.strip().split('\n'):
                print(f"     {line}")
        if e.stderr:
            print("   Error details:")
            for line in e.stderr.strip().split('\n'):
                print(f"     {line}")
        return False

def test_import() -> bool:
    """Test importing the built package."""
    print_step("Testing Package Import")
    
    try:
        # Test basic imports
        import fabricla_connector
        print_success("Main package import successful")
        
        from fabricla_connector import api
        print_success("API module import successful")
        
        from fabricla_connector import config
        print_success("Config module import successful")
        
        from fabricla_connector import workflows
        print_success("Workflows module import successful")
        
        # Test version
        if hasattr(fabricla_connector, '__version__'):
            print_success(f"Package version: {fabricla_connector.__version__}")
        
        return True
        
    except ImportError as e:
        print_error(f"Import test failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error during import test: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Build and test FabricLA-Connector locally")
    
    # Fabric environment details
    parser.add_argument("--workspace-id", required=True, help="Fabric workspace ID")
    parser.add_argument("--environment-id", required=True, help="Fabric environment ID")
    
    # Authentication options
    parser.add_argument("--token", help="Bearer token for authentication")
    parser.add_argument("--client-id", help="Azure AD client ID")
    parser.add_argument("--client-secret", help="Azure AD client secret")
    parser.add_argument("--tenant-id", help="Azure AD tenant ID")
    
    # Options
    parser.add_argument("--skip-upload", action="store_true", help="Skip upload step")
    parser.add_argument("--skip-clean", action="store_true", help="Skip cleaning build artifacts")
    parser.add_argument("--publish", action="store_true", help="Auto-publish environment after upload (makes package immediately active)")
    
    args = parser.parse_args()
    
    # Validate service principal args
    sp_args = [args.client_id, args.client_secret, args.tenant_id]
    if any(sp_args) and not all(sp_args):
        print_error("If using service principal auth, must provide --client-id, --client-secret, AND --tenant-id")
        sys.exit(1)
    
    print(f"{Colors.BOLD}🧪 FabricLA-Connector Local Testing{Colors.END}")
    print("=" * 50)
    print(f"Workspace ID: {args.workspace_id}")
    print(f"Environment ID: {args.environment_id}")
    
    if args.token:
        print("Authentication: Bearer Token")
    elif args.client_id:
        print("Authentication: Service Principal")
    else:
        print("Authentication: DefaultAzureCredential")
    print()
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    # Run the build and test process
    steps_completed = 0
    total_steps = 6 if not args.skip_upload else 5
    
    try:
        # Step 1: Check prerequisites
        if not check_prerequisites():
            print_error("Prerequisites check failed")
            sys.exit(1)
        steps_completed += 1
        
        # Step 2: Clean build artifacts
        if not args.skip_clean:
            if not clean_build_artifacts():
                print_error("Failed to clean build artifacts")
                sys.exit(1)
        steps_completed += 1
        
        # Step 3: Install dependencies
        if not install_dependencies():
            print_error("Failed to install dependencies")
            sys.exit(1)
        steps_completed += 1
        
        # Step 4: Build wheel
        wheel_path = build_wheel()
        if not wheel_path:
            print_error("Failed to build wheel")
            sys.exit(1)
        steps_completed += 1
        
        # Step 5: Validate wheel
        if not validate_wheel(wheel_path):
            print_error("Wheel validation failed")
            sys.exit(1)
        steps_completed += 1
        
        # Step 6: Test import
        if not test_import():
            print_error("Import test failed")
            sys.exit(1)
        steps_completed += 1
        
        # Step 7: Upload to Fabric (optional)
        if not args.skip_upload:
            if not upload_to_fabric(
                wheel_path, args.workspace_id, args.environment_id,
                args.token, args.client_id, args.client_secret, args.tenant_id,
                publish=args.publish
            ):
                print_error("Upload to Fabric failed")
                sys.exit(1)
            steps_completed += 1
        
        # Success summary
        print()
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 All tests completed successfully!{Colors.END}")
        print(f"   Steps completed: {steps_completed}")
        print(f"   Wheel location: {wheel_path}")
        
        if not args.skip_upload:
            print()
            print("📋 Next Steps:")
            print("1. Go to your Fabric environment")
            print("2. Publish the staged libraries to make them active")
            print("3. Test the connector in a Fabric notebook")
        
    except KeyboardInterrupt:
        print()
        print_warning("Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()