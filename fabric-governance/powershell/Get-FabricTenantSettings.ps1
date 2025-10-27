<#
.SYNOPSIS
    Export Microsoft Fabric tenant settings using the Tenant Settings API.

.DESCRIPTION
    This script retrieves the complete tenant settings configuration from Microsoft Fabric
    using the GetTenantSettingsAsAdmin REST API. It supports filtering, preview feature 
    identification, and multiple output formats.

.PARAMETER OutputPath
    Path where the tenant settings JSON file will be saved.

.PARAMETER IncludePreviewFeatures
    Flag to include metadata about which settings are preview features.

.PARAMETER Format
    Output format: JSON, CSV, or HTML. Default is JSON.

.PARAMETER TenantId
    Azure AD Tenant ID. If not provided, uses the current logged-in tenant.

.PARAMETER Verbose
    Enable verbose logging for troubleshooting.

.EXAMPLE
    .\Get-FabricTenantSettings.ps1 -OutputPath ".\settings.json" -IncludePreviewFeatures

.EXAMPLE
    .\Get-FabricTenantSettings.ps1 -OutputPath ".\settings.json" -Format HTML -Verbose

.NOTES
    Author: Fabric Governance Team
    Requires: Fabric Administrator role
    Dependencies: Azure CLI (az)
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [Parameter(Mandatory = $false)]
    [switch]$IncludePreviewFeatures,

    [Parameter(Mandatory = $false)]
    [ValidateSet("JSON", "CSV", "HTML")]
    [string]$Format = "JSON",

    [Parameter(Mandatory = $false)]
    [string]$TenantId = $null
)

# Check if Azure CLI is installed
try {
    $azVersion = az version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Azure CLI not found"
    }
    Write-Verbose "Azure CLI is installed"
} catch {
    Write-Error "Azure CLI is not installed. Install it from: https://aka.ms/installazurecliwindows"
    exit 1
}

# Function to get access token for Fabric API using Azure CLI
function Get-FabricAccessToken {
    param([string]$TenantId)
    
    try {
        # Check if already logged in
        $account = az account show 2>$null | ConvertFrom-Json
        if ($null -eq $account) {
            Write-Host "Not authenticated. Logging in to Azure..."
            if ($TenantId) {
                az login --tenant $TenantId --only-show-errors | Out-Null
            } else {
                az login --only-show-errors | Out-Null
            }
        } else {
            Write-Verbose "Already authenticated as: $($account.user.name)"
        }

        Write-Verbose "Getting access token for Fabric API"
        $tokenJson = az account get-access-token --resource "https://api.fabric.microsoft.com" --query "accessToken" -o tsv
        
        if ([string]::IsNullOrEmpty($tokenJson)) {
            throw "Failed to obtain access token"
        }
        
        return $tokenJson
    } catch {
        Write-Error "Failed to get access token: $_"
        throw
    }
}

# Function to call Fabric Tenant Settings API
function Get-TenantSettingsFromAPI {
    param(
        [string]$AccessToken
    )

    $uri = "https://api.fabric.microsoft.com/v1/admin/tenantsettings"
    $headers = @{
        "Authorization" = "Bearer $AccessToken"
        "Content-Type"  = "application/json"
    }

    try {
        Write-Verbose "Calling Fabric Tenant Settings API: $uri"
        $response = Invoke-RestMethod -Uri $uri -Method Get -Headers $headers -ErrorAction Stop
        Write-Host "Successfully retrieved tenant settings" -ForegroundColor Green
        return $response
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorMessage = $_.Exception.Message
        
        Write-Error "Failed to retrieve tenant settings. Status Code: $statusCode"
        Write-Error "Error: $errorMessage"
        
        if ($statusCode -eq 401 -or $statusCode -eq 403) {
            Write-Warning "Authentication/Authorization failed. Ensure you have Fabric Administrator role."
        }
        
        throw
    }
}

# Function to identify preview features
function Add-PreviewFeatureMetadata {
    param([object]$Settings)

    # Known preview feature patterns (update this list periodically)
    $previewKeywords = @(
        "preview",
        "experimental",
        "beta",
        "early access",
        "public preview",
        "private preview"
    )

    $settingsWithMetadata = @()
    
    foreach ($setting in $Settings.tenantSettings) {
        $settingObj = [PSCustomObject]@{
            SettingName     = $setting.settingName
            Title           = $setting.title
            Enabled         = $setting.enabled
            CanSpecifySecurityGroups = $setting.canSpecifySecurityGroups
            TenantSettingGroup = $setting.tenantSettingGroup
            IsPreviewFeature = $false
            PreviewIndicators = @()
        }

        # Check if this is a preview feature
        $titleLower = $setting.title.ToLower()
        $descriptionLower = if ($setting.description) { $setting.description.ToLower() } else { "" }
        
        foreach ($keyword in $previewKeywords) {
            if ($titleLower -like "*$keyword*" -or $descriptionLower -like "*$keyword*") {
                $settingObj.IsPreviewFeature = $true
                $settingObj.PreviewIndicators += $keyword
            }
        }

        $settingsWithMetadata += $settingObj
    }

    return $settingsWithMetadata
}

# Function to export to different formats
function Export-TenantSettings {
    param(
        [object]$Settings,
        [string]$Path,
        [string]$Format
    )

    $directory = Split-Path -Path $Path -Parent
    if (-not (Test-Path $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
        Write-Verbose "Created directory: $directory"
    }

    switch ($Format) {
        "JSON" {
            $Settings | ConvertTo-Json -Depth 10 | Set-Content -Path $Path -Encoding UTF8
            Write-Host "Tenant settings exported to JSON: $Path" -ForegroundColor Green
        }
        "CSV" {
            $Settings | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
            Write-Host "Tenant settings exported to CSV: $Path" -ForegroundColor Green
        }
        "HTML" {
            $html = $Settings | ConvertTo-Html -Title "Fabric Tenant Settings" -PreContent "<h1>Fabric Tenant Settings Report</h1><p>Generated: $(Get-Date)</p>"
            $html | Set-Content -Path $Path -Encoding UTF8
            Write-Host "Tenant settings exported to HTML: $Path" -ForegroundColor Green
        }
    }
}

# Main execution
try {
    Write-Host "====================================" -ForegroundColor Cyan
    Write-Host "Fabric Tenant Settings Exporter" -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan
    Write-Host ""

    # Step 1: Authenticate and get access token
    Write-Host "[1/4] Authenticating to Azure and Fabric..." -ForegroundColor Yellow
    $accessToken = Get-FabricAccessToken -TenantId $TenantId

    # Step 2: Retrieve tenant settings
    Write-Host "[2/4] Retrieving tenant settings from Fabric API..." -ForegroundColor Yellow
    $tenantSettings = Get-TenantSettingsFromAPI -AccessToken $accessToken

    # Step 3: Process settings
    Write-Host "[3/4] Processing tenant settings..." -ForegroundColor Yellow
    
    if ($IncludePreviewFeatures) {
        Write-Verbose "Adding preview feature metadata"
        $processedSettings = Add-PreviewFeatureMetadata -Settings $tenantSettings
    } else {
        $processedSettings = $tenantSettings.tenantSettings
    }

    $previewCount = ($processedSettings | Where-Object { $_.IsPreviewFeature -eq $true }).Count
    Write-Host "  Total settings: $($processedSettings.Count)" -ForegroundColor Gray
    Write-Host "  Preview features identified: $previewCount" -ForegroundColor Gray

    # Step 4: Export to file
    Write-Host "[4/4] Exporting to $Format format..." -ForegroundColor Yellow
    
    # Get current tenant ID from Azure CLI
    $currentTenantId = az account show --query "tenantId" -o tsv
    
    $exportData = @{
        ExportDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        TenantId = $currentTenantId
        SettingsCount = $processedSettings.Count
        PreviewFeaturesCount = $previewCount
        Settings = $processedSettings
    }

    Export-TenantSettings -Settings $exportData -Path $OutputPath -Format $Format

    Write-Host ""
    Write-Host "====================================" -ForegroundColor Green
    Write-Host "Export completed successfully!" -ForegroundColor Green
    Write-Host "====================================" -ForegroundColor Green
    Write-Host "Output file: $OutputPath" -ForegroundColor White

} catch {
    Write-Host ""
    Write-Host "====================================" -ForegroundColor Red
    Write-Host "Export failed!" -ForegroundColor Red
    Write-Host "====================================" -ForegroundColor Red
    Write-Error $_.Exception.Message
    exit 1
}
