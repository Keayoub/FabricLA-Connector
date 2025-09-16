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

# Test with minimal wheel
python upload_wheel_to_fabric.py --wheel-path dist/simple-package.whl [args] --publish
```

### **Common Error Messages**

- **"Unauthorized"** → Check authentication method and permissions
- **"Environment not found"** → Verify workspace-id and environment-id
- **"File already exists"** → Use staging workflow or increment version
- **"Invalid wheel format"** → Check wheel build process

## 📋 Command Reference

### **Upload Tool Commands**

```bash
# Minimal upload to staging
python upload_wheel_to_fabric.py --wheel-path WHEEL --workspace-id ID --environment-id ID

# Auto-publish
python upload_wheel_to_fabric.py --wheel-path WHEEL --workspace-id ID --environment-id ID --publish

# With service principal
python upload_wheel_to_fabric.py --wheel-path WHEEL --workspace-id ID --environment-id ID --app-id ID --app-secret SECRET --tenant-id ID

# With bearer token
python upload_wheel_to_fabric.py --wheel-path WHEEL --workspace-id ID --environment-id ID --bearer-token TOKEN
```

### **Test Script Commands**

```bash
# Build only
python test_local_build.py --workspace-id ID --environment-id ID --skip-upload

# Build and stage
python test_local_build.py --workspace-id ID --environment-id ID

# Build and auto-publish
python test_local_build.py --workspace-id ID --environment-id ID --publish

# With custom auth
python test_local_build.py --workspace-id ID --environment-id ID --bearer-token TOKEN
```

---

**💡 Need help?** Check the main [project README](../README.md) or [deployment options guide](../DEPLOYMENT_OPTIONS_GUIDE.md) for more information.