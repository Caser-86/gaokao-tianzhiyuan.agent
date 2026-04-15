param(
  [string]$BindHost = '127.0.0.1',
  [int]$ApiPort = 8000,
  [int]$WebPort = 3000,
  [string]$AdminToken = 'dev-admin-token',
  [string]$DatabasePath = '',
  [string]$StateFilePath = '',
  [switch]$RunSmoke,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$tmpDir = Join-Path $repoRoot '.tmp'
New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

$apiBaseUrl = "http://$BindHost`:$ApiPort"
$webBaseUrl = "http://$BindHost`:$WebPort"
$resolvedDatabasePath = if ([string]::IsNullOrWhiteSpace($DatabasePath)) {
  Join-Path $tmpDir 'start-local-stack.db'
}
else {
  $DatabasePath
}

$resolvedDatabaseUrl = 'sqlite:///' + ($resolvedDatabasePath -replace '\\', '/')
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

function Write-PlanLine {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Label,
    [Parameter(Mandatory = $true)]
    [string]$Value
  )

  Write-Host ("{0}: {1}" -f $Label, $Value)
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
    " Process exited before readiness check passed."
  }
  else {
    ''
  }

  throw "$Label did not become ready at $Uri within $Attempts seconds.$exitHint Logs: $StdOutLog ; $StdErrLog"
}

function Start-ChildService {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Label,
    [Parameter(Mandatory = $true)]
    [string]$WorkingDirectory,
    [Parameter(Mandatory = $true)]
    [string]$ScriptBlockText,
    [Parameter(Mandatory = $true)]
    [string]$StdOutLog,
    [Parameter(Mandatory = $true)]
    [string]$StdErrLog
  )

  Write-Host "==> Starting $Label" -ForegroundColor Cyan
  return Start-Process `
    -FilePath 'powershell' `
    -ArgumentList @('-NoProfile', '-Command', $ScriptBlockText) `
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

Write-Host '==> Local stack startup plan' -ForegroundColor Cyan
Write-PlanLine -Label 'Repo root' -Value $repoRoot
Write-PlanLine -Label 'API base URL' -Value $apiBaseUrl
Write-PlanLine -Label 'Web base URL' -Value $webBaseUrl
Write-PlanLine -Label 'Database URL' -Value $resolvedDatabaseUrl
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

$apiCommand = @"
`$env:GAOKAO_AGENT_ADMIN_TOKEN='$AdminToken'
`$env:GAOKAO_AGENT_DATABASE_URL='$resolvedDatabaseUrl'
`$env:GAOKAO_AGENT_SMART_ANALYSIS_MODE='off'
python -m uvicorn app.main:app --host $BindHost --port $ApiPort
"@

$webCommand = @"
`$env:GAOKAO_AGENT_API_URL='$apiBaseUrl'
`$env:NEXT_PUBLIC_GAOKAO_AGENT_API_URL='$apiBaseUrl'
`$env:GAOKAO_AGENT_ADMIN_TOKEN='$AdminToken'
node .\node_modules\next\dist\bin\next dev --hostname $BindHost --port $WebPort
"@

$apiProcess = $null
$webProcess = $null
$apiListenerProcessId = $null
$webListenerProcessId = $null

try {
  $apiProcess = Start-ChildService `
    -Label 'API' `
    -WorkingDirectory (Join-Path $repoRoot 'apps/api') `
    -ScriptBlockText $apiCommand `
    -StdOutLog $apiOutLog `
    -StdErrLog $apiErrLog

  Wait-UntilReady `
    -Label 'API' `
    -Uri "$apiBaseUrl/health" `
    -Process $apiProcess `
    -StdOutLog $apiOutLog `
    -StdErrLog $apiErrLog

  $apiListenerProcessId = Get-ListeningProcessId -Port $ApiPort

  $webProcess = Start-ChildService `
    -Label 'Web' `
    -WorkingDirectory (Join-Path $repoRoot 'apps/web') `
    -ScriptBlockText $webCommand `
    -StdOutLog $webOutLog `
    -StdErrLog $webErrLog

  Wait-UntilReady `
    -Label 'Web' `
    -Uri "$webBaseUrl/" `
    -Process $webProcess `
    -StdOutLog $webOutLog `
    -StdErrLog $webErrLog

  $webListenerProcessId = Get-ListeningProcessId -Port $WebPort

  if ($RunSmoke) {
    Write-Host '==> Running live smoke checks' -ForegroundColor Cyan
    & (Join-Path $repoRoot 'scripts/smoke-local-stack.ps1') `
      -ApiBaseUrl $apiBaseUrl `
      -WebBaseUrl $webBaseUrl `
      -AdminToken $AdminToken
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
    admin_token = $AdminToken
    database_path = $resolvedDatabasePath
    database_url = $resolvedDatabaseUrl
    api_pid = $displayApiProcessId
    web_pid = $displayWebProcessId
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
