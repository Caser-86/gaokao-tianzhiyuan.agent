$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$pathsThatMustBeTracked = @(
  'apps/web/app/layout.tsx',
  'apps/web/app/globals.css',
  'apps/web/components/public/page-section-renderer.tsx',
  'apps/web/components/public/search-entry.tsx',
  'apps/web/tests/public-content.test.tsx',
  'apps/web/tsconfig.json',
  'apps/web/next-env.d.ts',
  'data/catalog.json'
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
