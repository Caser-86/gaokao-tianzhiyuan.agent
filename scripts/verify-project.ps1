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

$pythonCandidates = @(
  (Join-Path $repoRoot 'apps/api/.venv/Scripts/python.exe')
  (Join-Path $repoRoot 'apps/api/.venv/bin/python')
)
$repoPython = $pythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $repoPython) {
  $repoPython = 'python'
}

Invoke-RepoScript -Label 'Verify gitignore coverage' -RelativePath 'scripts/verify-gitignore.ps1'
Invoke-RepoScript -Label 'Verify platform foundation files' -RelativePath 'scripts/verify-platform-foundation.ps1'
Invoke-RepoScript -Label 'Verify public foundation files' -RelativePath 'scripts/verify-public-foundation.ps1'
Invoke-RepoScript -Label 'Verify web Babel cleanup' -RelativePath 'scripts/verify-web-babelrc.ps1'

Invoke-RepoCommand `
  -Label 'Verify JSON data assets' `
  -WorkingDirectory $repoRoot `
  -FilePath $repoPython `
  -ArgumentList @((Join-Path $repoRoot 'scripts/verify-data-assets.py'))

Invoke-RepoCommand `
  -Label 'Run JSON data asset validator test' `
  -WorkingDirectory $repoRoot `
  -FilePath $repoPython `
  -ArgumentList @((Join-Path $repoRoot 'scripts/tests/test_verify_data_assets.py'))

Invoke-RepoScript -Label 'Run smoke replay uniqueness regression' -RelativePath 'scripts/tests/test-smoke-replay-uniqueness.ps1'
Invoke-RepoScript -Label 'Run official-account smoke replay uniqueness regression' -RelativePath 'scripts/tests/test-wechat-official-smoke-replay-uniqueness.ps1'
Invoke-RepoScript -Label 'Run local stack release version regression' -RelativePath 'scripts/tests/test-start-local-stack-release-version.ps1'

if (-not $SkipApiTests) {
  Invoke-RepoCommand `
    -Label 'Run API test suite' `
    -WorkingDirectory (Join-Path $repoRoot 'apps/api') `
    -FilePath $repoPython `
    -ArgumentList @('-m', 'pytest', '-q', '--cov=app', '--cov-report=term-missing')
}

if (-not $SkipWebTests) {
  Invoke-RepoCommand `
    -Label 'Run web test suite' `
    -WorkingDirectory (Join-Path $repoRoot 'apps/web') `
    -FilePath 'npm' `
    -ArgumentList @('run', 'test:coverage')
}

Invoke-RepoCommand `
  -Label 'Run web typecheck' `
  -WorkingDirectory (Join-Path $repoRoot 'apps/web') `
  -FilePath 'npm' `
  -ArgumentList @('run', 'typecheck')

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
