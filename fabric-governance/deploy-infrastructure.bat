@echo off
REM ============================================================================
REM Fabric Tenant Governance - Infrastructure Deployment Script
REM ============================================================================
REM This script deploys the Azure infrastructure required for Fabric tenant
REM governance and preview feature management using Bicep templates.
REM ============================================================================

echo ============================================
echo Fabric Tenant Governance Deployment
echo ============================================
echo.

REM Check if Azure CLI is installed
where az >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Azure CLI is not installed or not in PATH
    echo Please install from: https://aka.ms/installazurecliwindows
    exit /b 1
)

REM Get deployment parameters
set /p RESOURCE_GROUP="Enter resource group name (e.g., fabric-governance-rg): "
set /p LOCATION="Enter Azure region (e.g., eastus): "
set /p WORKSPACE_NAME="Enter Log Analytics workspace name (e.g., fabric-governance-la): "
set /p ENVIRONMENT="Enter environment tag (production/test): "
set /p ALERT_EMAILS="Enter alert email addresses (comma-separated, optional): "

echo.
echo Deployment Configuration:
echo   Resource Group: %RESOURCE_GROUP%
echo   Location: %LOCATION%
echo   Workspace Name: %WORKSPACE_NAME%
echo   Environment: %ENVIRONMENT%
echo   Alert Emails: %ALERT_EMAILS%
echo.

set /p CONFIRM="Continue with deployment? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo Deployment cancelled.
    exit /b 0
)

echo.
echo [1/4] Logging in to Azure...
call az login
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Azure login failed
    exit /b 1
)

echo.
echo [2/4] Creating resource group...
call az group create --name %RESOURCE_GROUP% --location %LOCATION%
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create resource group
    exit /b 1
)

echo.
echo [3/4] Deploying infrastructure with Bicep...
cd /d "%~dp0bicep"

if "%ALERT_EMAILS%"=="" (
    call az deployment group create ^
        --resource-group %RESOURCE_GROUP% ^
        --template-file tenant-monitoring.bicep ^
        --parameters location=%LOCATION% ^
        --parameters workspaceName=%WORKSPACE_NAME% ^
        --parameters environmentTag=%ENVIRONMENT% ^
        --name fabric-governance-deployment
) else (
    call az deployment group create ^
        --resource-group %RESOURCE_GROUP% ^
        --template-file tenant-monitoring.bicep ^
        --parameters location=%LOCATION% ^
        --parameters workspaceName=%WORKSPACE_NAME% ^
        --parameters environmentTag=%ENVIRONMENT% ^
        --parameters alertEmailAddresses="%ALERT_EMAILS%" ^
        --name fabric-governance-deployment
)

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Deployment failed
    exit /b 1
)

echo.
echo [4/4] Retrieving deployment outputs...
for /f "delims=" %%i in ('az deployment group show --resource-group %RESOURCE_GROUP% --name fabric-governance-deployment --query "properties.outputs.dceEndpoint.value" -o tsv') do set DCE_ENDPOINT=%%i
for /f "delims=" %%i in ('az deployment group show --resource-group %RESOURCE_GROUP% --name fabric-governance-deployment --query "properties.outputs.dcrImmutableId.value" -o tsv') do set DCR_ID=%%i
for /f "delims=" %%i in ('az deployment group show --resource-group %RESOURCE_GROUP% --name fabric-governance-deployment --query "properties.outputs.workspaceId.value" -o tsv') do set WORKSPACE_ID=%%i

echo.
echo ============================================
echo Deployment Completed Successfully!
echo ============================================
echo.
echo IMPORTANT: Save these values for your .env file:
echo.
echo AZURE_MONITOR_DCE_ENDPOINT=%DCE_ENDPOINT%
echo AZURE_MONITOR_DCR_IMMUTABLE_ID=%DCR_ID%
echo LOG_ANALYTICS_WORKSPACE_ID=%WORKSPACE_ID%
echo AZURE_RESOURCE_GROUP=%RESOURCE_GROUP%
echo LOG_ANALYTICS_WORKSPACE_NAME=%WORKSPACE_NAME%
echo.
echo Next Steps:
echo 1. Update your .env file with the values above
echo 2. Run the tenant settings monitor notebook
echo 3. Configure PowerShell scripts for scheduled monitoring
echo.
echo Documentation: README.md
echo ============================================

cd /d "%~dp0"
pause
