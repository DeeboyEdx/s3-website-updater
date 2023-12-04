param(
    [string] $BucketName = 'pccommander.net'
)
$index = if ((hostname) -eq 'YMMTA0015') {
    -1
} else {
    0
}
try {
    $allProjects = Get-Content (Join-Path $PSScriptRoot 'projects.json') -ErrorAction Stop | ConvertFrom-Json
    $projects = $allProjects.Where({ $_.BucketName -eq $BucketName })
    $customObject = $projects[$index]
}
catch {
    Throw "Error: $($_.Exception.Message)"
}
$params = @{}
$customObject.PSObject.Properties | ForEach-Object {
    $params[$_.Name] = $_.Value
}

return $params