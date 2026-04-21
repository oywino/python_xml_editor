$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$appJsPath = Join-Path $projectRoot "app.js"
$launcherPath = Join-Path $projectRoot "XML_Editor.py"
$distDir = Join-Path $projectRoot "dist"
$releaseDir = Join-Path $projectRoot "release"
$separator = if ($IsWindows) { ";" } else { ":" }

function Get-PythonCommand {
  if (Get-Command py -ErrorAction SilentlyContinue) {
    return @("py", "-3")
  }

  if (Get-Command python -ErrorAction SilentlyContinue) {
    return @("python")
  }

  throw "Python was not found on PATH. Install Python first."
}

function Invoke-Python {
  param(
    [string[]]$PythonCommand,
    [string[]]$Arguments
  )

  $exe = $PythonCommand[0]
  $prefixArgs = @()
  if ($PythonCommand.Length -gt 1) {
    $prefixArgs = $PythonCommand[1..($PythonCommand.Length - 1)]
  }

  & $exe @($prefixArgs + $Arguments)
}

function Get-AppVersion {
  $content = Get-Content $appJsPath -Raw
  $match = [regex]::Match($content, "const APP_VERSION = '([^']+)'")
  if (-not $match.Success) {
    throw "Could not find APP_VERSION in app.js."
  }
  return $match.Groups[1].Value
}

$pythonCmd = Get-PythonCommand
$version = Get-AppVersion
$outputName = "XML_Prompt_Editor_$version.exe"
$distExePath = Join-Path $distDir "XML_Prompt_Editor.exe"

Write-Host "Building XML Prompt Editor $version"

try {
  Invoke-Python -PythonCommand $pythonCmd -Arguments @("-m", "PyInstaller", "--version") | Out-Null
} catch {
  throw "PyInstaller is not available. Install it with: py -3 -m pip install pyinstaller"
}

foreach ($path in @(
  (Join-Path $projectRoot "build"),
  $distDir,
  $releaseDir
)) {
  if (Test-Path $path) {
    Remove-Item -LiteralPath $path -Recurse -Force
  }
}

Invoke-Python -PythonCommand $pythonCmd -Arguments @(
  "-m", "PyInstaller",
  "--clean",
  "--noconfirm",
  "--onefile",
  "--windowed",
  "--name", "XML_Prompt_Editor",
  "--add-data", ("{0}{1}." -f (Join-Path $projectRoot "index.html"), $separator),
  "--add-data", ("{0}{1}." -f (Join-Path $projectRoot "app.js"), $separator),
  "--add-data", ("{0}{1}." -f (Join-Path $projectRoot "style.css"), $separator),
  $launcherPath
)

if (-not (Test-Path $distExePath)) {
  throw "PyInstaller completed without creating $distExePath"
}

New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
$releaseExePath = Join-Path $releaseDir $outputName
Copy-Item $distExePath $releaseExePath -Force

if (-not (Test-Path $releaseExePath)) {
  throw "Expected release executable was not created: $releaseExePath"
}

Write-Host "Created:" $releaseExePath
