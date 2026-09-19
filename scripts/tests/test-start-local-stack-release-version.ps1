$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '../..')
$startScript = Join-Path $repoRoot 'scripts/start-local-stack.ps1'
$apiEnv = Join-Path $repoRoot 'apps/api/.env.example'
$webEnv = Join-Path $repoRoot 'apps/web/.env.example'

$output = & powershell -NoProfile -ExecutionPolicy Bypass -File $startScript `
  -ReleaseVersion 'release-version-test' `
  -ApiEnvFilePath $apiEnv `
  -WebEnvFilePath $webEnv `
  -AdminToken 'synthetic-start-admin' `
  -WechatOfficialAccountToken 'synthetic-start-wechat' `
  -WechatOfficialAccountAppId 'wx-synthetic-start' `
  -WechatOfficialAccountEncodingAesKey ('a' * 43) `
  -DatabasePath '.tmp/test-start-release-version.db' `
  -StateFilePath '.tmp/test-start-release-version.state.json' `
  -DryRun 2>&1 | Out-String

if ($LASTEXITCODE -ne 0) {
  throw "start-local-stack release version dry run failed: $output"
}

if ($output -notmatch 'Release version: release-version-test') {
  throw "start-local-stack did not report the requested release version. Output: $output"
}

Write-Host 'start-local-stack release version test passed.' -ForegroundColor Green
