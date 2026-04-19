$ghPath = "C:\Program Files\GitHub CLI\gh.exe"
$ghConfigDir = Join-Path $PSScriptRoot ".codex-gh"

if (-not (Test-Path $ghPath)) {
  Write-Error "GitHub CLI not found at $ghPath"
  exit 1
}

if (-not (Test-Path $ghConfigDir)) {
  New-Item -ItemType Directory -Path $ghConfigDir | Out-Null
}

$env:GH_CONFIG_DIR = $ghConfigDir
& $ghPath @args
exit $LASTEXITCODE
