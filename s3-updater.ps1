param (
    [Parameter(Mandatory=$true)]
    [ValidateScript({
        foreach ($path in $_) {
            if (!(Test-Path $path) -or (Get-Item $path).PSIsContainer) {
                throw "Path '$path' is not a valid file path."
            }
        }
        $true
    })]
    [string[]]$Path,

    [ValidateScript({
        if (!(Test-Path $_) -or !(Get-Item $_).PSIsContainer) {
            throw "Path '$_' is not a valid directory path."
        }
        $true
    })]
    [string]$ProjectRoot = (Get-Location).Path,
    
    # [Parameter(Mandatory=$true)]
    [string]
    $BucketName = 'diego-bucket-test',

    [switch]
    $Force
)
$py_script_name = "s3_funcs.py"

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
Write-Host "python $py_script_name `"$filenames`" $BucketName" -ForegroundColor Cyan
$py_script_path = Join-Path $PSScriptRoot $py_script_name

python $py_script_path $filenames $BucketName

Pop-Location