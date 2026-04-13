$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$pathsThatMustBeIgnored = @(
  'apps/web/.next/cache/test-entry',
  'apps/web/node_modules/react/index.js',
  'apps/api/__pycache__/main.cpython-313.pyc',
  'apps/api/.pytest_cache/v/cache/nodeids'
)

Push-Location $repoRoot
try {
  foreach ($path in $pathsThatMustBeIgnored) {
    git check-ignore $path | Out-Null
    if ($LASTEXITCODE -ne 0) {
      throw "Expected git to ignore $path"
    }
  }
}
finally {
  Pop-Location
}
