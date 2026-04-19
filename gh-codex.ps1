$ghPath = "C:\Program Files\GitHub CLI\gh.exe"
$ghConfigDir = Join-Path $PSScriptRoot ".codex-gh"
$gitDir = Join-Path $PSScriptRoot ".git-codex"

if (-not (Test-Path $ghPath)) {
  Write-Error "GitHub CLI not found at $ghPath"
  exit 1
}

if (-not (Test-Path $ghConfigDir)) {
  New-Item -ItemType Directory -Path $ghConfigDir | Out-Null
}

$env:GH_CONFIG_DIR = $ghConfigDir
$env:GIT_DIR = $gitDir
$env:GIT_WORK_TREE = $PSScriptRoot
& $ghPath @args
exit $LASTEXITCODE
