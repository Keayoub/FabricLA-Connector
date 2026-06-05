#!/usr/bin/env python3
"""
Fabric Requirements Downloader
Downloads the latest official pip package lists from Microsoft Synapse Spark Runtime repository
https://github.com/microsoft/synapse-spark-runtime/tree/main/Fabric
"""

import requests
import yaml
import sys
from pathlib import Path
from typing import Dict, List, Optional

def download_fabric_runtime_yaml(runtime_version: str) -> Optional[Dict]:
    """Download the YAML file from Microsoft Synapse Spark Runtime repository."""
    if runtime_version == "1.2":
        url = "https://raw.githubusercontent.com/microsoft/synapse-spark-runtime/main/Fabric/Runtime%201.2%20(Spark%203.4)/Fabric-Python310-CPU.yml"
        python_version = "3.10"
    elif runtime_version == "1.3":
        url = "https://raw.githubusercontent.com/microsoft/synapse-spark-runtime/main/Fabric/Runtime%201.3%20(Spark%203.5)/Fabric-Python311-CPU.yml"
        python_version = "3.11"
    else:
        print(f"Unsupported runtime version: {runtime_version}")
        return None

    print(f"Downloading Fabric Runtime {runtime_version} (Python {python_version}) from Microsoft repository...")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Parse YAML content
        yaml_content = yaml.safe_load(response.text)
        print(f"Successfully downloaded runtime specifications")
        return yaml_content

    except requests.exceptions.RequestException as e:
        print(f"Failed to download from {url}: {e}")
        return None
    except yaml.YAMLError as e:
        print(f"Failed to parse YAML content: {e}")
        return None

def extract_pip_packages(yaml_content: Dict) -> List[str]:
    """Extract the official pip package list from the YAML content."""
    pip_packages = []

    # The official Fabric runtime files publish pip packages under the pip section.
    dependencies = yaml_content.get('dependencies', [])

    for dep in dependencies:
        if isinstance(dep, dict) and 'pip' in dep:
            pip_packages.extend(dep['pip'])
            break

    return pip_packages

def create_requirements_file(runtime_version: str, pip_packages: List[str]) -> str:
    """Create a requirements.txt file content from the official pip package list."""
    content = []

    # Header
    content.append(f"# Fabric Runtime {runtime_version} - Official Microsoft Dependencies")
    content.append(f"# Downloaded from: https://github.com/microsoft/synapse-spark-runtime")
    content.append(f"# Generated on: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    content.append("")

    content.append("# Official pip packages from the selected Fabric runtime")
    content.extend(pip_packages)

    return '\n'.join(content)

def main():
    """Main function to download and create requirements files."""
    print("Fabric Requirements Downloader")
    print("=" * 50)

    # Ask user for runtime version
    while True:
        runtime_choice = input("Select Fabric Runtime version (1.2 or 1.3): ").strip()
        if runtime_choice in ["1.2", "1.3"]:
            break
        print("Please enter '1.2' or '1.3'")

    # Download YAML content
    yaml_content = download_fabric_runtime_yaml(runtime_choice)
    if not yaml_content:
        print("Failed to download runtime specifications")
        return False

    # Extract packages
    pip_packages = extract_pip_packages(yaml_content)
    print(f"Found {len(pip_packages)} official pip packages")

    # Create requirements file content
    requirements_content = create_requirements_file(runtime_choice, pip_packages)

    # Save to file
    filename = f"requirements-fabric-{runtime_choice}.txt"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(requirements_content)
        print(f"Created {filename}")

        # Also create a generic requirements.txt if it doesn't exist
        if not Path("requirements.txt").exists():
            with open("requirements.txt", 'w', encoding='utf-8') as f:
                f.write(requirements_content)
            print(f"Created requirements.txt")

        print(f"\nRequirements file created with {len(pip_packages)} packages")
        print(f"File location: {Path(filename).absolute()}")

        return True

    except Exception as e:
        print(f"Failed to save requirements file: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
