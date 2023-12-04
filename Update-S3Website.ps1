[CmdletBinding()]
param (
    [ValidateSet('pccommander.net', 'lazyspaniard.com')]
    [string] $WebsiteName = 'PcCommander.net',
    [switch] $Force
)
$n = 10
Write-Host "$(' '*$n) Updating website $WebsiteName $(' '*$n)" -backgroundcolor Green -foregroundcolor Black
$params = & (Join-Path $PSScriptRoot .\Get-Params.ps1) -BucketName $WebsiteName
$params['Force'] = $Force
Write-Verbose "Params: $($params.GetEnumerator())"
& (Join-Path $PSScriptRoot .\s3-uploader.ps1) @params
