<#
.SYNOPSIS
    Updates an AWS S3 website with the specified parameters using the s3-uploader.ps1 script.

.DESCRIPTION
    This script updates a website identified by the specified WebsiteName with the
    parameters obtained from the Get-Params.ps1 script. It provides the option to force
    the update using the -Force switch.

.PARAMETER WebsiteName
    Specifies the name of the website to be updated. Valid values are 'pccommander.net'
    and 'lazyspaniard.com'. Default value is 'PcCommander.net'.

.PARAMETER Force
    Switch parameter that forces the update, bypassing any confirmation prompts.

.EXAMPLE
    PS C:\> .\Update-S3Website.ps1 -WebsiteName 'lazyspaniard.com' -Force
    Updates the 'lazyspaniard.com' website with the specified parameters without prompting for confirmation.

.NOTES
    File: Update-S3Website.ps1
    Author: Diego Reategui
    Date: 2023-12-26

#>
[CmdletBinding(SupportsShouldProcess)]
param (
    [ValidateSet('pccommander.net', 'lazyspaniard.com')]
    [string] $WebsiteName = 'PcCommander.net',
    [switch] $Force
)
$n = 10
Write-Host "$(' '*$n) Updating website $WebsiteName $(' '*$n)" -backgroundcolor Green -foregroundcolor Black
$params = & (Join-Path $PSScriptRoot .\Get-Params.ps1) -BucketName $WebsiteName
$params['Force'] = $Force
if ($WhatIfPreference) {
    $params['WhatIf'] = $true
    Write-Host "What if: Would update S3 bucket for website '$WebsiteName'" -ForegroundColor Cyan
}
Write-Verbose "Params: $($params.GetEnumerator())"
& (Join-Path $PSScriptRoot .\s3-uploader.ps1) @params
