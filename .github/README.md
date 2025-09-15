# GitHub Actions Workflow: Build and Upload to Fabric

This workflow automates the process of building the FabricLA-Connector Python wheel package and uploading it to your Microsoft Fabric environment.

## Overview

The workflow consists of three main jobs:

1. **Build**: Creates a Python wheel package from the source code
2. **Upload to Fabric**: Uploads the wheel to your Fabric workspace environment
3. **Release**: Creates a GitHub release for tagged versions (optional)

## Workflow Triggers

The workflow runs on:

- **Push to main/develop branches**: Builds and uploads the package
- **Tagged releases** (v*): Builds, uploads, and creates a GitHub release
- **Pull requests**: Builds only (no upload)
- **Manual trigger**: Allows custom workspace ID and upload control

## Setup Requirements

### 1. GitHub Secrets

Configure the following secrets in your GitHub repository:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `FABRIC_TENANT_ID` | Azure AD tenant ID | `00000000-0000-0000-0000-000000000000` |
| `FABRIC_CLIENT_ID` | Service principal client ID | `11111111-1111-1111-1111-111111111111` |
| `FABRIC_CLIENT_SECRET` | Service principal client secret | `your-client-secret` |
| `FABRIC_WORKSPACE_ID` | Default Fabric workspace ID | `22222222-2222-2222-2222-222222222222` |

### 2. Service Principal Setup

Create a service principal with appropriate permissions:

```bash
# Create service principal
az ad sp create-for-rbac --name "FabricLA-Connector-Deploy" \
  --role "Contributor" \
  --scopes "/subscriptions/{subscription-id}"

# Note the output values for the GitHub secrets:
# - appId -> FABRIC_CLIENT_ID
# - password -> FABRIC_CLIENT_SECRET  
# - tenant -> FABRIC_TENANT_ID
```

### 3. Fabric Workspace Permissions

Ensure the service principal has permissions in your Fabric workspace:

1. Go to your Fabric workspace
2. Navigate to **Workspace settings** > **Security**
3. Add the service principal with **Contributor** or **Admin** role

## Usage

### Automatic Deployment

The workflow automatically triggers on:

```yaml
# Automatic triggers
on:
  push:
    branches: [main, develop]
    tags: ['v*']
  pull_request:
    branches: [main]
```

### Manual Deployment

You can manually trigger the workflow from the GitHub Actions tab:

1. Go to **Actions** > **Build and Upload FabricLA-Connector to Fabric Environment**
2. Click **Run workflow**
3. Optionally specify:
   - Custom Fabric workspace ID
   - Whether to upload to Fabric (default: true)

## Workflow Outputs

### Build Artifacts

- **Python wheel**: Available as GitHub Actions artifact
- **Package validation**: Automated wheel integrity checks
- **Version extraction**: Automatic version detection from setup.py

### Fabric Deployment

- **Package upload**: Wheel uploaded to Fabric workspace
- **Deployment summary**: Available in the workflow summary
- **Usage instructions**: Generated for Fabric notebook integration

### GitHub Release

For tagged versions (v*), the workflow creates:

- **GitHub release** with release notes
- **Wheel attachment** for manual download
- **Installation instructions** in release description

## Package Usage in Fabric

After successful deployment, use the package in your Fabric notebooks:

```python
# Option 1: If package is in environment
from fabricla_connector import (
    acquire_token, get_capacities, get_workspaces,
    collect_capacity_metrics, post_rows_to_dcr
)

# Option 2: Manual installation if needed
%pip install /path/to/fabricla_connector-1.0.0-py3-none-any.whl

# Then import
from fabricla_connector import acquire_token, get_capacities
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify GitHub secrets are correctly set
   - Check service principal permissions
   - Ensure tenant ID is correct

2. **Workspace Not Found**
   - Verify workspace ID is correct
   - Check service principal has workspace access
   - Ensure workspace is in the same tenant

3. **Build Failed**
   - Check setup.py for syntax errors
   - Verify all dependencies are properly specified
   - Review Python version compatibility

### Debug Mode

Enable debug mode by adding to your workflow:

```yaml
env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true
```

## Customization

### Custom Upload Logic

Modify `.github/scripts/upload-to-fabric.py` to implement custom upload logic:

```python
def upload_package_to_environment(self, workspace_id, wheel_path, package_name, version):
    # Add your custom upload implementation here
    # This might involve:
    # - Fabric-specific APIs
    # - Azure Storage integration
    # - Custom package management
    pass
```

### Environment-Specific Deployments

Create environment-specific workflows:

```yaml
# .github/workflows/deploy-prod.yml
on:
  push:
    tags: ['v*']
    
jobs:
  deploy-prod:
    environment: production
    # ... deployment steps
```

## Security Considerations

1. **Secrets Management**: Store sensitive values in GitHub secrets
2. **Branch Protection**: Limit deployment to protected branches
3. **Environment Reviews**: Use GitHub environments for approval workflows
4. **Audit Logging**: Monitor deployment activities in GitHub Actions logs

## Integration with Fabric

The uploaded wheel package integrates seamlessly with your existing Fabric infrastructure:

- **DCR Configuration**: Works with existing Data Collection Rules
- **Log Analytics**: Integrates with current Log Analytics workspaces  
- **Monitoring**: Supports existing monitoring and alerting setup
- **Notebooks**: Compatible with all Fabric notebook environments