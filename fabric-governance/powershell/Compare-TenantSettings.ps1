<#
.SYNOPSIS
    Compare Microsoft Fabric tenant settings between two environments (TEST vs PROD).

.DESCRIPTION
    This script compares tenant settings exported from two different Fabric environments
    to identify configuration drift, highlight preview features, and generate comparison reports.

.PARAMETER TestSettingsPath
    Path to the TEST environment tenant settings JSON file.

.PARAMETER ProdSettingsPath
    Path to the PROD environment tenant settings JSON file.

.PARAMETER OutputReport
    Path where the comparison report will be saved (HTML format).

.PARAMETER HighlightPreviewFeatures
    Flag to specifically highlight preview features in the comparison.

.PARAMETER FailOnDrift
    Exit with error code if drift is detected (useful for CI/CD pipelines).

.EXAMPLE
    .\Compare-TenantSettings.ps1 -TestSettingsPath ".\test-settings.json" -ProdSettingsPath ".\prod-settings.json" -OutputReport ".\comparison.html"

.EXAMPLE
    .\Compare-TenantSettings.ps1 -TestSettingsPath ".\test.json" -ProdSettingsPath ".\prod.json" -HighlightPreviewFeatures -FailOnDrift

.NOTES
    Author: Fabric Governance Team
    Dependencies: Azure CLI (az) - optional, only for authentication context
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$TestSettingsPath,

    [Parameter(Mandatory = $true)]
    [string]$ProdSettingsPath,

    [Parameter(Mandatory = $false)]
    [string]$OutputReport = ".\tenant-comparison-report.html",

    [Parameter(Mandatory = $false)]
    [switch]$HighlightPreviewFeatures,

    [Parameter(Mandatory = $false)]
    [switch]$FailOnDrift
)

# Function to load tenant settings from JSON
function Import-TenantSettings {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        throw "Settings file not found: $Path"
    }

    try {
        $content = Get-Content -Path $Path -Raw | ConvertFrom-Json
        Write-Verbose "Loaded settings from: $Path"
        return $content
    } catch {
        throw "Failed to parse JSON from $Path: $_"
    }
}

# Function to compare settings
function Compare-Settings {
    param(
        [object]$TestSettings,
        [object]$ProdSettings
    )

    $differences = @()
    $testSettingsDict = @{}
    $prodSettingsDict = @{}

    # Build dictionaries for easier lookup
    foreach ($setting in $TestSettings.Settings) {
        $testSettingsDict[$setting.SettingName] = $setting
    }

    foreach ($setting in $ProdSettings.Settings) {
        $prodSettingsDict[$setting.SettingName] = $setting
    }

    # Compare each setting
    $allSettingNames = ($testSettingsDict.Keys + $prodSettingsDict.Keys) | Select-Object -Unique

    foreach ($settingName in $allSettingNames) {
        $testSetting = $testSettingsDict[$settingName]
        $prodSetting = $prodSettingsDict[$settingName]

        $difference = [PSCustomObject]@{
            SettingName = $settingName
            ExistsInTest = ($null -ne $testSetting)
            ExistsInProd = ($null -ne $prodSetting)
            TestEnabled = if ($testSetting) { $testSetting.Enabled } else { $null }
            ProdEnabled = if ($prodSetting) { $prodSetting.Enabled } else { $null }
            IsDifferent = $false
            IsPreviewFeature = $false
            DifferenceType = ""
            Title = ""
            RiskLevel = "Low"
        }

        # Determine if there's a difference
        if ($null -eq $testSetting) {
            $difference.IsDifferent = $true
            $difference.DifferenceType = "Missing in TEST"
            $difference.Title = $prodSetting.Title
            $difference.RiskLevel = "Medium"
        } elseif ($null -eq $prodSetting) {
            $difference.IsDifferent = $true
            $difference.DifferenceType = "Missing in PROD"
            $difference.Title = $testSetting.Title
            $difference.RiskLevel = "Medium"
        } else {
            $difference.Title = $testSetting.Title
            
            if ($testSetting.Enabled -ne $prodSetting.Enabled) {
                $difference.IsDifferent = $true
                $difference.DifferenceType = "Enabled state differs"
                
                # Check if it's a preview feature
                if ($testSetting.IsPreviewFeature -eq $true) {
                    $difference.IsPreviewFeature = $true
                    $difference.RiskLevel = "High"
                } else {
                    $difference.RiskLevel = "Medium"
                }
            }
        }

        if ($difference.IsDifferent) {
            $differences += $difference
        }
    }

    return $differences
}

# Function to generate HTML report
function New-ComparisonReport {
    param(
        [object[]]$Differences,
        [string]$OutputPath,
        [bool]$HighlightPreviews
    )

    $highRisk = ($Differences | Where-Object { $_.RiskLevel -eq "High" }).Count
    $mediumRisk = ($Differences | Where-Object { $_.RiskLevel -eq "Medium" }).Count
    $lowRisk = ($Differences | Where-Object { $_.RiskLevel -eq "Low" }).Count
    $previewDiffs = ($Differences | Where-Object { $_.IsPreviewFeature -eq $true }).Count

    $html = @"
<!DOCTYPE html>
<html>
<head>
    <title>Fabric Tenant Settings Comparison Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background-color: #0078d4;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .summary {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .summary-card {
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }
        .high-risk { background-color: #ffebee; border-left: 4px solid #d32f2f; }
        .medium-risk { background-color: #fff3e0; border-left: 4px solid #f57c00; }
        .low-risk { background-color: #e8f5e9; border-left: 4px solid #388e3c; }
        .preview-feature { background-color: #e3f2fd; border-left: 4px solid #1976d2; }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        th {
            background-color: #0078d4;
            color: white;
            padding: 12px;
            text-align: left;
        }
        td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .badge {
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        }
        .badge-high { background-color: #d32f2f; color: white; }
        .badge-medium { background-color: #f57c00; color: white; }
        .badge-low { background-color: #388e3c; color: white; }
        .badge-preview { background-color: #1976d2; color: white; }
        .enabled { color: #388e3c; font-weight: bold; }
        .disabled { color: #d32f2f; font-weight: bold; }
        .footer {
            margin-top: 20px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Fabric Tenant Settings Comparison Report</h1>
        <p>Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")</p>
    </div>

    <div class="summary">
        <h2>Summary</h2>
        <div class="summary-grid">
            <div class="summary-card high-risk">
                <h3>$highRisk</h3>
                <p>High Risk Differences</p>
            </div>
            <div class="summary-card medium-risk">
                <h3>$mediumRisk</h3>
                <p>Medium Risk Differences</p>
            </div>
            <div class="summary-card low-risk">
                <h3>$lowRisk</h3>
                <p>Low Risk Differences</p>
            </div>
            <div class="summary-card preview-feature">
                <h3>$previewDiffs</h3>
                <p>Preview Feature Differences</p>
            </div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Setting Name</th>
                <th>Title</th>
                <th>TEST Status</th>
                <th>PROD Status</th>
                <th>Difference Type</th>
                <th>Risk Level</th>
                <th>Preview Feature</th>
            </tr>
        </thead>
        <tbody>
"@

    foreach ($diff in $Differences) {
        $testStatus = if ($diff.ExistsInTest) {
            if ($diff.TestEnabled) { "<span class='enabled'>Enabled</span>" } else { "<span class='disabled'>Disabled</span>" }
        } else { "N/A" }

        $prodStatus = if ($diff.ExistsInProd) {
            if ($diff.ProdEnabled) { "<span class='enabled'>Enabled</span>" } else { "<span class='disabled'>Disabled</span>" }
        } else { "N/A" }

        $riskBadge = switch ($diff.RiskLevel) {
            "High" { "<span class='badge badge-high'>HIGH</span>" }
            "Medium" { "<span class='badge badge-medium'>MEDIUM</span>" }
            "Low" { "<span class='badge badge-low'>LOW</span>" }
        }

        $previewBadge = if ($diff.IsPreviewFeature) {
            "<span class='badge badge-preview'>PREVIEW</span>"
        } else { "" }

        $html += @"
            <tr>
                <td>$($diff.SettingName)</td>
                <td>$($diff.Title)</td>
                <td>$testStatus</td>
                <td>$prodStatus</td>
                <td>$($diff.DifferenceType)</td>
                <td>$riskBadge</td>
                <td>$previewBadge</td>
            </tr>
"@
    }

    $html += @"
        </tbody>
    </table>

    <div class="footer">
        <p>Fabric Tenant Governance & Preview Feature Management</p>
    </div>
</body>
</html>
"@

    $html | Set-Content -Path $OutputPath -Encoding UTF8
    Write-Host "Comparison report generated: $OutputPath" -ForegroundColor Green
}

# Main execution
try {
    Write-Host "====================================" -ForegroundColor Cyan
    Write-Host "Fabric Tenant Settings Comparator" -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan
    Write-Host ""

    # Step 1: Load settings files
    Write-Host "[1/3] Loading tenant settings files..." -ForegroundColor Yellow
    $testSettings = Import-TenantSettings -Path $TestSettingsPath
    $prodSettings = Import-TenantSettings -Path $ProdSettingsPath

    Write-Host "  TEST settings: $($testSettings.SettingsCount) settings" -ForegroundColor Gray
    Write-Host "  PROD settings: $($prodSettings.SettingsCount) settings" -ForegroundColor Gray

    # Step 2: Compare settings
    Write-Host "[2/3] Comparing tenant settings..." -ForegroundColor Yellow
    $differences = Compare-Settings -TestSettings $testSettings -ProdSettings $prodSettings

    $totalDiffs = $differences.Count
    $previewDiffs = ($differences | Where-Object { $_.IsPreviewFeature -eq $true }).Count
    $highRisk = ($differences | Where-Object { $_.RiskLevel -eq "High" }).Count

    Write-Host "  Total differences found: $totalDiffs" -ForegroundColor Gray
    Write-Host "  Preview feature differences: $previewDiffs" -ForegroundColor Gray
    Write-Host "  High risk differences: $highRisk" -ForegroundColor $(if ($highRisk -gt 0) { "Red" } else { "Gray" })

    # Step 3: Generate report
    Write-Host "[3/3] Generating comparison report..." -ForegroundColor Yellow
    New-ComparisonReport -Differences $differences -OutputPath $OutputReport -HighlightPreviews $HighlightPreviewFeatures

    Write-Host ""
    Write-Host "====================================" -ForegroundColor Green
    Write-Host "Comparison completed successfully!" -ForegroundColor Green
    Write-Host "====================================" -ForegroundColor Green
    Write-Host "Report location: $OutputReport" -ForegroundColor White

    # Display preview feature warnings
    if ($HighlightPreviewFeatures -and $previewDiffs -gt 0) {
        Write-Host ""
        Write-Warning "Preview features with differences detected:"
        $differences | Where-Object { $_.IsPreviewFeature -eq $true } | ForEach-Object {
            Write-Host "  - $($_.Title) ($($_.SettingName))" -ForegroundColor Yellow
        }
    }

    # Fail on drift if requested
    if ($FailOnDrift -and $totalDiffs -gt 0) {
        Write-Host ""
        Write-Error "Configuration drift detected between TEST and PROD environments!"
        exit 1
    }

} catch {
    Write-Host ""
    Write-Host "====================================" -ForegroundColor Red
    Write-Host "Comparison failed!" -ForegroundColor Red
    Write-Host "====================================" -ForegroundColor Red
    Write-Error $_.Exception.Message
    exit 1
}
