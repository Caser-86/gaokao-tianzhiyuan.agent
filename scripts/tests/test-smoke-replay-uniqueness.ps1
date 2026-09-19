$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '../..')
$smokeScript = Join-Path $repoRoot 'scripts/smoke-local-stack.ps1'
$apiEnv = Join-Path $repoRoot 'apps/api/.env.example'

function Get-DryRunVerificationNonce {
  $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $smokeScript `
    -ApiBaseUrl 'http://127.0.0.1:8000' `
    -WebBaseUrl 'http://127.0.0.1:3000' `
    -ApiEnvFilePath $apiEnv `
    -AdminToken 'synthetic-smoke-admin' `
    -WechatOfficialAccountToken 'synthetic-smoke-wechat' `
    -WechatOfficialAccountAppId 'wx-synthetic-smoke' `
    -WechatOfficialAccountEncodingAesKey ('a' * 43) `
    -SkipAdminCheck `
    -SkipChatProbe `
    -SkipWechatProbe `
    -DryRun 2>&1 | Out-String

  if ($LASTEXITCODE -ne 0) {
    throw "Smoke dry run failed: $output"
  }

  $match = [regex]::Match(
    $output,
    'official-account\?signature=[^&]+&timestamp=[^&]+&nonce=([^&]+)&echostr='
  )
  if (-not $match.Success) {
    throw "Smoke dry run did not expose a verification nonce. Output: $output"
  }

  return $match.Groups[1].Value
}

$firstNonce = Get-DryRunVerificationNonce
$secondNonce = Get-DryRunVerificationNonce

if ($firstNonce -eq $secondNonce) {
  throw "Smoke verification nonce was reused across runs: $firstNonce"
}

if (-not $firstNonce.StartsWith('smoke-') -or -not $secondNonce.StartsWith('smoke-')) {
  throw "Smoke verification nonce does not use the smoke namespace: $firstNonce / $secondNonce"
}

Write-Host "Smoke replay uniqueness test passed: $firstNonce != $secondNonce" -ForegroundColor Green
