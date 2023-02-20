Describe "Test script parameters" {
    It "Validates the Path parameter with valid paths" {
        $Path = @(
            "C:\temp\file1.txt",
            "C:\temp\file2.txt"
        )

        $scriptBlock = {
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
                [string[]]$Path
            )

            $Path
        }

        $result = Invoke-Pester -ScriptBlock $scriptBlock -Parameters @{Path = $Path}

        $result | Should Be $Path
    }

    It "Throws an error for invalid file paths" {
        $Path = @(
            "C:\temp\file1.txt",
            "C:\temp\file2.txt",
            "C:\temp\folder1"
        )

        $scriptBlock = {
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
                [string[]]$Path
            )

            $Path
        }

        $result = Invoke-Pester -ScriptBlock $scriptBlock -Parameters @{Path = $Path} -ErrorAction SilentlyContinue

        $result | Should BeNullOrEmpty
    }

    It "Validates the ProjectRoot parameter with a valid path" {
        $ProjectRoot = "C:\temp"

        $scriptBlock = {
            param (
                [string]$ProjectRoot = (Get-Location),
                [ValidateScript({
                    if (!(Test-Path $_) -or (Get-Item $_).PSIsContainer) {
                        throw "Path '$_' is not a valid directory path."
                    }
                    $true
                })]
                [string]$ProjectRoot
            )

            $ProjectRoot
        }

        $result = Invoke-Pester -ScriptBlock $scriptBlock -Parameters @{ProjectRoot = $ProjectRoot}

        $result | Should Be $ProjectRoot
    }

    It "Throws an error for an invalid ProjectRoot path" {
        $ProjectRoot = "C:\temp\invalid"

        $scriptBlock = {
            param (
                [string]$ProjectRoot = (Get-Location),
                [ValidateScript({
                    if (!(Test-Path $_) -or (Get-Item $_).PSIsContainer) {
                        throw "Path '$_' is not a valid directory path."
                    }
                    $true
                })]
                [string]$ProjectRoot
            )

            $ProjectRoot
        }

        $result = Invoke-Pester -ScriptBlock $scriptBlock -Parameters @{ProjectRoot = $ProjectRoot} -ErrorAction SilentlyContinue

        $result | Should BeNullOrEmpty
    }
}
