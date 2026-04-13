$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$pathsThatMustBeTracked = @(
  'apps/api/app/routers/platform.py',
  'apps/api/app/services/platform.py',
  'apps/api/tests/test_platform_api.py'
)

Push-Location $repoRoot
try {
  foreach ($path in $pathsThatMustBeTracked) {
    git ls-files --error-unmatch -- $path | Out-Null
    if ($LASTEXITCODE -ne 0) {
      throw "Expected git to track $path"
    }
  }
}
finally {
  Pop-Location
}
