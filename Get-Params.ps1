<#
.SYNOPSIS
    Retrieves project parameters based on the provided BucketName from a JSON file.

.DESCRIPTION
    This script reads project information from a JSON file named 'projects.json'
    and extracts parameters for a specific project identified by the given BucketName.
    The project parameters are stored in a hashtable and returned.

.PARAMETER BucketName
    Specifies the name of the bucket for which project parameters need to be retrieved.
    Default value is 'pccommander.net'.

.EXAMPLE
    PS C:\> .\Get-Params.ps1 -BucketName 'YourBucketName'
    Retrieves and returns project parameters for the specified bucket.

.NOTES
    This script is making two assumptions in order to function for two computers with differing project root paths.  More if subsequent computers share the same project root path.
    1. There are no more than two sets of parameters for the same project.  (Anymore would never be returned.)
    2. The named computer uses the parameters (in particular, the project path) that's listed last in the 'projects.json' file
    2b. The non-named computer uses the first applicable parameters in the 'projects.json' file

    File: Get-Params.ps1
    Author: Diego Reategui
    Date: 2023-12-26

#>
param(
    [string] $BucketName = 'pccommander.net'
)
$NON_MAIN_COMPUTERS_NAME = 'YMMTA0015'
$index = if ((hostname) -eq $NON_MAIN_COMPUTERS_NAME) {
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