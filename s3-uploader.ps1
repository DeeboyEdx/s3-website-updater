[CmdletBinding(DefaultParameterSetName='SyncChanges')]
param (
    
    # [Parameter(Mandatory=$true)]
    [string] $BucketName = 'diego-bucket-test',

    [ValidateScript({
        if (!(Test-Path $_) -or !(Get-Item $_).PSIsContainer) {
            throw "Path '$_' is not a valid directory path."
        }
        $true
    })]
    [string] $ProjectRoot = (Get-Location).Path,

    [Parameter(ParameterSetName='SyncChanges')]
    [switch] $SyncJustChanges,

    [Parameter(ParameterSetName='IndividualFiles', Mandatory=$true)]
    [ValidateScript({
        foreach ($path in $_) {
            if (!(Test-Path $path) -or (Get-Item $path).PSIsContainer) {
                throw "Path '$path' is not a valid file path."
            }
        }
        $true
    })]
    [string[]] $Path,

    [switch] $Force
)
if ($PSCmdlet.ParameterSetName -eq 'SyncChanges') {
    Write-Host "Syncing all updated files"
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
    # Write-Host
    $fullPath = Get-ChildItem $p | Select-Object -ExpandProperty FullName
    # Write-Host "Path: $p"
    # Write-Host "Full path: $fullPath"
    $rp = $fullPath.Replace($ProjectRoot, "")
    # Write-Host "Relative path: $rp"
    $filenames += $rp
}

# Write-Host "`nfilenames: $filenames"

# $filenames = '"' + ($filenames -join ', ') + '"'
$filenames = $filenames -join ', '

Push-Location $ProjectRoot

Write-Host "command: " -NoNewline

if ($PSCmdlet.ParameterSetName -eq 'SyncChanges') {
    Write-Host "python $py_s3_website_sync_name `"$ProjectRoot`" $BucketName" -ForegroundColor Cyan
    python $py_s3_website_sync_path $ProjectRoot $BucketName
}
else {
    Write-Host "python $py_s3_funcs_name `"$filenames`" $BucketName" -ForegroundColor Cyan
    python $py_s3_funcs_path $filenames $BucketName
}

Pop-Location