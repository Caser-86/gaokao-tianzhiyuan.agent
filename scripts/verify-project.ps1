param(
  [switch]$SkipApiTests,
  [switch]$SkipWebTests,
  [switch]$SkipWebBuild
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')

function Invoke-RepoCommand {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Label,
    [Parameter(Mandatory = $true)]
    [string]$WorkingDirectory,
    [Parameter(Mandatory = $true)]
    [string]$FilePath,
    [string[]]$ArgumentList = @()
  )

  Push-Location $WorkingDirectory
  try {
    Write-Host "==> $Label" -ForegroundColor Cyan
    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
      throw "$Label failed with exit code $LASTEXITCODE"
    }
  }
  finally {
    Pop-Location
  }
}

function Invoke-RepoScript {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Label,
    [Parameter(Mandatory = $true)]
    [string]$RelativePath
  )

  Invoke-RepoCommand `
    -Label $Label `
    -WorkingDirectory $repoRoot `
    -FilePath 'powershell' `
    -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $repoRoot $RelativePath))
}

Invoke-RepoScript -Label 'Verify gitignore coverage' -RelativePath 'scripts/verify-gitignore.ps1'
Invoke-RepoScript -Label 'Verify platform foundation files' -RelativePath 'scripts/verify-platform-foundation.ps1'
Invoke-RepoScript -Label 'Verify public foundation files' -RelativePath 'scripts/verify-public-foundation.ps1'
Invoke-RepoScript -Label 'Verify web Babel cleanup' -RelativePath 'scripts/verify-web-babelrc.ps1'

if (-not $SkipApiTests) {
  Invoke-RepoCommand `
    -Label 'Run API test suite' `
    -WorkingDirectory (Join-Path $repoRoot 'apps/api') `
    -FilePath 'python' `
    -ArgumentList @('-m', 'pytest', '-q')
}

if (-not $SkipWebTests) {
  Invoke-RepoCommand `
    -Label 'Run web test suite' `
    -WorkingDirectory (Join-Path $repoRoot 'apps/web') `
    -FilePath 'npm' `
    -ArgumentList @('test', '--')
}

if (-not $SkipWebBuild) {
  Invoke-RepoCommand `
    -Label 'Run web production build' `
    -WorkingDirectory (Join-Path $repoRoot 'apps/web') `
    -FilePath 'npm' `
    -ArgumentList @('run', 'build')
}

Write-Host '==> Working tree status' -ForegroundColor Cyan
Push-Location $repoRoot
try {
  git status --short
  if ($LASTEXITCODE -ne 0) {
    throw "git status failed with exit code $LASTEXITCODE"
  }
}
finally {
  Pop-Location
}

Write-Host 'Project verification finished successfully.' -ForegroundColor Green
