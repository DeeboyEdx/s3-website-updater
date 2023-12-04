# s3-website-updater

Scripts for simplifying the updating of s3-hosted websites from local project files

## Latest update

Created Get-Params.ps1 and Update-S3Website.ps1

Get-Params.ps1
based on BucketName parameter AND computer's hostname, it'll return a params hashtable

Update-S3Website.ps1
is a one command way of kicking off the whole update process with minimal arguments, just a WebsiteName (which in turn is used as the BucketName argument to Get-Params)
