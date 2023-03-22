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
[CmdletBinding(DefaultParameterSetName='SyncChanges')]
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

    [switch] 
    $Force
)
if ($PSCmdlet.ParameterSetName -eq 'SyncChanges') {
    Write-Host "Syncing all updated files"
}

$dbug = $DebugPreference -eq 'Continue' -or $false
function Write-Debug {
    if ($dbug) {
        Write-Host $args -ForegroundColor Magenta
    }
}

$py_s3_funcs_name = "s3_funcs.py"
$py_s3_funcs_path = Join-Path $PSScriptRoot $py_s3_funcs_name
$py_s3_website_sync_name = 'website_full_sync.py'
$py_s3_website_sync_path = Join-Path $PSScriptRoot $py_s3_website_sync_name

$ProjectRoot = (Get-Item $ProjectRoot | Select-Object -ExpandProperty FullName) + '\'
$ProjectRoot = $ProjectRoot.Replace('\\','\')
Write-Host "Project Root path: $ProjectRoot" -ForegroundColor Yellow

if ((-not $Force) -and (Read-Host 'Confirmed?').Trim() -notlike 'y*') {
    Write-Host "Exiting"
    return
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

Push-Location $ProjectRoot

# Write-Host "command: " -NoNewline
if ($PSCmdlet.ParameterSetName -eq 'SyncChanges') {
    # Write-Host "python $py_s3_website_sync_name `"$ProjectRoot`" $BucketName" -ForegroundColor Cyan
    if (-not $dbug) {
        $output = $err = $null
        try {
            $output = python $py_s3_website_sync_path $ProjectRoot $BucketName 2>&1
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
else {
    # Write-Host "python $py_s3_funcs_name `"$filenames`" $BucketName" -ForegroundColor Cyan
    if (-not $dbug) {
        $output = $err = $null
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

Pop-Location