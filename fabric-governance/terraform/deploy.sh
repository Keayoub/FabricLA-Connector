#!/bin/bash
# ============================================================================
# Fabric Tenant Governance - Terraform Deployment Script
# Bash Script (Linux/macOS)
# ============================================================================

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo ""
    echo "============================================================================"
    echo "$1"
    echo "============================================================================"
    echo ""
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Main deployment
print_header "Fabric Tenant Governance Infrastructure Deployment"

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed or not in PATH"
    echo "Download from: https://www.terraform.io/downloads"
    exit 1
fi

print_success "Terraform found: $(terraform version | head -n 1)"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed or not in PATH"
    echo "Download from: https://aka.ms/azure-cli"
    exit 1
fi

print_success "Azure CLI found"
echo ""

# Check Azure authentication
print_info "Checking Azure authentication..."
if ! az account show &> /dev/null; then
    print_info "Not authenticated to Azure. Starting login..."
    az login
    if [ $? -ne 0 ]; then
        print_error "Azure login failed"
        exit 1
    fi
else
    print_success "Already authenticated to Azure"
    az account show --query "{Subscription:name, TenantId:tenantId}" -o table
fi
echo ""

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    print_info "terraform.tfvars not found. Creating from example..."
    if [ -f "terraform.tfvars.example" ]; then
        cp terraform.tfvars.example terraform.tfvars
        print_success "Created terraform.tfvars from example"
        echo ""
        print_header "IMPORTANT: Please edit terraform.tfvars with your configuration"
        echo "Required settings:"
        echo "  - resource_group_name"
        echo "  - location"
        echo "  - workspace_name"
        echo "  - alert_email_addresses"
        echo ""
        echo "Opening terraform.tfvars in default editor..."
        ${EDITOR:-nano} terraform.tfvars
        echo ""
        read -p "Press Enter to continue after saving your changes..."
    else
        print_error "terraform.tfvars.example not found"
        exit 1
    fi
fi

# Step 1: Terraform Init
print_header "Step 1: Terraform Initialization"

terraform init
if [ $? -ne 0 ]; then
    print_error "Terraform init failed"
    exit 1
fi

print_success "Terraform initialized successfully"
echo ""

# Step 2: Terraform Plan
print_header "Step 2: Terraform Plan"
echo "Generating deployment plan..."
echo ""

terraform plan -out=tfplan
if [ $? -ne 0 ]; then
    print_error "Terraform plan failed"
    exit 1
fi

print_success "Plan generated successfully"
echo ""

# Step 3: Confirm deployment
print_header "Step 3: Review and Confirm"
echo "Please review the plan above."
echo ""
read -p "Do you want to proceed with deployment? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    print_info "Deployment cancelled by user"
    exit 0
fi

# Step 4: Terraform Apply
print_header "Step 4: Terraform Apply"
echo "Deploying infrastructure..."
echo "This may take 3-5 minutes..."
echo ""

terraform apply tfplan
if [ $? -ne 0 ]; then
    echo ""
    print_error "Terraform apply failed"
    echo ""
    echo "Troubleshooting tips:"
    echo "1. Check Azure Portal for deployment errors"
    echo "2. Verify your Azure subscription has sufficient permissions"
    echo "3. Check terraform.tfvars for correct values"
    echo "4. Review error messages above"
    echo ""
    exit 1
fi

echo ""
print_header "Deployment Successful!"

# Capture outputs
echo "Capturing outputs..."
echo ""

terraform output -json > outputs.json

echo "Deployment Summary:"
echo "-------------------"
terraform output deployment_summary
echo ""

echo "Important Values (save these to .env file):"
echo "------------------------------------------"
echo ""

DCE_ENDPOINT=$(terraform output -raw dce_endpoint 2>/dev/null)
DCR_ID=$(terraform output -raw dcr_immutable_id 2>/dev/null)
WORKSPACE_ID=$(terraform output -raw workspace_customer_id 2>/dev/null)
WORKSPACE_NAME=$(terraform output -raw workspace_name 2>/dev/null)

echo "AZURE_MONITOR_DCE_ENDPOINT=$DCE_ENDPOINT"
echo "AZURE_MONITOR_DCR_IMMUTABLE_ID=$DCR_ID"
echo "LOG_ANALYTICS_WORKSPACE_ID=$WORKSPACE_ID"
echo "LOG_ANALYTICS_WORKSPACE_NAME=$WORKSPACE_NAME"

echo ""
echo "Saving outputs to env-outputs.txt..."
cat > env-outputs.txt << EOF
# Fabric Governance Infrastructure Outputs
# Copy these values to your .env file

AZURE_MONITOR_DCE_ENDPOINT=$DCE_ENDPOINT
AZURE_MONITOR_DCR_IMMUTABLE_ID=$DCR_ID
LOG_ANALYTICS_WORKSPACE_ID=$WORKSPACE_ID
LOG_ANALYTICS_WORKSPACE_NAME=$WORKSPACE_NAME
EOF

print_success "Outputs saved to env-outputs.txt"
echo ""

# Next steps
print_header "Next Steps:"
echo ""
echo "1. Copy values from env-outputs.txt to ../.env file"
echo "2. Test data ingestion:"
echo "   python ../scripts/automated_governance_pipeline.py --mode monitor"
echo ""
echo "3. Verify in Log Analytics workspace: $WORKSPACE_NAME"
echo "   Query: FabricTenantSettings_CL | take 10"
echo ""
echo "4. Set up scheduled monitoring (optional):"
echo "   - Cron job (Linux/macOS)"
echo "   - Azure Automation"
echo ""
print_header "Deployment Complete!"

# Ask if user wants to update .env file
echo ""
read -p "Do you want to update the .env file now? (yes/no): " OPEN_ENV
if [ "$OPEN_ENV" == "yes" ]; then
    if [ -f "../.env" ]; then
        echo "Opening .env file..."
        ${EDITOR:-nano} ../.env
    else
        echo "Creating .env from example..."
        if [ -f "../.env.example" ]; then
            cp ../.env.example ../.env
            ${EDITOR:-nano} ../.env
        else
            print_warning ".env.example not found in parent directory"
        fi
    fi
fi

echo ""
print_success "Deployment complete!"
echo ""
