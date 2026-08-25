$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '../..')
$smokeScript = Join-Path $repoRoot 'scripts/smoke-wechat-official-account.ps1'
$apiEnv = Join-Path $repoRoot 'apps/api/.env.example'

function Get-DryRunVerificationNonce {
  $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $smokeScript `
    -ApiBaseUrl 'http://127.0.0.1:8000' `
    -ApiEnvFilePath $apiEnv `
    -WechatOfficialAccountToken 'synthetic-official-wechat' `
    -WechatOfficialAccountAppId 'wx-synthetic-official' `
    -WechatOfficialAccountEncodingAesKey ('a' * 43) `
    -DryRun 2>&1 | Out-String

  if ($LASTEXITCODE -ne 0) {
    throw "Official-account smoke dry run failed: $output"
  }

  $match = [regex]::Match(
    $output,
    'official-account\?signature=[^&]+&timestamp=[^&]+&nonce=([^&]+)'
  )
  if (-not $match.Success) {
    throw "Official-account smoke did not expose a verification nonce. Output: $output"
  }

  return $match.Groups[1].Value
}

$firstNonce = Get-DryRunVerificationNonce
$secondNonce = Get-DryRunVerificationNonce

if ($firstNonce -eq $secondNonce) {
  throw "Official-account smoke verification nonce was reused: $firstNonce"
}

if (-not $firstNonce.StartsWith('smoke-') -or -not $secondNonce.StartsWith('smoke-')) {
  throw "Official-account smoke nonce does not use the smoke namespace: $firstNonce / $secondNonce"
}

Write-Host "Official-account smoke replay uniqueness test passed: $firstNonce != $secondNonce" -ForegroundColor Green
