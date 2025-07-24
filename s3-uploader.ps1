<#
.SYNOPSIS
Uploads an HTML project to an S3 bucket.

.DESCRIPTION
This script uploads an HTML project to an S3 bucket using the AWS CLI and Python. The script supports uploading individual files or syncing all updated files in the project.

.PARAMETER BucketName
The name of the S3 bucket to upload the project to.

.PARAMETER ProjectRoot
The root directory of the HTML project to upload. The default value is the current directory.

.PARAMETER SyncJustChanges
A switch parameter that specifies to sync only the updated files in the project. When this parameter is specified, the script will sync only the files that have been modified since the last execution of this script with this parameter.

.PARAMETER Path
An array of file paths to upload. This parameter is mandatory when the SyncJustChanges parameter is not specified. The specified files will be uploaded to the S3 bucket.

.PARAMETER Force
A switch parameter that specifies to confirm the upload operation without prompting for confirmation.

.EXAMPLE
.\upload-html-to-s3.ps1 -BucketName "my-bucket" -ProjectRoot "C:\my-html-project" -SyncJustChanges
Uploads the updated files in the HTML project located at 'C:\my-html-project' to the 'my-bucket' S3 bucket.

.EXAMPLE
.\upload-html-to-s3.ps1 -BucketName "my-bucket" -Path "C:\my-html-project\index.html", "C:\my-html-project\styles.css"
Uploads the 'index.html' and 'styles.css' files in the 'my-html-project' directory to the 'my-bucket' S3 bucket.

.EXAMPLE
.\upload-html-to-s3.ps1 -BucketName "my-bucket" -ProjectRoot "C:\my-html-project" -Force
Uploads the entire HTML project located at 'C:\my-html-project' to the 'my-bucket' S3 bucket without prompting for confirmation.

#>
[CmdletBinding(DefaultParameterSetName='SyncChanges', SupportsShouldProcess)]
param (    
    [ValidateNotNullOrEmpty()]
    [Parameter(Mandatory=$true, HelpMessage='Name of the S3 bucket to upload to')]
    [string] 
    $BucketName,# = 'diego-bucket-test',

    [ValidateScript({
        if (!(Test-Path $_) -or !(Get-Item $_).PSIsContainer) {
            throw "Path '$_' is not a valid directory path."
        }
        $true
    })]
    [string] 
    $ProjectRoot = (Get-Location).Path,

    [Parameter(ParameterSetName='SyncChanges')]
    [switch] 
    $SyncJustChanges,

    [Parameter(ParameterSetName='IndividualFiles', Mandatory=$true)]
    [ValidateScript({
        foreach ($path in $_) {
            if (!(Test-Path $path) -or (Get-Item $path).PSIsContainer) {
                throw "Path '$path' is not a valid file path."
            }
        }
        $true
    })]
    [string[]] 
    $Path,

    [string]
    $DistributionId,

    [switch] 
    $Force
)
function Test-InVirtualEnvironment {
    return ((Test-Path env:VIRTUAL_ENV) -and (Split-Path $env:VIRTUAL_ENV) -eq $PSScriptRoot)
}
function Activate-VirtualEnvironment ([switch]$ReturnPriorVenvState) {
    if (-not ($wasInVEnv = Test-InVirtualEnvironment)) {
        Write-Host "Not in virtual env. Activating..." -F DarkGray
        Push-Location $PSScriptRoot
        if (($prior = $VerbosePreference) -ne 'SilentlyContinue') {
            $VerbosePreference = 'SilentlyContinue'
        }
        .\.win-venv\Scripts\activate
        $VerbosePreference = $prior
        Pop-Location
        if (-not (Test-InVirtualEnvironment)) {
            Write-Host "Failed to activate virtual environment." -F Red
            exit 1
        }
    }
    else {
        Write-Verbose "Confirmed in virtual environment"
    }
    if ($ReturnPriorVenvState) {
        return $wasInVEnv
    }
}
if ($PSVersionTable.PSVersion.Major -lt 7) {
    $continue = Read-Host "Warning: This script requires PowerShell 7 or later. Do you want to continue? (Y/N)"
    if ($continue -notlike 'y*') {
        exit
    }
}
Write-Host

$wasInVEnv = Activate-VirtualEnvironment -ReturnPriorVenvState

$dbug = $DebugPreference -eq 'Continue' -or $false
function Write-Debug {
    if ($dbug) {
        Write-Host $args -ForegroundColor Magenta
    }
}

$py_s3_funcs_name = "s3_funcs.py"
$py_s3_funcs_path = Join-Path $PSScriptRoot $py_s3_funcs_name
$py_s3_website_sync_name = 's3_website_full_sync.py'
$py_s3_website_sync_path = Join-Path $PSScriptRoot $py_s3_website_sync_name

# Displaying project's fully qualified root path for user's verification.
$ProjectRoot = (Get-Item $ProjectRoot | Select-Object -ExpandProperty FullName) + '\'
$ProjectRoot = $ProjectRoot.Replace('\\','\')
Write-Host "Project Root path: $ProjectRoot" -ForegroundColor Yellow

if ((-not $Force) -and (Read-Host 'Confirmed?').Trim() -notlike 'y*') {
    exit
}

$filenames = @()
foreach ($p in $Path) {
    Write-Debug
    $fullPath = Get-ChildItem $p | Select-Object -ExpandProperty FullName
    Write-Debug "Path: $p"
    Write-Debug "Full path: $fullPath"
    $rp = $fullPath.Replace($ProjectRoot, "")
    Write-Debug "Relative path: $rp"
    $filenames += $rp
}
Write-Debug "`nfilenames: $filenames"
$filenames = $filenames -join ', '

Write-Verbose "Pushing to project directory"
Push-Location $ProjectRoot

# Write-Host "command: " -NoNewline
$output = $err = $null
$error.Clear()
if ($PSCmdlet.ParameterSetName -eq 'SyncChanges') {
    Write-Verbose 'Syncing all updated files...'
    if (-not $dbug) {
        $output = try {
            $py_script_args = @($py_s3_website_sync_path, $ProjectRoot, $BucketName)
            if (-not $DistributionId) {
                Write-Verbose "No Distribution ID specified"
            }
            else {
                Write-Verbose "Distribution ID: $DistributionId"
                $py_script_args += '--distro_id', $DistributionId
            }
            if ($Force) {
                $py_script_args += '--force'
            }
            if ($WhatIfPreference) {
                $py_script_args += '--dry-run'
            }
            # Write-Host "python $py_script_args" -ForegroundColor Cyan
            python $py_script_args 2>&1
        }
        catch {
            Write-Verbose "An error occurred while running the Python script: $_"
            $err = $_.Exception.Message
        }
        if ($null -ne $err -or $output -match 'error') {
            Write-Host "An error occurred during running the Python script: $error"
        }
        Write-Output $output
    }
}
else {
    Write-Verbose 'Uploading individual files...'
    # Write-Host "python `"$py_s3_funcs_path`" `"$filenames`" $BucketName" -ForegroundColor Cyan
    if (-not $dbug) {
        try {
            $output = python $py_s3_funcs_path $filenames $BucketName 2>&1
        }
        catch {
            $err = $_.Exception.Message
        }
        if ($null -ne $err -or $output -match 'error') {
            Write-Host "An error occurred while running the Python script: $error"
        }
        Write-Output $output
    }
}

if (-not $wasInVEnv) {
    Write-Host "Deactivating virtual environment..." -F DarkGray
    deactivate
}

Write-Verbose 'Popping directory, and Done'
Pop-Location