param(
  [string]$ApiBaseUrl = 'http://127.0.0.1:8000',
  [string]$WebBaseUrl = 'http://127.0.0.1:3000',
  [string]$AdminToken = '',
  [string]$WechatOfficialAccountToken = '',
  [string]$WechatOfficialAccountAppId = '',
  [string]$WechatOfficialAccountEncodingAesKey = '',
  [string]$ApiEnvFilePath = '',
  [string[]]$RequiredSkillIds = @('zhangxuefeng', 'catalog_lookup'),
  [switch]$SkipAdminCheck,
  [switch]$SkipChatProbe,
  [switch]$SkipWechatProbe,
  [switch]$SkipWechatOfficialAccountProbe,
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
  $node = $document.SelectSingleNode("/xml/$ElementName")
  if ($null -eq $node) {
    throw "Missing WeChat XML element: $ElementName"
  }
  $value = $node.InnerText
  if ($null -eq $value) {
    return ''
  }
  return $value.Trim()
}

function Invoke-WechatOfficialAccountProbe {
  param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl,
    [Parameter(Mandatory = $true)]
    [string]$Token,
    [Parameter(Mandatory = $true)]
    [string]$AppId,
    [Parameter(Mandatory = $true)]
    [string]$EncodingAesKey
  )

  $timestamp = '1710000000'
  $nonce = 'smoke-nonce-1'
  $echostr = 'smoke-echo'
  $signature = Get-WechatSignature -Token $Token -Timestamp $timestamp -Nonce $nonce
  $verifyUri = "$BaseUrl/api/chat/channels/wechat/official-account?signature=$signature&timestamp=$timestamp&nonce=$nonce&echostr=$echostr"

  Write-Host '==> WeChat official account verify probe' -ForegroundColor Cyan
  Write-Host "    GET $verifyUri"

  if ($DryRun) {
    return
  }

  $postUri = "$BaseUrl/api/chat/channels/wechat/official-account?signature=$signature&timestamp=$timestamp&nonce=$nonce"
  $xmlBody = @"
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
  $scanBody = @"
<xml>
  <ToUserName><![CDATA[gh_smoke]]></ToUserName>
  <FromUserName><![CDATA[smoke-scan-user]]></FromUserName>
  <CreateTime>1710000004</CreateTime>
  <MsgType><![CDATA[event]]></MsgType>
  <Event><![CDATA[scancode_push]]></Event>
  <EventKey><![CDATA[menu_scan_code]]></EventKey>
  <ScanCodeInfo>
    <ScanType><![CDATA[qrcode]]></ScanType>
    <ScanResult><![CDATA[https://example.com/smoke-scan]]></ScanResult>
  </ScanCodeInfo>
</xml>
"@
  $pictureBody = @"
<xml>
  <ToUserName><![CDATA[gh_smoke]]></ToUserName>
  <FromUserName><![CDATA[smoke-picture-user]]></FromUserName>
  <CreateTime>1710000005</CreateTime>
  <MsgType><![CDATA[event]]></MsgType>
  <Event><![CDATA[pic_photo_or_album]]></Event>
  <EventKey><![CDATA[menu_upload_picture]]></EventKey>
  <SendPicsInfo>
    <Count>2</Count>
    <PicList>
      <item><PicMd5Sum><![CDATA[pic-md5-1]]></PicMd5Sum></item>
      <item><PicMd5Sum><![CDATA[pic-md5-2]]></PicMd5Sum></item>
    </PicList>
  </SendPicsInfo>
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

  $client = [System.Net.Http.HttpClient]::new()
  try {
    $verifyResponse = $client.GetAsync($verifyUri).GetAwaiter().GetResult()
    $verifyContent = $verifyResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    Assert-True ($verifyResponse.IsSuccessStatusCode) 'WeChat official account verify probe returned non-200'
    Assert-True (($verifyContent.Trim()) -eq $echostr) 'WeChat official account verify probe returned an unexpected echostr'

    Write-Host '==> WeChat official account message probe' -ForegroundColor Cyan
    Write-Host "    POST $postUri"
    $requestContent = [System.Net.Http.StringContent]::new(
      $xmlBody,
      [System.Text.Encoding]::UTF8,
      'application/xml'
    )
    try {
      $postResponse = $client.PostAsync($postUri, $requestContent).GetAwaiter().GetResult()
    }
    finally {
      $requestContent.Dispose()
    }
    $postContent = $postResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    Assert-True ($postResponse.IsSuccessStatusCode) 'WeChat official account message probe returned non-200'
    Assert-True ($postContent -match '<ToUserName><!\[CDATA\[smoke-openid\]\]></ToUserName>') 'WeChat official account probe did not swap reply identity fields'
    Assert-True ($postContent -match '<MsgType><!\[CDATA\[text\]\]></MsgType>') 'WeChat official account probe did not return a text passive reply'

    Write-Host '==> WeChat official account subscribe probe' -ForegroundColor Cyan
    Write-Host "    POST $postUri"
    $subscribeRequestContent = [System.Net.Http.StringContent]::new(
      $subscribeBody,
      [System.Text.Encoding]::UTF8,
      'application/xml'
    )
    try {
      $subscribeResponse = $client.PostAsync($postUri, $subscribeRequestContent).GetAwaiter().GetResult()
    }
    finally {
      $subscribeRequestContent.Dispose()
    }
    $subscribeContent = $subscribeResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    Assert-True ($subscribeResponse.IsSuccessStatusCode) 'WeChat official account subscribe probe returned non-200'
    Assert-True ($subscribeContent -match '<ToUserName><!\[CDATA\[smoke-subscriber\]\]></ToUserName>') 'WeChat official account subscribe probe did not target the subscriber'
    Assert-True ($subscribeContent -match 'Agent') 'WeChat official account subscribe probe did not return the welcome reply'

    Write-Host '==> WeChat official account menu click probe' -ForegroundColor Cyan
    Write-Host "    POST $postUri"
    $clickRequestContent = [System.Net.Http.StringContent]::new(
      $clickBody,
      [System.Text.Encoding]::UTF8,
      'application/xml'
    )
    try {
      $clickResponse = $client.PostAsync($postUri, $clickRequestContent).GetAwaiter().GetResult()
    }
    finally {
      $clickRequestContent.Dispose()
    }
    $clickContent = $clickResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    Assert-True ($clickResponse.IsSuccessStatusCode) 'WeChat official account menu click probe returned non-200'
    Assert-True ($clickContent -match '<ToUserName><!\[CDATA\[smoke-menu-user\]\]></ToUserName>') 'WeChat official account menu click probe did not target the menu user'
    Assert-True ($clickContent -match '<MsgType><!\[CDATA\[text\]\]></MsgType>') 'WeChat official account menu click probe did not return a text passive reply'

    Write-Host '==> WeChat official account scan event probe' -ForegroundColor Cyan
    Write-Host "    POST $postUri"
    $scanRequestContent = [System.Net.Http.StringContent]::new(
      $scanBody,
      [System.Text.Encoding]::UTF8,
      'application/xml'
    )
    try {
      $scanResponse = $client.PostAsync($postUri, $scanRequestContent).GetAwaiter().GetResult()
    }
    finally {
      $scanRequestContent.Dispose()
    }
    $scanContent = $scanResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    Assert-True ($scanResponse.IsSuccessStatusCode) 'WeChat official account scan event probe returned non-200'
    Assert-True ($scanContent -match '<ToUserName><!\[CDATA\[smoke-scan-user\]\]></ToUserName>') 'WeChat official account scan event probe did not target the scan user'
    Assert-True ($scanContent -match '<MsgType><!\[CDATA\[text\]\]></MsgType>') 'WeChat official account scan event probe did not return a text passive reply'

    Write-Host '==> WeChat official account picture event probe' -ForegroundColor Cyan
    Write-Host "    POST $postUri"
    $pictureRequestContent = [System.Net.Http.StringContent]::new(
      $pictureBody,
      [System.Text.Encoding]::UTF8,
      'application/xml'
    )
    try {
      $pictureResponse = $client.PostAsync($postUri, $pictureRequestContent).GetAwaiter().GetResult()
    }
    finally {
      $pictureRequestContent.Dispose()
    }
    $pictureContent = $pictureResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    Assert-True ($pictureResponse.IsSuccessStatusCode) 'WeChat official account picture event probe returned non-200'
    Assert-True ($pictureContent -match '<ToUserName><!\[CDATA\[smoke-picture-user\]\]></ToUserName>') 'WeChat official account picture event probe did not target the picture user'
    Assert-True ($pictureContent -match '2') 'WeChat official account picture event probe did not include the picture count guidance'

    Write-Host '==> WeChat official account direct image probe' -ForegroundColor Cyan
    Write-Host "    POST $postUri"
    $directImageRequestContent = [System.Net.Http.StringContent]::new(
      $directImageBody,
      [System.Text.Encoding]::UTF8,
      'application/xml'
    )
    try {
      $directImageResponse = $client.PostAsync($postUri, $directImageRequestContent).GetAwaiter().GetResult()
    }
    finally {
      $directImageRequestContent.Dispose()
    }
    $directImageContent = $directImageResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    Assert-True ($directImageResponse.IsSuccessStatusCode) 'WeChat official account direct image probe returned non-200'
    Assert-True ($directImageContent -match '<ToUserName><!\[CDATA\[smoke-direct-image-user\]\]></ToUserName>') 'WeChat official account direct image probe did not target the direct image user'
    Assert-True ($directImageContent -match '<MsgType><!\[CDATA\[text\]\]></MsgType>') 'WeChat official account direct image probe did not return a text passive reply'

    Write-Host '==> WeChat official account video message probe' -ForegroundColor Cyan
    Write-Host "    POST $postUri"
    $videoRequestContent = [System.Net.Http.StringContent]::new(
      $videoBody,
      [System.Text.Encoding]::UTF8,
      'application/xml'
    )
    try {
      $videoResponse = $client.PostAsync($postUri, $videoRequestContent).GetAwaiter().GetResult()
    }
    finally {
      $videoRequestContent.Dispose()
    }
    $videoContent = $videoResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    Assert-True ($videoResponse.IsSuccessStatusCode) 'WeChat official account video message probe returned non-200'
    Assert-True ($videoContent -match '<ToUserName><!\[CDATA\[smoke-video-user\]\]></ToUserName>') 'WeChat official account video message probe did not target the video user'
    Assert-True ($videoContent -match '<MsgType><!\[CDATA\[text\]\]></MsgType>') 'WeChat official account video message probe did not return a text passive reply'

    Write-Host '==> WeChat official account voice message probe' -ForegroundColor Cyan
    Write-Host "    POST $postUri"
    $voiceRequestContent = [System.Net.Http.StringContent]::new(
      $voiceBody,
      [System.Text.Encoding]::UTF8,
      'application/xml'
    )
    try {
      $voiceResponse = $client.PostAsync($postUri, $voiceRequestContent).GetAwaiter().GetResult()
    }
    finally {
      $voiceRequestContent.Dispose()
    }
    $voiceContent = $voiceResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    Assert-True ($voiceResponse.IsSuccessStatusCode) 'WeChat official account voice message probe returned non-200'
    Assert-True ($voiceContent -match '<ToUserName><!\[CDATA\[smoke-voice-user\]\]></ToUserName>') 'WeChat official account voice message probe did not target the voice user'
    Assert-True ($voiceContent -match '<MsgType><!\[CDATA\[text\]\]></MsgType>') 'WeChat official account voice message probe did not return a text passive reply'

    Write-Host '==> WeChat official account location message probe' -ForegroundColor Cyan
    Write-Host "    POST $postUri"
    $locationRequestContent = [System.Net.Http.StringContent]::new(
      $locationBody,
      [System.Text.Encoding]::UTF8,
      'application/xml'
    )
    try {
      $locationResponse = $client.PostAsync($postUri, $locationRequestContent).GetAwaiter().GetResult()
    }
    finally {
      $locationRequestContent.Dispose()
    }
    $locationContent = $locationResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    Assert-True ($locationResponse.IsSuccessStatusCode) 'WeChat official account location message probe returned non-200'
    Assert-True ($locationContent -match '<ToUserName><!\[CDATA\[smoke-location-user\]\]></ToUserName>') 'WeChat official account location message probe did not target the location user'
    Assert-True ($locationContent -match '<MsgType><!\[CDATA\[text\]\]></MsgType>') 'WeChat official account location message probe did not return a text passive reply'

    Write-Host '==> WeChat official account link message probe' -ForegroundColor Cyan
    Write-Host "    POST $postUri"
    $linkRequestContent = [System.Net.Http.StringContent]::new(
      $linkBody,
      [System.Text.Encoding]::UTF8,
      'application/xml'
    )
    try {
      $linkResponse = $client.PostAsync($postUri, $linkRequestContent).GetAwaiter().GetResult()
    }
    finally {
      $linkRequestContent.Dispose()
    }
    $linkContent = $linkResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    Assert-True ($linkResponse.IsSuccessStatusCode) 'WeChat official account link message probe returned non-200'
    Assert-True ($linkContent -match '<ToUserName><!\[CDATA\[smoke-link-user\]\]></ToUserName>') 'WeChat official account link message probe did not target the link user'
    Assert-True ($linkContent -match '<MsgType><!\[CDATA\[text\]\]></MsgType>') 'WeChat official account link message probe did not return a text passive reply'

    $aesVerifyNonce = 'smoke-aes-nonce-1'
    $aesEchostrPlaintext = 'smoke-echo-aes'
    $aesEchostrEncrypted = Protect-WechatMessage `
      -Plaintext $aesEchostrPlaintext `
      -AppId $AppId `
      -EncodingAesKey $EncodingAesKey
    $aesVerifySignature = Get-WechatMsgSignature `
      -Token $Token `
      -Timestamp $timestamp `
      -Nonce $aesVerifyNonce `
      -Encrypted $aesEchostrEncrypted
    $aesVerifyUri = "$BaseUrl/api/chat/channels/wechat/official-account?msg_signature=$aesVerifySignature&timestamp=$timestamp&nonce=$aesVerifyNonce&echostr=$([System.Uri]::EscapeDataString($aesEchostrEncrypted))&encrypt_type=aes"

    Write-Host '==> WeChat official account AES verify probe' -ForegroundColor Cyan
    Write-Host "    GET $aesVerifyUri"
    $aesVerifyResponse = $client.GetAsync($aesVerifyUri).GetAwaiter().GetResult()
    $aesVerifyContent = $aesVerifyResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    Assert-True ($aesVerifyResponse.IsSuccessStatusCode) 'WeChat official account AES verify probe returned non-200'
    Assert-True (($aesVerifyContent.Trim()) -eq $aesEchostrPlaintext) 'WeChat official account AES verify probe returned an unexpected echostr'

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
      -AppId $AppId `
      -EncodingAesKey $EncodingAesKey
    $aesMessageNonce = 'smoke-aes-nonce-2'
    $aesMessageSignature = Get-WechatMsgSignature `
      -Token $Token `
      -Timestamp $timestamp `
      -Nonce $aesMessageNonce `
      -Encrypted $aesEncryptedBody
    $aesPostUri = "$BaseUrl/api/chat/channels/wechat/official-account?msg_signature=$aesMessageSignature&timestamp=$timestamp&nonce=$aesMessageNonce&encrypt_type=aes"
    $aesOuterBody = @"
<xml>
  <ToUserName><![CDATA[gh_smoke]]></ToUserName>
  <Encrypt><![CDATA[$aesEncryptedBody]]></Encrypt>
</xml>
"@

    Write-Host '==> WeChat official account AES message probe' -ForegroundColor Cyan
    Write-Host "    POST $aesPostUri"
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
    Assert-True ($aesResponse.IsSuccessStatusCode) 'WeChat official account AES message probe returned non-200'
    $responseEncrypted = Get-WechatXmlValue -Xml $aesResponseContent -ElementName 'Encrypt'
    $responseMsgSignature = Get-WechatXmlValue -Xml $aesResponseContent -ElementName 'MsgSignature'
    $responseTimestamp = Get-WechatXmlValue -Xml $aesResponseContent -ElementName 'TimeStamp'
    $responseNonce = Get-WechatXmlValue -Xml $aesResponseContent -ElementName 'Nonce'
    $expectedResponseSignature = Get-WechatMsgSignature `
      -Token $Token `
      -Timestamp $responseTimestamp `
      -Nonce $responseNonce `
      -Encrypted $responseEncrypted
    Assert-True ($responseMsgSignature -eq $expectedResponseSignature) 'WeChat official account AES message probe returned an invalid msg_signature'
    $decryptedResponse = Unprotect-WechatMessage `
      -Encrypted $responseEncrypted `
      -AppId $AppId `
      -EncodingAesKey $EncodingAesKey
    Assert-True ($decryptedResponse -match '<ToUserName><!\[CDATA\[smoke-aes-user\]\]></ToUserName>') 'WeChat official account AES message probe did not target the AES user'
    Assert-True ($decryptedResponse -match '<MsgType><!\[CDATA\[text\]\]></MsgType>') 'WeChat official account AES message probe did not return a text passive reply'
  }
  finally {
    $client.Dispose()
  }
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
$effectiveAdminToken = Resolve-SettingValue `
  -ExplicitValue $AdminToken `
  -EnvMaps @($apiEnvValues) `
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

$normalizedApiBaseUrl = $ApiBaseUrl.TrimEnd('/')
$normalizedWebBaseUrl = $WebBaseUrl.TrimEnd('/')
$adminHeaders = @{
  'X-Admin-Token' = $effectiveAdminToken
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
  foreach ($requiredSkillId in $RequiredSkillIds) {
    Assert-True ($skillIds -contains $requiredSkillId) "Chat skills listing did not include $requiredSkillId"
  }
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

if (-not $SkipWechatOfficialAccountProbe) {
  Invoke-WechatOfficialAccountProbe `
    -BaseUrl $normalizedApiBaseUrl `
    -Token $effectiveWechatOfficialAccountToken `
    -AppId $effectiveWechatOfficialAccountAppId `
    -EncodingAesKey $effectiveWechatOfficialAccountEncodingAesKey
}

Write-Host 'Local stack smoke test completed.' -ForegroundColor Green
