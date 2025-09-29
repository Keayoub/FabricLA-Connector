# Tools Documentation - FabricLA-Connector

Comprehensive development and testing tools for building, testing, and uploading the FabricLA-Connector Python package to Microsoft Fabric environments.

## 🛠️ Available Tools

### 1. **upload_wheel_to_fabric.py** - Main Upload Tool

The unified upload script that supports both staging and auto-publish workflows with multiple authentication methods.

#### **Basic Usage**

```bash
# Upload to staging (manual publish later)
python upload_wheel_to_fabric.py --wheel-path dist/fabricla_connector-1.0.0-py3-none-any.whl --workspace-id YOUR_ID --environment-id YOUR_ID

# Upload and auto-publish (immediate activation)
python upload_wheel_to_fabric.py --wheel-path dist/fabricla_connector-1.0.0-py3-none-any.whl --workspace-id YOUR_ID --environment-id YOUR_ID --publish
```

#### **Authentication Options**

```bash
# Option 1: Azure CLI (Recommended for development)
az login
python upload_wheel_to_fabric.py [other-args]

# Option 2: Service Principal via environment
export FABRIC_APP_ID="your-app-id"
export FABRIC_APP_SECRET="your-app-secret"
export FABRIC_TENANT_ID="your-tenant-id"
python upload_wheel_to_fabric.py [other-args]

# Option 3: Bearer Token
python upload_wheel_to_fabric.py --bearer-token "your-token" [other-args]
```

#### **Complete Parameter Reference**

```bash
python upload_wheel_to_fabric.py \
  --wheel-path "dist/fabricla_connector-1.0.0-py3-none-any.whl" \
  --workspace-id "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  --environment-id "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  --publish \                          # Optional: auto-publish after upload
  --bearer-token "your-token" \        # Optional: manual auth token
  --app-id "your-app-id" \            # Optional: service principal ID
  --app-secret "your-secret" \        # Optional: service principal secret
  --tenant-id "your-tenant-id"        # Optional: tenant ID
```

### 2. **test_local_build.py** - Automated Testing Workflow

Automates the complete build → test → upload workflow for local development.

#### **Basic Usage**

```bash
# Build only (no upload)
python test_local_build.py --workspace-id YOUR_ID --environment-id YOUR_ID --skip-upload

# Build and upload to staging
python test_local_build.py --workspace-id YOUR_ID --environment-id YOUR_ID

# Build, upload, and auto-publish
python test_local_build.py --workspace-id YOUR_ID --environment-id YOUR_ID --publish
```

#### **What It Does**

1. **Cleans** previous builds (`dist/`, `build/`, `*.egg-info`)
2. **Builds** wheel package using `pip wheel`
3. **Validates** wheel contents and dependencies
4. **Uploads** to Fabric environment
5. **Optionally publishes** for immediate activation

#### **Complete Parameter Reference**

```bash
python test_local_build.py \
  --workspace-id "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  --environment-id "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  --publish \                    # Optional: auto-publish after upload
  --skip-upload \                # Optional: build only, no upload
  --bearer-token "your-token"    # Optional: manual auth token
```

## 🔐 Authentication Methods Explained

### **Method 1: Azure CLI (Recommended for Development)**

**Setup:**
```bash
az login
# Optionally set specific tenant
az login --tenant your-tenant-id
```

**Benefits:**
- ✅ No secrets to manage
- ✅ Automatic token refresh
- ✅ Works with MFA
- ✅ Respects Azure CLI configuration

**Use Case:** Local development, testing

### **Method 2: Service Principal (Recommended for CI/CD)**

**Setup:**
```bash
# Set environment variables
export FABRIC_APP_ID="your-app-id"
export FABRIC_APP_SECRET="your-app-secret"
export FABRIC_TENANT_ID="your-tenant-id"

# Or pass as command line arguments
python upload_wheel_to_fabric.py --app-id YOUR_ID --app-secret YOUR_SECRET --tenant-id YOUR_TENANT [other-args]
```

**Benefits:**
- ✅ Programmatic authentication
- ✅ No interactive login required
- ✅ Perfect for automation
- ✅ Granular permissions control

**Use Case:** CI/CD pipelines, automation scripts

### **Method 3: Bearer Token (Manual)**

**Setup:**
```bash
# Get token manually (from browser dev tools, Postman, etc.)
python upload_wheel_to_fabric.py --bearer-token "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIs..." [other-args]
```

**Benefits:**
- ✅ Works when other methods fail
- ✅ Direct token control
- ✅ Useful for debugging

**Use Case:** Troubleshooting, one-off operations

## 📦 Deployment Strategy Guide

### **Staging Workflow (Recommended for Production)**

```bash
# 1. Upload to staging
python upload_wheel_to_fabric.py --wheel-path dist/your-package.whl --workspace-id YOUR_ID --environment-id YOUR_ID

# 2. Test in Fabric environment
# - Import package in notebook
# - Run validation tests
# - Check for conflicts

# 3. Publish when ready
# Use Fabric UI or API call to publish
```

**Benefits:**
- ✅ Review before activation
- ✅ Test in staging environment
- ✅ Rollback capability
- ✅ Security validation

### **Auto-Publish Workflow (Recommended for Development)**

```bash
# Upload and immediately activate
python upload_wheel_to_fabric.py --wheel-path dist/your-package.whl --workspace-id YOUR_ID --environment-id YOUR_ID --publish
```

**Benefits:**
- ✅ Faster iteration cycle
- ✅ Single command deployment
- ✅ Immediate testing capability

**Caution:** ⚠️ No review step - use carefully in production

## 🧪 Testing Workflows

### **Development Testing**

```bash
# Quick development cycle
python test_local_build.py --workspace-id YOUR_ID --environment-id YOUR_ID --publish

# Then in Fabric notebook:
# import fabricla_connector
# ... test your changes ...
```

### **Pre-Production Testing**

```bash
# 1. Build and stage
python test_local_build.py --workspace-id YOUR_ID --environment-id YOUR_ID

# 2. Manual testing in Fabric
# 3. Publish via UI when ready
```

### **CI/CD Integration**

```bash
# In your CI pipeline
export FABRIC_APP_ID="${{ secrets.FABRIC_APP_ID }}"
export FABRIC_APP_SECRET="${{ secrets.FABRIC_APP_SECRET }}"
export FABRIC_TENANT_ID="${{ secrets.FABRIC_TENANT_ID }}"

python test_local_build.py \
  --workspace-id "${{ vars.FABRIC_WORKSPACE_ID }}" \
  --environment-id "${{ vars.FABRIC_ENVIRONMENT_ID }}" \
  --publish
```

## 🔍 Troubleshooting

### **Authentication Issues**

```bash
# Check Azure CLI login
az account show

# Test service principal
az login --service-principal --username $FABRIC_APP_ID --password $FABRIC_APP_SECRET --tenant $FABRIC_TENANT_ID

# Verify permissions
# Ensure your account/service principal has:
# - Fabric.ReadWrite.All API permissions
# - Workspace member/admin access
```

### **Upload Failures**

```bash
# Check wheel file exists
ls -la dist/

# Verify workspace/environment IDs
# Use Fabric portal URLs to confirm GUIDs

# Tools Documentation - FabricLA-Connector

This directory contains small developer utilities used to build, test, and
upload the package to a Microsoft Fabric environment.

The main tools documented here:

- `upload_wheel_to_fabric.py` — upload a package file to Fabric staging and
  optionally publish the environment.
- `upload_wheel_to_blob.py` — upload a package file to Azure Blob Storage (adds
  optional SAS generation).
- `test_local_build.py` — local build → test → upload harness for development.

## upload_wheel_to_fabric.py

Purpose: upload a package file accepted by Fabric (wheels, sdists, zips, eggs)
to a Fabric workspace environment's staging libraries, with retries and an
optional publish step.

Key points
- Supported file types: any file type accepted by Fabric. The script uses
  `mimetypes.guess_type()` to set the multipart Content-Type.
- Authentication precedence (highest → lowest):
  1. `--token` (explicit bearer token)
  2. Service principal (`--client-id` / `--client-secret` / `--tenant-id`)
  3. `--use-default-credential` (DefaultAzureCredential; picks up `az login`,
     Managed Identity, or env vars)
- Retry: exponential backoff (configurable via `--retries`).

Usage examples

Upload to staging:

```powershell
py tools\upload_wheel_to_fabric.py --workspace-id <WS_ID> --environment-id <ENV_ID> --file dist\your-package.whl
```

Upload and publish immediately:

```powershell
py tools\upload_wheel_to_fabric.py --workspace-id <WS_ID> --environment-id <ENV_ID> --file dist\your-package.whl --publish
```

Using DefaultAzureCredential (dev / az login):

```powershell
py tools\upload_wheel_to_fabric.py --workspace-id <WS_ID> --environment-id <ENV_ID> --file dist\your-package.whl --use-default-credential
```

Using service principal:

```powershell
py tools\upload_wheel_to_fabric.py --workspace-id <WS_ID> --environment-id <ENV_ID> --file dist\your-package.whl --client-id <ID> --client-secret <SECRET> --tenant-id <TENANT>
```

Important notes
- If you pass `--use-default-credential`, make sure `azure-identity` is
  installed and you have logged in with `az login` or provided MI credentials.
- For CI/CD, prefer a service principal with minimal required permissions.

## upload_wheel_to_blob.py

Purpose: upload a package file to Azure Blob Storage. Supports both connection
string and credential (DefaultAzureCredential or ClientSecretCredential) auth.

Key points
- Can upload via `--connection-string` (existing behavior).
- Can authenticate with AAD via `--account-url` + `--use-default-credential`,
  or `--account-url` + `--client-id`/`--client-secret`/`--tenant-id`.
- SAS generation (`--generate-sas`) requires the storage account key which is
  typically only available in a connection string; SAS cannot be generated
  with AAD-only credentials.

Usage examples

Upload with connection string (account key present):

```powershell
py tools\upload_wheel_to_blob.py --file dist\your-package.whl --container mycontainer --connection-string "DefaultEndpointsProtocol=...;AccountName=...;AccountKey=...;"
```

Upload using DefaultAzureCredential:

```powershell
py tools\upload_wheel_to_blob.py --file dist\your-package.whl --container mycontainer --account-url https://<acct>.blob.core.windows.net --use-default-credential
```

Generate SAS (only with account key in connection string):

```powershell
py tools\upload_wheel_to_blob.py --file dist\your-package.whl --container mycontainer --connection-string "...AccountKey=..." --generate-sas
```

## test_local_build.py

Purpose: local convenience script to build the wheel, run a small validation
import test, and optionally upload to Fabric (and publish).

Usage highlights

```powershell
py tools\test_local_build.py --workspace-id <WS_ID> --environment-id <ENV_ID>
# or to skip upload
py tools\test_local_build.py --workspace-id <WS_ID> --environment-id <ENV_ID> --skip-upload
```

## Authentication and permissions

- For `--use-default-credential`, install `azure-identity` and sign in with
  `az login` (developer) or use Managed Identity in cloud hosts. The principal
  needs write permissions to the Fabric workspace/environment (workspace
  membership or an appropriate Fabric permission).
- For CI, use a service principal (ClientSecretCredential) and grant only the
  least privilege needed to upload and publish packages.

## Dependencies

- `requests` (required)
- `azure-identity` (required when using AAD-based auth flows)
- `azure-storage-blob` (required if you run `upload_wheel_to_blob.py` with
  connection-string or SAS generation)

Install (recommended in a virtualenv):

```powershell
py -m pip install -r requirements.txt
# or install individually
py -m pip install requests azure-identity azure-storage-blob
```

## Troubleshooting

- "Unauthorized" → confirm the auth method and that the identity has Fabric
  workspace access and the correct API permissions.
- "Environment not found" → verify the workspace-id and environment-id GUIDs.
- If DefaultAzureCredential fails, run `az login` locally or validate
  environment-managed identity on the host.

## Quick checklist before uploading

1. Build your package into `dist/` (e.g., `python -m build --wheel`).
2. Confirm the package file exists and is the correct version.
3. Choose auth method (token / service principal / DefaultAzureCredential).
4. Run the upload script and optionally `--publish` when ready.

---

See the main project `README.md` for higher-level onboarding and infra
instructions.