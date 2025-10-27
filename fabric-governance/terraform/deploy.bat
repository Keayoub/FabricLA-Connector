@echo off
REM ============================================================================
REM Fabric Tenant Governance - Terraform Deployment Script
REM Windows Batch Script
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo Fabric Tenant Governance Infrastructure Deployment
echo ============================================================================
echo.

REM Check if Terraform is installed
where terraform >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Terraform is not installed or not in PATH
    echo Download from: https://www.terraform.io/downloads
    pause
    exit /b 1
)

echo [OK] Terraform found: 
terraform version | findstr "Terraform"
echo.

REM Check if Azure CLI is installed
where az >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Azure CLI is not installed or not in PATH
    echo Download from: https://aka.ms/installazurecliwindows
    pause
    exit /b 1
)

echo [OK] Azure CLI found
echo.

REM Check Azure authentication
echo Checking Azure authentication...
az account show >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] Not authenticated to Azure. Starting login...
    az login
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Azure login failed
        pause
        exit /b 1
    )
) else (
    echo [OK] Already authenticated to Azure
    az account show --query "{Subscription:name, TenantId:tenantId}" -o table
)
echo.

REM Check if terraform.tfvars exists
if not exist terraform.tfvars (
    echo [INFO] terraform.tfvars not found. Creating from example...
    if exist terraform.tfvars.example (
        copy terraform.tfvars.example terraform.tfvars >nul
        echo [OK] Created terraform.tfvars from example
        echo.
        echo ============================================================================
        echo IMPORTANT: Please edit terraform.tfvars with your configuration
        echo ============================================================================
        echo.
        echo Required settings:
        echo   - resource_group_name
        echo   - location
        echo   - workspace_name
        echo   - alert_email_addresses
        echo.
        echo Press any key to open terraform.tfvars in notepad...
        pause >nul
        notepad terraform.tfvars
        echo.
        echo After saving your changes, press any key to continue...
        pause >nul
    ) else (
        echo [ERROR] terraform.tfvars.example not found
        pause
        exit /b 1
    )
)

echo ============================================================================
echo Step 1: Terraform Initialization
echo ============================================================================
echo.

terraform init
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Terraform init failed
    pause
    exit /b 1
)

echo.
echo [OK] Terraform initialized successfully
echo.

echo ============================================================================
echo Step 2: Terraform Plan
echo ============================================================================
echo.
echo Generating deployment plan...
echo.

terraform plan -out=tfplan
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Terraform plan failed
    pause
    exit /b 1
)

echo.
echo [OK] Plan generated successfully
echo.

echo ============================================================================
echo Step 3: Review and Confirm
echo ============================================================================
echo.
echo Please review the plan above.
echo.
set /p CONFIRM="Do you want to proceed with deployment? (yes/no): "

if /i not "!CONFIRM!"=="yes" (
    echo.
    echo [INFO] Deployment cancelled by user
    echo.
    pause
    exit /b 0
)

echo.
echo ============================================================================
echo Step 4: Terraform Apply
echo ============================================================================
echo.
echo Deploying infrastructure...
echo This may take 3-5 minutes...
echo.

terraform apply tfplan
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Terraform apply failed
    echo.
    echo Troubleshooting tips:
    echo 1. Check Azure Portal for deployment errors
    echo 2. Verify your Azure subscription has sufficient permissions
    echo 3. Check terraform.tfvars for correct values
    echo 4. Review error messages above
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo Deployment Successful!
echo ============================================================================
echo.

REM Capture outputs
echo Capturing outputs...
echo.

terraform output -json > outputs.json

echo Deployment Summary:
echo -------------------
terraform output deployment_summary
echo.

echo Important Values (save these to .env file):
echo ------------------------------------------
echo.

for /f "delims=" %%i in ('terraform output -raw dce_endpoint 2^>nul') do set DCE_ENDPOINT=%%i
for /f "delims=" %%i in ('terraform output -raw dcr_immutable_id 2^>nul') do set DCR_ID=%%i
for /f "delims=" %%i in ('terraform output -raw workspace_customer_id 2^>nul') do set WORKSPACE_ID=%%i
for /f "delims=" %%i in ('terraform output -raw workspace_name 2^>nul') do set WORKSPACE_NAME=%%i

echo AZURE_MONITOR_DCE_ENDPOINT=!DCE_ENDPOINT!
echo AZURE_MONITOR_DCR_IMMUTABLE_ID=!DCR_ID!
echo LOG_ANALYTICS_WORKSPACE_ID=!WORKSPACE_ID!
echo LOG_ANALYTICS_WORKSPACE_NAME=!WORKSPACE_NAME!

echo.
echo Saving outputs to env-outputs.txt...
(
    echo # Fabric Governance Infrastructure Outputs
    echo # Copy these values to your .env file
    echo.
    echo AZURE_MONITOR_DCE_ENDPOINT=!DCE_ENDPOINT!
    echo AZURE_MONITOR_DCR_IMMUTABLE_ID=!DCR_ID!
    echo LOG_ANALYTICS_WORKSPACE_ID=!WORKSPACE_ID!
    echo LOG_ANALYTICS_WORKSPACE_NAME=!WORKSPACE_NAME!
) > env-outputs.txt

echo [OK] Outputs saved to env-outputs.txt
echo.

echo ============================================================================
echo Next Steps:
echo ============================================================================
echo.
echo 1. Copy values from env-outputs.txt to ..\.env file
echo 2. Test data ingestion:
echo    python ..\scripts\automated_governance_pipeline.py --mode monitor
echo.
echo 3. Verify in Log Analytics workspace: !WORKSPACE_NAME!
echo    Query: FabricTenantSettings_CL ^| take 10
echo.
echo 4. Set up scheduled monitoring (optional):
echo    - Windows Task Scheduler
echo    - Azure Automation
echo.
echo ============================================================================
echo.

REM Ask if user wants to open .env file
set /p OPEN_ENV="Do you want to update the .env file now? (yes/no): "
if /i "!OPEN_ENV!"=="yes" (
    if exist ..\.env (
        echo Opening .env file...
        notepad ..\.env
    ) else (
        echo Creating .env from example...
        if exist ..\.env.example (
            copy ..\.env.example ..\.env >nul
            notepad ..\.env
        ) else (
            echo [WARNING] .env.example not found in parent directory
        )
    )
)

echo.
echo Deployment complete!
echo.
pause
