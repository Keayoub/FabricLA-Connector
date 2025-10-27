<#
.SYNOPSIS
    Disable preview features in Microsoft Fabric tenant.

.DESCRIPTION
    This script disables preview features in a Fabric tenant to ensure production
    stability. It can be used before promoting artifacts from TEST to PROD, or as
    part of governance enforcement.

.PARAMETER TenantId
    Azure AD Tenant ID. If not provided, uses the current logged-in tenant.

.PARAMETER Environment
    Target environment name (for logging purposes). Default is "Production".

.PARAMETER ExcludeApprovedPreviews
    Path to JSON file containing approved preview features that should NOT be disabled.

.PARAMETER DryRun
    If specified, shows what would be disabled without making actual changes.

.PARAMETER Force
    Skip confirmation prompt and disable immediately.

.EXAMPLE
    .\Disable-PreviewFeatures.ps1 -DryRun

.EXAMPLE
    .\Disable-PreviewFeatures.ps1 -ExcludeApprovedPreviews ".\config\approved-previews.json" -Force

.NOTES
    Author: Fabric Governance Team
    Requires: Fabric Administrator role
    Dependencies: Azure CLI (az)
    WARNING: This script modifies tenant settings. Use with caution!
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$TenantId = $null,

    [Parameter(Mandatory = $false)]
    [string]$Environment = "Production",

    [Parameter(Mandatory = $false)]
    [string]$ExcludeApprovedPreviews = $null,

    [Parameter(Mandatory = $false)]
    [switch]$DryRun,

    [Parameter(Mandatory = $false)]
    [switch]$Force
)

# Check if Azure CLI is installed
try {
    az version 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Azure CLI not found"
    }
    Write-Verbose "Azure CLI is installed"
} catch {
    Write-Error "Azure CLI is not installed. Install it from: https://aka.ms/installazurecliwindows"
    exit 1
}

# Function to get access token using Azure CLI
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

        $token = az account get-access-token --resource "https://api.fabric.microsoft.com" --query "accessToken" -o tsv
        return $token
    } catch {
        Write-Error "Failed to get access token: $_"
        throw
    }
}

# Function to get tenant settings
function Get-TenantSettings {
    param([string]$AccessToken)

    $uri = "https://api.fabric.microsoft.com/v1/admin/tenantsettings"
    $headers = @{
        "Authorization" = "Bearer $AccessToken"
        "Content-Type"  = "application/json"
    }

    try {
        $response = Invoke-RestMethod -Uri $uri -Method Get -Headers $headers -ErrorAction Stop
        return $response
    } catch {
        Write-Error "Failed to retrieve tenant settings: $_"
        throw
    }
}

# Function to identify preview features
function Get-PreviewFeatures {
    param([object]$TenantSettings)

    $previewKeywords = @(
        "preview", "experimental", "beta", "early access", "public preview", "private preview"
    )

    $previewFeatures = @()
    
    foreach ($setting in $TenantSettings.tenantSettings) {
        $titleLower = $setting.title.ToLower()
        $isPreview = $false

        foreach ($keyword in $previewKeywords) {
            if ($titleLower -like "*$keyword*") {
                $isPreview = $true
                break
            }
        }

        if ($isPreview) {
            $previewFeatures += [PSCustomObject]@{
                SettingName = $setting.settingName
                Title = $setting.title
                Enabled = $setting.enabled
                TenantSettingGroup = $setting.tenantSettingGroup
            }
        }
    }

    return $previewFeatures
}

# Function to load approved previews
function Get-ApprovedPreviews {
    param([string]$FilePath)

    if ([string]::IsNullOrEmpty($FilePath) -or -not (Test-Path $FilePath)) {
        return @()
    }

    try {
        $content = Get-Content -Path $FilePath -Raw | ConvertFrom-Json
        return $content.approvedPreviewFeatures
    } catch {
        Write-Warning "Failed to load approved previews from $FilePath"
        return @()
    }
}

# Function to disable a preview feature (MOCK - needs actual API implementation)
function Disable-PreviewFeature {
    param(
        [string]$AccessToken,
        [string]$SettingName,
        [bool]$DryRun
    )

    if ($DryRun) {
        Write-Verbose "DRY RUN: Would disable $SettingName"
        return $true
    }

    # NOTE: This is a placeholder. The actual Fabric API for updating tenant settings
    # may require different parameters and endpoint structure.
    # Consult the official Fabric Admin API documentation for the correct implementation.
    
    Write-Warning "Actual tenant setting update API not implemented in this script."
    Write-Warning "You need to use the Fabric Admin Portal or wait for official PowerShell module."
    
    return $false
}

# Main execution
try {
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Fabric Preview Features Disabler" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""

    if ($DryRun) {
        Write-Host "*** DRY RUN MODE - No changes will be made ***" -ForegroundColor Yellow
        Write-Host ""
    }

    # Step 1: Authenticate
    Write-Host "[1/5] Authenticating to Azure and Fabric..." -ForegroundColor Yellow
    $accessToken = Get-FabricAccessToken -TenantId $TenantId

    # Step 2: Get tenant settings
    Write-Host "[2/5] Retrieving tenant settings..." -ForegroundColor Yellow
    $tenantSettings = Get-TenantSettings -AccessToken $accessToken

    # Step 3: Identify preview features
    Write-Host "[3/5] Identifying preview features..." -ForegroundColor Yellow
    $previewFeatures = Get-PreviewFeatures -TenantSettings $tenantSettings
    
    Write-Host "  Total preview features found: $($previewFeatures.Count)" -ForegroundColor Gray
    $enabledPreviews = $previewFeatures | Where-Object { $_.Enabled -eq $true }
    Write-Host "  Currently enabled: $($enabledPreviews.Count)" -ForegroundColor Gray

    # Step 4: Filter out approved previews
    Write-Host "[4/5] Checking approved previews list..." -ForegroundColor Yellow
    $approvedPreviews = Get-ApprovedPreviews -FilePath $ExcludeApprovedPreviews
    
    $toDisable = $enabledPreviews | Where-Object {
        $settingName = $_.SettingName
        $settingName -notin $approvedPreviews
    }

    Write-Host "  Approved previews (will be kept): $($approvedPreviews.Count)" -ForegroundColor Gray
    Write-Host "  Preview features to disable: $($toDisable.Count)" -ForegroundColor Gray

    if ($toDisable.Count -eq 0) {
        Write-Host ""
        Write-Host "No preview features need to be disabled." -ForegroundColor Green
        exit 0
    }

    # Display list of features to disable
    Write-Host ""
    Write-Host "Preview features to be disabled:" -ForegroundColor Yellow
    $toDisable | ForEach-Object {
        Write-Host "  - $($_.Title)" -ForegroundColor White
        Write-Host "    ($($_.SettingName))" -ForegroundColor Gray
    }

    # Confirm before proceeding
    if (-not $Force -and -not $DryRun) {
        Write-Host ""
        $confirmation = Read-Host "Do you want to proceed with disabling these preview features? (Y/N)"
        if ($confirmation -ne 'Y' -and $confirmation -ne 'y') {
            Write-Host "Operation cancelled by user." -ForegroundColor Yellow
            exit 0
        }
    }

    # Step 5: Disable preview features
    Write-Host ""
    Write-Host "[5/5] Disabling preview features..." -ForegroundColor Yellow
    
    $successCount = 0
    $failureCount = 0

    foreach ($feature in $toDisable) {
        try {
            $result = Disable-PreviewFeature -AccessToken $accessToken -SettingName $feature.SettingName -DryRun $DryRun
            
            if ($result) {
                if ($DryRun) {
                    Write-Host "  [DRY RUN] Would disable: $($feature.Title)" -ForegroundColor Cyan
                } else {
                    Write-Host "  ✓ Disabled: $($feature.Title)" -ForegroundColor Green
                }
                $successCount++
            } else {
                Write-Host "  ✗ Failed: $($feature.Title)" -ForegroundColor Red
                $failureCount++
            }
        } catch {
            Write-Host "  ✗ Error disabling $($feature.Title): $_" -ForegroundColor Red
            $failureCount++
        }
    }

    # Summary
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "Operation Completed" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "  Successful: $successCount" -ForegroundColor White
    Write-Host "  Failed: $failureCount" -ForegroundColor White
    
    if ($DryRun) {
        Write-Host ""
        Write-Host "This was a DRY RUN. No changes were made." -ForegroundColor Yellow
        Write-Host "Run without -DryRun to apply changes." -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "IMPORTANT NOTES:" -ForegroundColor Yellow
    Write-Host "- This script currently shows what WOULD be disabled" -ForegroundColor Yellow
    Write-Host "- Actual Fabric tenant settings update API requires:" -ForegroundColor Yellow
    Write-Host "  1. Official Fabric Admin REST API endpoint" -ForegroundColor Yellow
    Write-Host "  2. Proper request payload structure" -ForegroundColor Yellow
    Write-Host "  3. Microsoft may not yet expose this via public API" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "For now, use the Fabric Admin Portal to disable preview features manually." -ForegroundColor Cyan

} catch {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Red
    Write-Host "Operation Failed!" -ForegroundColor Red
    Write-Host "==========================================" -ForegroundColor Red
    Write-Error $_.Exception.Message
    exit 1
}
