$gitPath = "C:\Program Files\Git\cmd\git.exe"
$gitDir = Join-Path $PSScriptRoot ".git-codex"

if (-not (Test-Path $gitPath)) {
  Write-Error "Git not found at $gitPath"
  exit 1
}

if (-not (Test-Path $gitDir)) {
  Write-Error "Writable Git directory not found at $gitDir"
  exit 1
}

$env:GIT_DIR = $gitDir
$env:GIT_WORK_TREE = $PSScriptRoot
& $gitPath @args
exit $LASTEXITCODE
