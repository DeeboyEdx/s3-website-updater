echo Note: This was designed to be run on my personal computer
pause
pwsh -noprofile -command "deactivate; .\.win-venv\Scripts\activate; .\s3-uploader.ps1 -ProjectRoot C:\Users\aquar\OneDrive\Documents\QuikScripts\python\push2pc\s3-html\ -BucketName pccommander.net -DistributionId ETFTX83TEXR9E -SyncJustChanges"