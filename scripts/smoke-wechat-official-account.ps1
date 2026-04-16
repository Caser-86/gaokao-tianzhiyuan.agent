param(
  [string]$ApiBaseUrl = 'http://127.0.0.1:8000',
  [string]$WechatOfficialAccountToken = '',
  [string]$WechatOfficialAccountAppId = '',
  [string]$WechatOfficialAccountEncodingAesKey = '',
  [string]$ApiEnvFilePath = '',
  [switch]$SkipPlaintextProbes,
  [switch]$SkipAesProbes,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Add-Type -AssemblyName System.Net.Http

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')

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

function Get-WechatSignature {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Token,
    [Parameter(Mandatory = $true)]
    [string]$Timestamp,
    [Parameter(Mandatory = $true)]
    [string]$Nonce
  )

  $sorted = @($Token, $Timestamp, $Nonce) | Sort-Object
  $payload = [string]::Concat($sorted)
  $sha1 = [System.Security.Cryptography.SHA1]::Create()
  try {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
    $hash = $sha1.ComputeHash($bytes)
    return ([System.BitConverter]::ToString($hash)).Replace('-', '').ToLowerInvariant()
  }
  finally {
    $sha1.Dispose()
  }
}

function Get-WechatMsgSignature {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Token,
    [Parameter(Mandatory = $true)]
    [string]$Timestamp,
    [Parameter(Mandatory = $true)]
    [string]$Nonce,
    [Parameter(Mandatory = $true)]
    [string]$Encrypted
  )

  $helperPath = Join-Path $repoRoot 'scripts/wechat_aes_helper.py'
  $output = & python $helperPath sign --value $Encrypted --token $Token --timestamp $Timestamp --nonce $Nonce
  if ($LASTEXITCODE -ne 0) {
    throw "WeChat AES helper failed while running 'sign'."
  }
  return ($output | Out-String).Trim()
}

function Invoke-WechatCryptoHelper {
  param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('encrypt', 'decrypt')]
    [string]$Operation,
    [Parameter(Mandatory = $true)]
    [string]$Value,
    [Parameter(Mandatory = $true)]
    [string]$AppId,
    [Parameter(Mandatory = $true)]
    [string]$EncodingAesKey
  )

  $helperPath = Join-Path $repoRoot 'scripts/wechat_aes_helper.py'
  $output = & python $helperPath $Operation --value $Value --app-id $AppId --encoding-aes-key $EncodingAesKey
  if ($LASTEXITCODE -ne 0) {
    throw "WeChat AES helper failed while running '$Operation'."
  }
  return ($output | Out-String).Trim()
}

function Protect-WechatMessage {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Plaintext,
    [Parameter(Mandatory = $true)]
    [string]$AppId,
    [Parameter(Mandatory = $true)]
    [string]$EncodingAesKey
  )

  return Invoke-WechatCryptoHelper `
    -Operation 'encrypt' `
    -Value $Plaintext `
    -AppId $AppId `
    -EncodingAesKey $EncodingAesKey
}

function Unprotect-WechatMessage {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Encrypted,
    [Parameter(Mandatory = $true)]
    [string]$AppId,
    [Parameter(Mandatory = $true)]
    [string]$EncodingAesKey
  )

  return Invoke-WechatCryptoHelper `
    -Operation 'decrypt' `
    -Value $Encrypted `
    -AppId $AppId `
    -EncodingAesKey $EncodingAesKey
}

function Get-WechatXmlValue {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Xml,
    [Parameter(Mandatory = $true)]
    [string]$ElementName
  )

  $document = New-Object System.Xml.XmlDocument
  $document.LoadXml($Xml)
  $node = $document.SelectSingleNode("//$ElementName")
  if ($null -eq $node) {
    throw "Missing XML element: $ElementName"
  }

  return $node.InnerText
}

function Invoke-WechatXmlPostProbe {
  param(
    [Parameter(Mandatory = $true)]
    [System.Net.Http.HttpClient]$Client,
    [Parameter(Mandatory = $true)]
    [string]$Label,
    [Parameter(Mandatory = $true)]
    [string]$Uri,
    [Parameter(Mandatory = $true)]
    [string]$Body
  )

  Write-Host "==> $Label" -ForegroundColor Cyan
  Write-Host "    POST $Uri"

  if ($DryRun) {
    return ''
  }

  $requestContent = [System.Net.Http.StringContent]::new(
    $Body,
    [System.Text.Encoding]::UTF8,
    'application/xml'
  )
  try {
    $response = $Client.PostAsync($Uri, $requestContent).GetAwaiter().GetResult()
  }
  finally {
    $requestContent.Dispose()
  }

  $content = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
  Assert-True ($response.IsSuccessStatusCode) "$Label returned non-200"
  return $content
}

$defaultApiEnvPath = Join-Path $repoRoot 'apps/api/.env'
$resolvedApiEnvFilePath = if (-not [string]::IsNullOrWhiteSpace($ApiEnvFilePath)) {
  (Resolve-Path -LiteralPath $ApiEnvFilePath -ErrorAction Stop).Path
}
elseif (Test-Path -LiteralPath $defaultApiEnvPath) {
  (Resolve-Path -LiteralPath $defaultApiEnvPath).Path
}
else {
  ''
}
$apiEnvValues = Read-EnvFile -Path $resolvedApiEnvFilePath
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

Write-Host '==> WeChat official account smoke plan' -ForegroundColor Cyan
Write-Host "API base URL: $($ApiBaseUrl.TrimEnd('/'))"
Write-Host "API env file: $(if ($resolvedApiEnvFilePath) { $resolvedApiEnvFilePath } else { '(not found)' })"
Write-Host "WeChat callback token: $(Get-MaskedValue -Value $effectiveWechatOfficialAccountToken)"
Write-Host "WeChat app id: $effectiveWechatOfficialAccountAppId"
Write-Host "WeChat AES key configured: $((-not [string]::IsNullOrWhiteSpace($effectiveWechatOfficialAccountEncodingAesKey)).ToString())"
Write-Host "Skip plaintext probes: $($SkipPlaintextProbes.ToString())"
Write-Host "Skip AES probes: $($SkipAesProbes.ToString())"

if ($SkipPlaintextProbes -and $SkipAesProbes) {
  Write-Host 'No probe category enabled. Nothing to do.' -ForegroundColor Yellow
  return
}

$normalizedApiBaseUrl = $ApiBaseUrl.TrimEnd('/')
$timestamp = '1710000000'
$plaintextNonce = 'smoke-nonce-1'
$plaintextSignature = Get-WechatSignature `
  -Token $effectiveWechatOfficialAccountToken `
  -Timestamp $timestamp `
  -Nonce $plaintextNonce
$plaintextPostUri = "$normalizedApiBaseUrl/api/chat/channels/wechat/official-account?signature=$plaintextSignature&timestamp=$timestamp&nonce=$plaintextNonce"

$client = [System.Net.Http.HttpClient]::new()
try {
  if (-not $SkipPlaintextProbes) {
    $echostr = 'smoke-echo'
    $verifyUri = "$plaintextPostUri&echostr=$echostr"
    Write-Host '==> WeChat official account verify probe' -ForegroundColor Cyan
    Write-Host "    GET $verifyUri"
    if (-not $DryRun) {
      $verifyResponse = $client.GetAsync($verifyUri).GetAwaiter().GetResult()
      $verifyContent = $verifyResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
      Assert-True ($verifyResponse.IsSuccessStatusCode) 'WeChat official account verify probe returned non-200'
      Assert-True (($verifyContent.Trim()) -eq $echostr) 'WeChat official account verify probe returned an unexpected echostr'
    }

    $textBody = @"
<xml>
  <ToUserName><![CDATA[gh_smoke]]></ToUserName>
  <FromUserName><![CDATA[smoke-openid]]></FromUserName>
  <CreateTime>1710000001</CreateTime>
  <MsgType><![CDATA[text]]></MsgType>
  <Content><![CDATA[Smoke test question]]></Content>
  <MsgId>1234567890</MsgId>
</xml>
"@
    $subscribeBody = @"
<xml>
  <ToUserName><![CDATA[gh_smoke]]></ToUserName>
  <FromUserName><![CDATA[smoke-subscriber]]></FromUserName>
  <CreateTime>1710000002</CreateTime>
  <MsgType><![CDATA[event]]></MsgType>
  <Event><![CDATA[subscribe]]></Event>
</xml>
"@
    $clickBody = @"
<xml>
  <ToUserName><![CDATA[gh_smoke]]></ToUserName>
  <FromUserName><![CDATA[smoke-menu-user]]></FromUserName>
  <CreateTime>1710000003</CreateTime>
  <MsgType><![CDATA[event]]></MsgType>
  <Event><![CDATA[CLICK]]></Event>
  <EventKey><![CDATA[menu_usage_help]]></EventKey>
</xml>
"@
    $directImageBody = @"
<xml>
  <ToUserName><![CDATA[gh_smoke]]></ToUserName>
  <FromUserName><![CDATA[smoke-direct-image-user]]></FromUserName>
  <CreateTime>1710000005</CreateTime>
  <MsgType><![CDATA[image]]></MsgType>
  <PicUrl><![CDATA[https://example.com/direct-image.png]]></PicUrl>
  <MediaId><![CDATA[direct-image-media-1]]></MediaId>
  <MsgId>2234567891</MsgId>
</xml>
"@
    $videoBody = @"
<xml>
  <ToUserName><![CDATA[gh_smoke]]></ToUserName>
  <FromUserName><![CDATA[smoke-video-user]]></FromUserName>
  <CreateTime>1710000005</CreateTime>
  <MsgType><![CDATA[video]]></MsgType>
  <MediaId><![CDATA[video-media-1]]></MediaId>
  <ThumbMediaId><![CDATA[video-thumb-1]]></ThumbMediaId>
  <MsgId>2234567892</MsgId>
</xml>
"@
    $voiceBody = @"
<xml>
  <ToUserName><![CDATA[gh_smoke]]></ToUserName>
  <FromUserName><![CDATA[smoke-voice-user]]></FromUserName>
  <CreateTime>1710000006</CreateTime>
  <MsgType><![CDATA[voice]]></MsgType>
  <MediaId><![CDATA[voice-media-1]]></MediaId>
  <Format><![CDATA[amr]]></Format>
  <Recognition><![CDATA[Henan 560 recommend majors]]></Recognition>
  <MsgId>3234567890</MsgId>
</xml>
"@
    $locationBody = @"
<xml>
  <ToUserName><![CDATA[gh_smoke]]></ToUserName>
  <FromUserName><![CDATA[smoke-location-user]]></FromUserName>
  <CreateTime>1710000007</CreateTime>
  <MsgType><![CDATA[location]]></MsgType>
  <Location_X>39.984154</Location_X>
  <Location_Y>116.307490</Location_Y>
  <Scale>15</Scale>
  <Label><![CDATA[Beijing Haidian District]]></Label>
  <MsgId>4234567893</MsgId>
</xml>
"@
    $linkBody = @"
<xml>
  <ToUserName><![CDATA[gh_smoke]]></ToUserName>
  <FromUserName><![CDATA[smoke-link-user]]></FromUserName>
  <CreateTime>1710000008</CreateTime>
  <MsgType><![CDATA[link]]></MsgType>
  <Title><![CDATA[Henan admission report]]></Title>
  <Description><![CDATA[2025 analysis report]]></Description>
  <Url><![CDATA[https://example.com/report]]></Url>
  <MsgId>4234567894</MsgId>
</xml>
"@

    $textContent = Invoke-WechatXmlPostProbe -Client $client -Label 'WeChat official account text probe' -Uri $plaintextPostUri -Body $textBody
    if (-not $DryRun) {
      Assert-True ($textContent -match '<ToUserName><!\[CDATA\[smoke-openid\]\]></ToUserName>') 'WeChat official account text probe did not target the text user'
      Assert-True ($textContent -match '<MsgType><!\[CDATA\[text\]\]></MsgType>') 'WeChat official account text probe did not return a text passive reply'
    }

    $subscribeContent = Invoke-WechatXmlPostProbe -Client $client -Label 'WeChat official account subscribe probe' -Uri $plaintextPostUri -Body $subscribeBody
    if (-not $DryRun) {
      Assert-True ($subscribeContent -match '<ToUserName><!\[CDATA\[smoke-subscriber\]\]></ToUserName>') 'WeChat official account subscribe probe did not target the subscriber'
      Assert-True ($subscribeContent -match 'Agent') 'WeChat official account subscribe probe did not return the welcome reply'
    }

    $clickContent = Invoke-WechatXmlPostProbe -Client $client -Label 'WeChat official account click probe' -Uri $plaintextPostUri -Body $clickBody
    if (-not $DryRun) {
      Assert-True ($clickContent -match '<ToUserName><!\[CDATA\[smoke-menu-user\]\]></ToUserName>') 'WeChat official account click probe did not target the menu user'
      Assert-True ($clickContent -match '<MsgType><!\[CDATA\[text\]\]></MsgType>') 'WeChat official account click probe did not return a text passive reply'
    }

    $directImageContent = Invoke-WechatXmlPostProbe -Client $client -Label 'WeChat official account direct image probe' -Uri $plaintextPostUri -Body $directImageBody
    if (-not $DryRun) {
      Assert-True ($directImageContent -match '<ToUserName><!\[CDATA\[smoke-direct-image-user\]\]></ToUserName>') 'WeChat official account direct image probe did not target the image user'
      Assert-True ($directImageContent -match '<MsgType><!\[CDATA\[text\]\]></MsgType>') 'WeChat official account direct image probe did not return a text passive reply'
    }

    $videoContent = Invoke-WechatXmlPostProbe -Client $client -Label 'WeChat official account video probe' -Uri $plaintextPostUri -Body $videoBody
    if (-not $DryRun) {
      Assert-True ($videoContent -match '<ToUserName><!\[CDATA\[smoke-video-user\]\]></ToUserName>') 'WeChat official account video probe did not target the video user'
      Assert-True ($videoContent -match '<MsgType><!\[CDATA\[text\]\]></MsgType>') 'WeChat official account video probe did not return a text passive reply'
    }

    $voiceContent = Invoke-WechatXmlPostProbe -Client $client -Label 'WeChat official account voice probe' -Uri $plaintextPostUri -Body $voiceBody
    if (-not $DryRun) {
      Assert-True ($voiceContent -match '<ToUserName><!\[CDATA\[smoke-voice-user\]\]></ToUserName>') 'WeChat official account voice probe did not target the voice user'
      Assert-True ($voiceContent -match '<MsgType><!\[CDATA\[text\]\]></MsgType>') 'WeChat official account voice probe did not return a text passive reply'
    }

    $locationContent = Invoke-WechatXmlPostProbe -Client $client -Label 'WeChat official account location probe' -Uri $plaintextPostUri -Body $locationBody
    if (-not $DryRun) {
      Assert-True ($locationContent -match '<ToUserName><!\[CDATA\[smoke-location-user\]\]></ToUserName>') 'WeChat official account location probe did not target the location user'
      Assert-True ($locationContent -match '<MsgType><!\[CDATA\[text\]\]></MsgType>') 'WeChat official account location probe did not return a text passive reply'
    }

    $linkContent = Invoke-WechatXmlPostProbe -Client $client -Label 'WeChat official account link probe' -Uri $plaintextPostUri -Body $linkBody
    if (-not $DryRun) {
      Assert-True ($linkContent -match '<ToUserName><!\[CDATA\[smoke-link-user\]\]></ToUserName>') 'WeChat official account link probe did not target the link user'
      Assert-True ($linkContent -match '<MsgType><!\[CDATA\[text\]\]></MsgType>') 'WeChat official account link probe did not return a text passive reply'
    }
  }

  if (-not $SkipAesProbes) {
    $aesVerifyNonce = 'smoke-aes-nonce-1'
    $aesEchostrPlaintext = 'smoke-echo-aes'
    $aesEchostrEncrypted = Protect-WechatMessage `
      -Plaintext $aesEchostrPlaintext `
      -AppId $effectiveWechatOfficialAccountAppId `
      -EncodingAesKey $effectiveWechatOfficialAccountEncodingAesKey
    $aesVerifySignature = Get-WechatMsgSignature `
      -Token $effectiveWechatOfficialAccountToken `
      -Timestamp $timestamp `
      -Nonce $aesVerifyNonce `
      -Encrypted $aesEchostrEncrypted
    $aesVerifyUri = "$normalizedApiBaseUrl/api/chat/channels/wechat/official-account?msg_signature=$aesVerifySignature&timestamp=$timestamp&nonce=$aesVerifyNonce&echostr=$([System.Uri]::EscapeDataString($aesEchostrEncrypted))&encrypt_type=aes"

    Write-Host '==> WeChat official account AES verify probe' -ForegroundColor Cyan
    Write-Host "    GET $aesVerifyUri"
    if (-not $DryRun) {
      $aesVerifyResponse = $client.GetAsync($aesVerifyUri).GetAwaiter().GetResult()
      $aesVerifyContent = $aesVerifyResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
      Assert-True ($aesVerifyResponse.IsSuccessStatusCode) 'WeChat official account AES verify probe returned non-200'
      Assert-True (($aesVerifyContent.Trim()) -eq $aesEchostrPlaintext) 'WeChat official account AES verify probe returned an unexpected echostr'
    }

    $aesInnerBody = @"
<xml>
  <ToUserName><![CDATA[gh_smoke]]></ToUserName>
  <FromUserName><![CDATA[smoke-aes-user]]></FromUserName>
  <CreateTime>1710000006</CreateTime>
  <MsgType><![CDATA[text]]></MsgType>
  <Content><![CDATA[Smoke AES test question]]></Content>
  <MsgId>2234567890</MsgId>
</xml>
"@
    $aesEncryptedBody = Protect-WechatMessage `
      -Plaintext $aesInnerBody `
      -AppId $effectiveWechatOfficialAccountAppId `
      -EncodingAesKey $effectiveWechatOfficialAccountEncodingAesKey
    $aesMessageNonce = 'smoke-aes-nonce-2'
    $aesMessageSignature = Get-WechatMsgSignature `
      -Token $effectiveWechatOfficialAccountToken `
      -Timestamp $timestamp `
      -Nonce $aesMessageNonce `
      -Encrypted $aesEncryptedBody
    $aesPostUri = "$normalizedApiBaseUrl/api/chat/channels/wechat/official-account?msg_signature=$aesMessageSignature&timestamp=$timestamp&nonce=$aesMessageNonce&encrypt_type=aes"
    $aesOuterBody = @"
<xml>
  <ToUserName><![CDATA[gh_smoke]]></ToUserName>
  <Encrypt><![CDATA[$aesEncryptedBody]]></Encrypt>
</xml>
"@

    Write-Host '==> WeChat official account AES text probe' -ForegroundColor Cyan
    Write-Host "    POST $aesPostUri"
    if (-not $DryRun) {
      $aesRequestContent = [System.Net.Http.StringContent]::new(
        $aesOuterBody,
        [System.Text.Encoding]::UTF8,
        'application/xml'
      )
      try {
        $aesResponse = $client.PostAsync($aesPostUri, $aesRequestContent).GetAwaiter().GetResult()
      }
      finally {
        $aesRequestContent.Dispose()
      }

      $aesResponseContent = $aesResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
      Assert-True ($aesResponse.IsSuccessStatusCode) 'WeChat official account AES text probe returned non-200'

      $responseEncrypted = Get-WechatXmlValue -Xml $aesResponseContent -ElementName 'Encrypt'
      $responseMsgSignature = Get-WechatXmlValue -Xml $aesResponseContent -ElementName 'MsgSignature'
      $responseTimestamp = Get-WechatXmlValue -Xml $aesResponseContent -ElementName 'TimeStamp'
      $responseNonce = Get-WechatXmlValue -Xml $aesResponseContent -ElementName 'Nonce'
      $expectedResponseSignature = Get-WechatMsgSignature `
        -Token $effectiveWechatOfficialAccountToken `
        -Timestamp $responseTimestamp `
        -Nonce $responseNonce `
        -Encrypted $responseEncrypted
      Assert-True ($responseMsgSignature -eq $expectedResponseSignature) 'WeChat official account AES text probe returned an invalid msg_signature'

      $decryptedResponse = Unprotect-WechatMessage `
        -Encrypted $responseEncrypted `
        -AppId $effectiveWechatOfficialAccountAppId `
        -EncodingAesKey $effectiveWechatOfficialAccountEncodingAesKey
      Assert-True ($decryptedResponse -match '<ToUserName><!\[CDATA\[smoke-aes-user\]\]></ToUserName>') 'WeChat official account AES text probe did not target the AES user'
      Assert-True ($decryptedResponse -match '<MsgType><!\[CDATA\[text\]\]></MsgType>') 'WeChat official account AES text probe did not return a text passive reply'
    }
  }
}
finally {
  $client.Dispose()
}

Write-Host 'WeChat official account smoke completed.' -ForegroundColor Green
