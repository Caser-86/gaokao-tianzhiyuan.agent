param(
  [string]$ApiBaseUrl = 'http://127.0.0.1:8000',
  [string]$WebBaseUrl = 'http://127.0.0.1:3000',
  [string]$AdminToken = 'dev-admin-token',
  [switch]$SkipAdminCheck,
  [switch]$SkipChatProbe,
  [switch]$SkipWechatProbe,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Add-Type -AssemblyName System.Net.Http

function Assert-True {
  param(
    [Parameter(Mandatory = $true)]
    [bool]$Condition,
    [Parameter(Mandatory = $true)]
    [string]$Message
  )

  if (-not $Condition) {
    throw $Message
  }
}

function Invoke-JsonProbe {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Label,
    [Parameter(Mandatory = $true)]
    [string]$Uri,
    [string]$Method = 'GET',
    [hashtable]$Headers = @{},
    [object]$Body = $null
  )

  Write-Host "==> $Label" -ForegroundColor Cyan
  Write-Host "    $Method $Uri"

  if ($DryRun) {
    return $null
  }

  $invokeArgs = @{
    Uri = $Uri
    Method = $Method
    Headers = $Headers
  }

  if ($null -ne $Body) {
    $invokeArgs['ContentType'] = 'application/json'
    $invokeArgs['Body'] = ($Body | ConvertTo-Json -Depth 8)
  }

  return Invoke-RestMethod @invokeArgs
}

function Invoke-PageProbe {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Label,
    [Parameter(Mandatory = $true)]
    [string]$Uri
  )

  Write-Host "==> $Label" -ForegroundColor Cyan
  Write-Host "    GET $Uri"

  if ($DryRun) {
    return
  }

  $client = [System.Net.Http.HttpClient]::new()
  try {
    $response = $client.GetAsync($Uri).GetAwaiter().GetResult()
    $content = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
  }
  finally {
    $client.Dispose()
  }

  Assert-True ($response.IsSuccessStatusCode) "$Label returned HTTP $([int]$response.StatusCode)"
  Assert-True ($content.Length -gt 0) "$Label returned an empty response body"
}

$normalizedApiBaseUrl = $ApiBaseUrl.TrimEnd('/')
$normalizedWebBaseUrl = $WebBaseUrl.TrimEnd('/')
$adminHeaders = @{
  'X-Admin-Token' = $AdminToken
}

$apiHealth = Invoke-JsonProbe -Label 'API health check' -Uri "$normalizedApiBaseUrl/health"
if (-not $DryRun) {
  Assert-True ($apiHealth.status -eq 'ok') 'API health check did not return status=ok'
}

$chatHealth = Invoke-JsonProbe -Label 'Chat health check' -Uri "$normalizedApiBaseUrl/api/chat/health"
if (-not $DryRun) {
  Assert-True ($chatHealth.status -eq 'ok') 'Chat health check did not return status=ok'
}

$skills = Invoke-JsonProbe -Label 'Chat skills listing' -Uri "$normalizedApiBaseUrl/api/chat/skills"
if (-not $DryRun) {
  Assert-True ($skills.items.Count -ge 1) 'Chat skills listing returned no skills'
  $skillIds = @($skills.items | ForEach-Object { $_.skill_id })
  Assert-True ($skillIds -contains 'zhangxuefeng') 'Chat skills listing did not include zhangxuefeng'
}

Invoke-PageProbe -Label 'Web homepage' -Uri "$normalizedWebBaseUrl/"
Invoke-PageProbe -Label 'Web chat page' -Uri "$normalizedWebBaseUrl/chat"
Invoke-PageProbe -Label 'Web admin page' -Uri "$normalizedWebBaseUrl/admin"

if (-not $SkipAdminCheck) {
  $smartAnalysisSettings = Invoke-JsonProbe `
    -Label 'Admin smart-analysis settings' `
    -Uri "$normalizedApiBaseUrl/api/admin/smart-analysis/settings" `
    -Headers $adminHeaders

  if (-not $DryRun) {
    $validModes = @('off', 'gated', 'on')
    Assert-True ($validModes -contains $smartAnalysisSettings.mode) 'Admin smart-analysis settings returned an invalid mode'
  }
}

if (-not $SkipChatProbe) {
  $chatResponse = Invoke-JsonProbe `
    -Label 'Web chat message probe' `
    -Uri "$normalizedApiBaseUrl/api/chat/messages" `
    -Method 'POST' `
    -Body @{
      channel = 'web'
      user_id = 'smoke-web-user'
      message = 'Please suggest Jiangsu target schools.'
      metadata = @{
        source = 'smoke_local_stack'
        smart_analysis_mode = 'off'
      }
    }

  if (-not $DryRun) {
    Assert-True ($chatResponse.channel -eq 'web') 'Web chat probe returned an unexpected channel'
    Assert-True ($chatResponse.request_id -like 'chat_*') 'Web chat probe did not return a chat request id'
    Assert-True ($chatResponse.output.type -eq 'structured_json') 'Web chat probe did not return structured_json output'
  }
}

if (-not $SkipWechatProbe) {
  $wechatResponse = Invoke-JsonProbe `
    -Label 'WeChat adapter probe' `
    -Uri "$normalizedApiBaseUrl/api/chat/channels/wechat" `
    -Method 'POST' `
    -Body @{
      openid = 'smoke-wechat-user'
      message = 'Henan 560, what major should I choose?'
      message_type = 'text'
      metadata = @{
        source = 'smoke_local_stack'
        smart_analysis_mode = 'off'
      }
    }

  if (-not $DryRun) {
    Assert-True ($wechatResponse.channel -eq 'wechat') 'WeChat probe returned an unexpected channel'
    Assert-True ($wechatResponse.request_id -like 'chat_*') 'WeChat probe did not return a chat request id'
    Assert-True ($wechatResponse.output.type -eq 'structured_json') 'WeChat probe did not return structured_json output'
  }
}

Write-Host 'Local stack smoke test completed.' -ForegroundColor Green
