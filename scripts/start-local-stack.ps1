param(
  [string]$BindHost = '127.0.0.1',
  [int]$ApiPort = 8000,
  [int]$WebPort = 3000,
  [string]$AdminToken = '',
  [string]$WechatOfficialAccountToken = '',
  [string]$WechatOfficialAccountAppId = '',
  [string]$WechatOfficialAccountEncodingAesKey = '',
  [string]$SmartAnalysisMode = '',
  [string]$DatabasePath = '',
  [string]$StateFilePath = '',
  [string]$ApiEnvFilePath = '',
  [string]$WebEnvFilePath = '',
  [switch]$RunSmoke,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$tmpDir = Join-Path $repoRoot '.tmp'
New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

function Write-PlanLine {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Label,
    [Parameter(Mandatory = $true)]
    [string]$Value
  )

  Write-Host ("{0}: {1}" -f $Label, $Value)
}

function Read-EnvFile {
  param(
    [string]$Path
  )

  $values = @{}
  if ([string]::IsNullOrWhiteSpace($Path)) {
    return $values
  }

  $resolvedPath = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
  foreach ($rawLine in Get-Content -LiteralPath $resolvedPath) {
    $line = $rawLine.Trim()
    if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) {
      continue
    }

    $separatorIndex = $line.IndexOf('=')
    if ($separatorIndex -lt 1) {
      continue
    }

    $name = $line.Substring(0, $separatorIndex).Trim()
    $value = $line.Substring($separatorIndex + 1)
    if (
      $value.Length -ge 2 -and (
        ($value.StartsWith('"') -and $value.EndsWith('"')) -or
        ($value.StartsWith("'") -and $value.EndsWith("'"))
      )
    ) {
      $value = $value.Substring(1, $value.Length - 2)
    }

    $values[$name] = $value
  }

  return $values
}

function Resolve-SettingValue {
  param(
    [string]$ExplicitValue,
    [System.Collections.IDictionary[]]$EnvMaps = @(),
    [Parameter(Mandatory = $true)]
    [string]$Name,
    [string]$Fallback = ''
  )

  if (-not [string]::IsNullOrWhiteSpace($ExplicitValue)) {
    return $ExplicitValue
  }

  foreach ($envMap in $EnvMaps) {
    if ($null -eq $envMap) {
      continue
    }

    if ($envMap.ContainsKey($Name)) {
      $candidate = [string]$envMap[$Name]
      if (-not [string]::IsNullOrWhiteSpace($candidate)) {
        return $candidate
      }
    }
  }

  return $Fallback
}

function ConvertTo-EnvAssignmentBlock {
  param(
    [Parameter(Mandatory = $true)]
    [System.Collections.IDictionary]$Variables
  )

  $lines = @()
  foreach ($name in ($Variables.Keys | Sort-Object)) {
    $value = [string]$Variables[$name]
    $escapedValue = $value.Replace("'", "''")
    $lines += "`$env:${name}='$escapedValue'"
  }

  return ($lines -join "`n")
}

function Get-MaskedValue {
  param(
    [string]$Value
  )

  if ([string]::IsNullOrWhiteSpace($Value)) {
    return '(not set)'
  }

  if ($Value.Length -le 4) {
    return ('*' * $Value.Length)
  }

  return ('*' * ($Value.Length - 4)) + $Value.Substring($Value.Length - 4)
}

function Get-SqlitePathFromDatabaseUrl {
  param(
    [string]$DatabaseUrl
  )

  if ([string]::IsNullOrWhiteSpace($DatabaseUrl)) {
    return ''
  }

  if (-not $DatabaseUrl.StartsWith('sqlite:///')) {
    return ''
  }

  $path = $DatabaseUrl.Substring('sqlite:///'.Length)
  if ($path -match '^[A-Za-z]:/') {
    return ($path -replace '/', '\')
  }

  return $path
}

function Wait-UntilReady {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Label,
    [Parameter(Mandatory = $true)]
    [string]$Uri,
    [Parameter(Mandatory = $true)]
    [System.Diagnostics.Process]$Process,
    [Parameter(Mandatory = $true)]
    [string]$StdOutLog,
    [Parameter(Mandatory = $true)]
    [string]$StdErrLog,
    [int]$Attempts = 60
  )

  for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
    try {
      $response = Invoke-RestMethod -Uri $Uri -Method Get
      if ($null -ne $response) {
        return
      }
    }
    catch {
    }

    Start-Sleep -Seconds 1
  }

  $exitHint = if ($Process.HasExited) {
    ' Process exited before readiness check passed.'
  }
  else {
    ''
  }

  throw "$Label did not become ready at $Uri within $Attempts seconds.$exitHint Logs: $StdOutLog ; $StdErrLog"
}

function Wait-UntilStable {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Label,
    [Parameter(Mandatory = $true)]
    [string]$Uri,
    [Parameter(Mandatory = $true)]
    [int]$Port,
    [Parameter(Mandatory = $true)]
    [System.Diagnostics.Process]$Process,
    [Parameter(Mandatory = $true)]
    [string]$StdOutLog,
    [Parameter(Mandatory = $true)]
    [string]$StdErrLog,
    [int]$StableSeconds = 5
  )

  for ($second = 1; $second -le $StableSeconds; $second++) {
    if ($Process.HasExited) {
      throw "$Label exited during the stability window. Logs: $StdOutLog ; $StdErrLog"
    }

    $listenerProcessId = Get-ListeningProcessId -Port $Port
    if (-not $listenerProcessId) {
      throw "$Label stopped listening on port $Port during the stability window. Logs: $StdOutLog ; $StdErrLog"
    }

    try {
      $response = Invoke-RestMethod -Uri $Uri -Method Get
      if ($null -eq $response) {
        throw
      }
    }
    catch {
      throw "$Label failed a stability probe at $Uri. Logs: $StdOutLog ; $StdErrLog"
    }

    Start-Sleep -Seconds 1
  }
}

function Write-ServiceRunnerScript {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Label,
    [Parameter(Mandatory = $true)]
    [string]$WorkingDirectory,
    [Parameter(Mandatory = $true)]
    [string]$EnvAssignmentBlock,
    [Parameter(Mandatory = $true)]
    [string]$CommandText,
    [Parameter(Mandatory = $true)]
    [string]$Timestamp
  )

  $runnerScriptPath = Join-Path $tmpDir ("start-local-stack-{0}.{1}.runner.ps1" -f $Label.ToLowerInvariant(), $Timestamp)
  $escapedWorkingDirectory = $WorkingDirectory.Replace("'", "''")
  $scriptContent = @"
`$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$EnvAssignmentBlock
Set-Location '$escapedWorkingDirectory'
$CommandText
"@
  Set-Content -LiteralPath $runnerScriptPath -Value $scriptContent -Encoding UTF8
  return $runnerScriptPath
}

function Start-ChildService {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Label,
    [Parameter(Mandatory = $true)]
    [string]$WorkingDirectory,
    [Parameter(Mandatory = $true)]
    [string]$RunnerScriptPath,
    [Parameter(Mandatory = $true)]
    [string]$StdOutLog,
    [Parameter(Mandatory = $true)]
    [string]$StdErrLog
  )

  Write-Host "==> Starting $Label" -ForegroundColor Cyan
  $quotedRunnerScriptPath = '"' + $RunnerScriptPath + '"'
  return Start-Process `
    -FilePath 'powershell' `
    -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $quotedRunnerScriptPath) `
    -WorkingDirectory $WorkingDirectory `
    -RedirectStandardOutput $StdOutLog `
    -RedirectStandardError $StdErrLog `
    -PassThru
}

function Get-ListeningProcessId {
  param(
    [Parameter(Mandatory = $true)]
    [int]$Port
  )

  $connection = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
    Select-Object -First 1

  if ($null -eq $connection) {
    return $null
  }

  return $connection.OwningProcess
}

function Select-PreferredProcessId {
  param(
    [int]$ListenerProcessId,
    [int]$FallbackProcessId
  )

  if ($ListenerProcessId) {
    return $ListenerProcessId
  }

  return $FallbackProcessId
}

$defaultApiEnvPath = Join-Path $repoRoot 'apps/api/.env'
$defaultWebEnvPath = Join-Path $repoRoot 'apps/web/.env.local'
$resolvedApiEnvFilePath = if (-not [string]::IsNullOrWhiteSpace($ApiEnvFilePath)) {
  (Resolve-Path -LiteralPath $ApiEnvFilePath -ErrorAction Stop).Path
}
elseif (Test-Path -LiteralPath $defaultApiEnvPath) {
  (Resolve-Path -LiteralPath $defaultApiEnvPath).Path
}
else {
  ''
}
$resolvedWebEnvFilePath = if (-not [string]::IsNullOrWhiteSpace($WebEnvFilePath)) {
  (Resolve-Path -LiteralPath $WebEnvFilePath -ErrorAction Stop).Path
}
elseif (Test-Path -LiteralPath $defaultWebEnvPath) {
  (Resolve-Path -LiteralPath $defaultWebEnvPath).Path
}
else {
  ''
}
$apiEnvValues = Read-EnvFile -Path $resolvedApiEnvFilePath
$webEnvValues = Read-EnvFile -Path $resolvedWebEnvFilePath

$apiBaseUrl = "http://$BindHost`:$ApiPort"
$webBaseUrl = "http://$BindHost`:$WebPort"
$effectiveAdminToken = Resolve-SettingValue `
  -ExplicitValue $AdminToken `
  -EnvMaps @($apiEnvValues, $webEnvValues) `
  -Name 'GAOKAO_AGENT_ADMIN_TOKEN' `
  -Fallback 'dev-admin-token'
$effectiveWechatOfficialAccountToken = Resolve-SettingValue `
  -ExplicitValue $WechatOfficialAccountToken `
  -EnvMaps @($apiEnvValues) `
  -Name 'GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_TOKEN' `
  -Fallback 'dev-wechat-token'
$effectiveWechatOfficialAccountAppId = Resolve-SettingValue `
  -ExplicitValue $WechatOfficialAccountAppId `
  -EnvMaps @($apiEnvValues) `
  -Name 'GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_APP_ID' `
  -Fallback 'wx-dev-appid'
$effectiveWechatOfficialAccountEncodingAesKey = Resolve-SettingValue `
  -ExplicitValue $WechatOfficialAccountEncodingAesKey `
  -EnvMaps @($apiEnvValues) `
  -Name 'GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_ENCODING_AES_KEY' `
  -Fallback 'MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY'
$effectiveSmartAnalysisMode = Resolve-SettingValue `
  -ExplicitValue $SmartAnalysisMode `
  -EnvMaps @($apiEnvValues) `
  -Name 'GAOKAO_AGENT_SMART_ANALYSIS_MODE' `
  -Fallback 'off'
$resolvedDatabaseUrl = if (-not [string]::IsNullOrWhiteSpace($DatabasePath)) {
  'sqlite:///' + ($DatabasePath -replace '\\', '/')
}
else {
  Resolve-SettingValue `
    -ExplicitValue '' `
    -EnvMaps @($apiEnvValues) `
    -Name 'GAOKAO_AGENT_DATABASE_URL' `
    -Fallback ('sqlite:///' + ((Join-Path $tmpDir 'start-local-stack.db') -replace '\\', '/'))
}
$resolvedDatabasePath = if (-not [string]::IsNullOrWhiteSpace($DatabasePath)) {
  $DatabasePath
}
else {
  Get-SqlitePathFromDatabaseUrl -DatabaseUrl $resolvedDatabaseUrl
}
$resolvedStateFilePath = if ([string]::IsNullOrWhiteSpace($StateFilePath)) {
  Join-Path $tmpDir 'start-local-stack.state.json'
}
else {
  $StateFilePath
}
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$apiOutLog = Join-Path $tmpDir "start-local-stack-api.$timestamp.out.log"
$apiErrLog = Join-Path $tmpDir "start-local-stack-api.$timestamp.err.log"
$webOutLog = Join-Path $tmpDir "start-local-stack-web.$timestamp.out.log"
$webErrLog = Join-Path $tmpDir "start-local-stack-web.$timestamp.err.log"

Write-Host '==> Local stack startup plan' -ForegroundColor Cyan
Write-PlanLine -Label 'Repo root' -Value $repoRoot
Write-PlanLine -Label 'API base URL' -Value $apiBaseUrl
Write-PlanLine -Label 'Web base URL' -Value $webBaseUrl
Write-PlanLine -Label 'API env file' -Value $(if ($resolvedApiEnvFilePath) { $resolvedApiEnvFilePath } else { '(not found)' })
Write-PlanLine -Label 'Web env file' -Value $(if ($resolvedWebEnvFilePath) { $resolvedWebEnvFilePath } else { '(not found)' })
Write-PlanLine -Label 'Database URL' -Value $resolvedDatabaseUrl
Write-PlanLine -Label 'Admin token' -Value (Get-MaskedValue -Value $effectiveAdminToken)
Write-PlanLine -Label 'Smart analysis mode' -Value $effectiveSmartAnalysisMode
Write-PlanLine -Label 'WeChat callback token' -Value (Get-MaskedValue -Value $effectiveWechatOfficialAccountToken)
Write-PlanLine -Label 'WeChat app id' -Value $effectiveWechatOfficialAccountAppId
Write-PlanLine -Label 'WeChat AES key configured' -Value (-not [string]::IsNullOrWhiteSpace($effectiveWechatOfficialAccountEncodingAesKey)).ToString()
Write-PlanLine -Label 'State file' -Value $resolvedStateFilePath
Write-PlanLine -Label 'API stdout log' -Value $apiOutLog
Write-PlanLine -Label 'API stderr log' -Value $apiErrLog
Write-PlanLine -Label 'Web stdout log' -Value $webOutLog
Write-PlanLine -Label 'Web stderr log' -Value $webErrLog
Write-PlanLine -Label 'Run smoke after startup' -Value $RunSmoke.ToString()

if ($DryRun) {
  Write-Host 'Dry run requested. No processes were started.' -ForegroundColor Yellow
  return
}

$apiRuntimeEnv = @{}
foreach ($name in $apiEnvValues.Keys) {
  $apiRuntimeEnv[$name] = [string]$apiEnvValues[$name]
}
$apiRuntimeEnv['GAOKAO_AGENT_ADMIN_TOKEN'] = $effectiveAdminToken
$apiRuntimeEnv['GAOKAO_AGENT_DATABASE_URL'] = $resolvedDatabaseUrl
$apiRuntimeEnv['GAOKAO_AGENT_SMART_ANALYSIS_MODE'] = $effectiveSmartAnalysisMode
$apiRuntimeEnv['GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_TOKEN'] = $effectiveWechatOfficialAccountToken
$apiRuntimeEnv['GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_APP_ID'] = $effectiveWechatOfficialAccountAppId
$apiRuntimeEnv['GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_ENCODING_AES_KEY'] = $effectiveWechatOfficialAccountEncodingAesKey
$apiEnvAssignmentBlock = ConvertTo-EnvAssignmentBlock -Variables $apiRuntimeEnv

$webRuntimeEnv = @{}
foreach ($name in $webEnvValues.Keys) {
  $webRuntimeEnv[$name] = [string]$webEnvValues[$name]
}
$webRuntimeEnv['GAOKAO_AGENT_API_URL'] = $apiBaseUrl
$webRuntimeEnv['NEXT_PUBLIC_GAOKAO_AGENT_API_URL'] = $apiBaseUrl
$webRuntimeEnv['GAOKAO_AGENT_ADMIN_TOKEN'] = $effectiveAdminToken
$webEnvAssignmentBlock = ConvertTo-EnvAssignmentBlock -Variables $webRuntimeEnv

$apiCommand = @"
python -m uvicorn app.main:app --host $BindHost --port $ApiPort
"@

$webCommand = @"
node .\node_modules\next\dist\bin\next dev --hostname $BindHost --port $WebPort
"@

$apiRunnerScript = Write-ServiceRunnerScript `
  -Label 'api' `
  -WorkingDirectory (Join-Path $repoRoot 'apps/api') `
  -EnvAssignmentBlock $apiEnvAssignmentBlock `
  -CommandText $apiCommand `
  -Timestamp $timestamp
$webRunnerScript = Write-ServiceRunnerScript `
  -Label 'web' `
  -WorkingDirectory (Join-Path $repoRoot 'apps/web') `
  -EnvAssignmentBlock $webEnvAssignmentBlock `
  -CommandText $webCommand `
  -Timestamp $timestamp

$apiProcess = $null
$webProcess = $null
$apiListenerProcessId = $null
$webListenerProcessId = $null

try {
  $apiProcess = Start-ChildService `
    -Label 'API' `
    -WorkingDirectory (Join-Path $repoRoot 'apps/api') `
    -RunnerScriptPath $apiRunnerScript `
    -StdOutLog $apiOutLog `
    -StdErrLog $apiErrLog

  Wait-UntilReady `
    -Label 'API' `
    -Uri "$apiBaseUrl/health" `
    -Process $apiProcess `
    -StdOutLog $apiOutLog `
    -StdErrLog $apiErrLog

  Wait-UntilStable `
    -Label 'API' `
    -Uri "$apiBaseUrl/health" `
    -Port $ApiPort `
    -Process $apiProcess `
    -StdOutLog $apiOutLog `
    -StdErrLog $apiErrLog

  $apiListenerProcessId = Get-ListeningProcessId -Port $ApiPort

  $webProcess = Start-ChildService `
    -Label 'Web' `
    -WorkingDirectory (Join-Path $repoRoot 'apps/web') `
    -RunnerScriptPath $webRunnerScript `
    -StdOutLog $webOutLog `
    -StdErrLog $webErrLog

  Wait-UntilReady `
    -Label 'Web' `
    -Uri "$webBaseUrl/" `
    -Process $webProcess `
    -StdOutLog $webOutLog `
    -StdErrLog $webErrLog `
    -Attempts 180

  Wait-UntilStable `
    -Label 'Web' `
    -Uri "$webBaseUrl/" `
    -Port $WebPort `
    -Process $webProcess `
    -StdOutLog $webOutLog `
    -StdErrLog $webErrLog

  $webListenerProcessId = Get-ListeningProcessId -Port $WebPort

  if ($RunSmoke) {
    Write-Host '==> Running live smoke checks' -ForegroundColor Cyan
    & (Join-Path $repoRoot 'scripts/smoke-local-stack.ps1') `
      -ApiBaseUrl $apiBaseUrl `
      -WebBaseUrl $webBaseUrl `
      -AdminToken $effectiveAdminToken `
      -WechatOfficialAccountToken $effectiveWechatOfficialAccountToken `
      -WechatOfficialAccountAppId $effectiveWechatOfficialAccountAppId `
      -WechatOfficialAccountEncodingAesKey $effectiveWechatOfficialAccountEncodingAesKey
  }

  Write-Host 'Local stack started successfully.' -ForegroundColor Green
  $displayApiProcessId = Select-PreferredProcessId -ListenerProcessId $apiListenerProcessId -FallbackProcessId $apiProcess.Id
  $displayWebProcessId = Select-PreferredProcessId -ListenerProcessId $webListenerProcessId -FallbackProcessId $webProcess.Id
  $stateDirectory = Split-Path -Parent $resolvedStateFilePath
  if (-not [string]::IsNullOrWhiteSpace($stateDirectory)) {
    New-Item -ItemType Directory -Force -Path $stateDirectory | Out-Null
  }

  @{
    bind_host = $BindHost
    api_port = $ApiPort
    web_port = $WebPort
    api_base_url = $apiBaseUrl
    web_base_url = $webBaseUrl
    api_env_file_path = $resolvedApiEnvFilePath
    web_env_file_path = $resolvedWebEnvFilePath
    smart_analysis_mode = $effectiveSmartAnalysisMode
    database_path = $resolvedDatabasePath
    database_url = $resolvedDatabaseUrl
    api_runner_pid = $apiProcess.Id
    web_runner_pid = $webProcess.Id
    api_pid = $displayApiProcessId
    web_pid = $displayWebProcessId
    api_runner_script = $apiRunnerScript
    web_runner_script = $webRunnerScript
    api_stdout_log = $apiOutLog
    api_stderr_log = $apiErrLog
    web_stdout_log = $webOutLog
    web_stderr_log = $webErrLog
    started_at = (Get-Date).ToString('o')
  } | ConvertTo-Json -Depth 4 | Set-Content -Path $resolvedStateFilePath

  Write-PlanLine -Label 'API PID' -Value $displayApiProcessId.ToString()
  Write-PlanLine -Label 'Web PID' -Value $displayWebProcessId.ToString()
  Write-PlanLine -Label 'State file' -Value $resolvedStateFilePath
  Write-PlanLine -Label 'Web homepage' -Value $webBaseUrl
  Write-PlanLine -Label 'Web chat' -Value "$webBaseUrl/chat"
  Write-PlanLine -Label 'Web admin' -Value "$webBaseUrl/admin"
  Write-Host 'Stop commands:' -ForegroundColor Yellow
  Write-Host "  Stop-Process -Id $displayApiProcessId,$displayWebProcessId"
}
catch {
  if ($webProcess -and -not $webProcess.HasExited) {
    Stop-Process -Id $webProcess.Id -Force
  }
  if ($apiProcess -and -not $apiProcess.HasExited) {
    Stop-Process -Id $apiProcess.Id -Force
  }
  $webListenerProcessId = Get-ListeningProcessId -Port $WebPort
  if ($webListenerProcessId) {
    Stop-Process -Id $webListenerProcessId -Force -ErrorAction SilentlyContinue
  }
  $apiListenerProcessId = Get-ListeningProcessId -Port $ApiPort
  if ($apiListenerProcessId) {
    Stop-Process -Id $apiListenerProcessId -Force -ErrorAction SilentlyContinue
  }
  Remove-Item -LiteralPath $resolvedStateFilePath -Force -ErrorAction SilentlyContinue
  throw
}
