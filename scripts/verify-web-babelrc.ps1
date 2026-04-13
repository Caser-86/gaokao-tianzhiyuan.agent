$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$babelConfigPath = Join-Path $repoRoot 'apps\web\.babelrc'

if (Test-Path $babelConfigPath) {
  throw "Expected apps/web/.babelrc to be removed"
}
