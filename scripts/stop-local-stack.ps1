param(
  [string]$StateFilePath = '',
  [int]$ApiPort = 0,
  [int]$WebPort = 0,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$tmpDir = Join-Path $repoRoot '.tmp'
$resolvedStateFilePath = if ([string]::IsNullOrWhiteSpace($StateFilePath)) {
  Join-Path $tmpDir 'start-local-stack.state.json'
}
else {
  $StateFilePath
}

function Write-PlanLine {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Label,
    [Parameter(Mandatory = $true)]
    [string]$Value
  )

  Write-Host ("{0}: {1}" -f $Label, $Value)
}

function Get-ListeningProcessId {
  param(
    [Parameter(Mandatory = $true)]
    [int]$Port
  )

  if ($Port -le 0) {
    return $null
  }

  $connection = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
    Select-Object -First 1

  if ($null -eq $connection) {
    return $null
  }

  return $connection.OwningProcess
}

function Stop-ProcessIfRunning {
  param(
    [Parameter(Mandatory = $true)]
    [int]$ProcessId,
    [Parameter(Mandatory = $true)]
    [string]$Label
  )

  if ($ProcessId -le 0) {
    return
  }

  $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
  if ($null -eq $process) {
    Write-Host "$Label pid $ProcessId is not running."
    return
  }

  if ($DryRun) {
    Write-Host "Would stop $Label pid $ProcessId"
    return
  }

  Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
  Write-Host "Stopped $Label pid $ProcessId"
}

$state = $null
if (Test-Path -LiteralPath $resolvedStateFilePath) {
  $state = Get-Content -LiteralPath $resolvedStateFilePath -Raw | ConvertFrom-Json
}

$resolvedApiPort = if ($ApiPort -gt 0) { $ApiPort } elseif ($state) { [int]$state.api_port } else { 0 }
$resolvedWebPort = if ($WebPort -gt 0) { $WebPort } elseif ($state) { [int]$state.web_port } else { 0 }
$apiRunnerPid = if ($state -and $state.PSObject.Properties.Name -contains 'api_runner_pid') { [int]$state.api_runner_pid } else { 0 }
$webRunnerPid = if ($state -and $state.PSObject.Properties.Name -contains 'web_runner_pid') { [int]$state.web_runner_pid } else { 0 }
$apiPid = if ($state) { [int]$state.api_pid } else { 0 }
$webPid = if ($state) { [int]$state.web_pid } else { 0 }

Write-Host '==> Local stack stop plan' -ForegroundColor Cyan
Write-PlanLine -Label 'State file' -Value $resolvedStateFilePath
Write-PlanLine -Label 'API port' -Value $resolvedApiPort.ToString()
Write-PlanLine -Label 'Web port' -Value $resolvedWebPort.ToString()
Write-PlanLine -Label 'API runner pid from state' -Value $apiRunnerPid.ToString()
Write-PlanLine -Label 'Web runner pid from state' -Value $webRunnerPid.ToString()
Write-PlanLine -Label 'API pid from state' -Value $apiPid.ToString()
Write-PlanLine -Label 'Web pid from state' -Value $webPid.ToString()

Stop-ProcessIfRunning -ProcessId $webPid -Label 'Web'
Stop-ProcessIfRunning -ProcessId $apiPid -Label 'API'
Stop-ProcessIfRunning -ProcessId $webRunnerPid -Label 'Web runner'
Stop-ProcessIfRunning -ProcessId $apiRunnerPid -Label 'API runner'

$webListenerProcessId = Get-ListeningProcessId -Port $resolvedWebPort
if ($webListenerProcessId) {
  Stop-ProcessIfRunning -ProcessId $webListenerProcessId -Label 'Web listener'
}

$apiListenerProcessId = Get-ListeningProcessId -Port $resolvedApiPort
if ($apiListenerProcessId) {
  Stop-ProcessIfRunning -ProcessId $apiListenerProcessId -Label 'API listener'
}

if ($DryRun) {
  Write-Host 'Dry run requested. No processes were stopped.' -ForegroundColor Yellow
  return
}

Start-Sleep -Seconds 1

$remainingApiListener = Get-ListeningProcessId -Port $resolvedApiPort
$remainingWebListener = Get-ListeningProcessId -Port $resolvedWebPort

if ($remainingApiListener -or $remainingWebListener) {
  throw "Some listener processes are still running. API=$remainingApiListener WEB=$remainingWebListener"
}

Remove-Item -LiteralPath $resolvedStateFilePath -Force -ErrorAction SilentlyContinue
Write-Host 'Local stack stop completed.' -ForegroundColor Green
