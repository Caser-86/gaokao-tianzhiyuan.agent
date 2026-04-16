# API

Gaokao agent backend service.

## Local setup

Run the API from this directory:

```powershell
cd apps/api
```

Create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Then fill in these fields with your real relay config:

- `GAOKAO_AGENT_LLM_PROVIDER=openai_compatible`
- `GAOKAO_AGENT_LLM_BASE_URL=<your relay base url>`
- `GAOKAO_AGENT_LLM_API_KEY=<your relay api key>`
- `GAOKAO_AGENT_LLM_MODEL=<your model name>`
- `GAOKAO_AGENT_SMART_ANALYSIS_MODE=off`
- `GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_TOKEN=<your wechat callback token>`
- `GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_APP_ID=<your wechat app id>`
- `GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_ENCODING_AES_KEY=<your 43-char aes key>`
- `GAOKAO_AGENT_ZHANGXUEFENG_SKILL_PATH=<optional absolute path to SKILL.md>`

If you want to use the local ZhangXueFeng skill repository, clone it into the workspace root first:

```powershell
git clone https://github.com/alchaincyf/zhangxuefeng-skill.git vendor/zhangxuefeng-skill
```

When `GAOKAO_AGENT_ZHANGXUEFENG_SKILL_PATH` is left blank, the API will automatically try these local paths:

- `vendor/zhangxuefeng-skill/SKILL.md`
- `.tmp/zhangxuefeng-skill/SKILL.md`

Example:

```env
GAOKAO_AGENT_LLM_PROVIDER=openai_compatible
GAOKAO_AGENT_LLM_BASE_URL=https://your-relay.example
GAOKAO_AGENT_LLM_API_KEY=your-relay-api-key
GAOKAO_AGENT_LLM_MODEL=gpt-4o-mini
GAOKAO_AGENT_SMART_ANALYSIS_MODE=off
GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_TOKEN=replace-with-your-wechat-token
GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_APP_ID=wx-replace-with-your-app-id
GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_ENCODING_AES_KEY=replace-with-43-char-encoding-aes-key
GAOKAO_AGENT_ZHANGXUEFENG_SKILL_PATH=
```

## Run the API

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Health check:

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/health
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/api/chat/health
```

## Test the ZhangXueFeng skill

Direct invoke:

```powershell
$body = @{
  channel = "wechat"
  user_id = "wx-local-test"
  message = "河南560分想学金融，靠谱吗？"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/chat/skills/zhangxuefeng/invoke `
  -ContentType "application/json" `
  -Body $body
```

Auto route:

```powershell
$body = @{
  channel = "wechat"
  user_id = "wx-local-test"
  message = "帮我看看江苏适合冲哪些985"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/chat/messages `
  -ContentType "application/json" `
  -Body $body
```

## Behavior notes

- The API now reads `apps/api/.env` automatically on startup.
- If relay config is missing or the model call fails, `zhangxuefeng` falls back to rule-based output instead of crashing the chat gateway.
- The response stays structured JSON so the web app and WeChat adapter can render differently later.

## Smart analysis access control

Smart analysis can be controlled globally with `GAOKAO_AGENT_SMART_ANALYSIS_MODE`:

- `off`: disable model-backed smart analysis for everyone.
- `gated`: allow model-backed smart analysis only for callers with the `smart_analysis` entitlement.
- `on`: allow model-backed smart analysis for everyone.

During the current integration phase, callers can pass entitlements through request metadata:

```json
{
  "metadata": {
    "entitlements": ["smart_analysis"]
  }
}
```

When smart analysis is blocked by policy, the API still returns a normal fallback answer and exposes the reason in `debug.notes`:

- `smart_analysis_disabled_globally`
- `smart_analysis_entitlement_required`

When the relay itself is unavailable, the API also distinguishes technical fallback reasons:

- `provider_not_configured`
- `provider_request_failed`
- `provider_insufficient_balance`
- `provider_invalid_response`

### Admin-managed smart analysis

Smart-analysis policy now has two layers:

- a global runtime mode stored in SQLite
- a per-user `smart_analysis` entitlement stored in SQLite

Bootstrap behavior:

- if no runtime DB row exists yet, the API falls back to `GAOKAO_AGENT_SMART_ANALYSIS_MODE`

Admin operations:

- `GET /api/admin/smart-analysis/settings`
- `PUT /api/admin/smart-analysis/settings`
- `GET /api/admin/smart-analysis/users/{user_id}`
- `PUT /api/admin/smart-analysis/users/{user_id}`
- `GET /api/admin/media-analysis-events?limit=10`
  - optional filters: `status`, `user_id`, `auto_routed_to_chat`
- `POST /api/admin/media-analysis-events/{event_id}/retry`
  - currently retries image records whose persisted `context.pic_url` is available

During the transition period, request `metadata.entitlements` is still accepted, but persisted DB state is preferred when available.

The admin dashboard now also surfaces recent media-analysis records from SQLite. Each record includes the media type, provider, status, summary, rendered reply, extracted fields, raw `context` (message ID, media ID, PicUrl and other retained callback metadata), retryability metadata, and whether the image result auto-routed into the existing gaokao chat flow. The current `/admin` page also supports lightweight filtering by status, user ID, and “auto-routed into main analysis”, plus an inline detail expander for single-record troubleshooting.

## WeChat official account minimal callback

The API now exposes an official account callback endpoint:

- `GET /api/chat/channels/wechat/official-account`
- `POST /api/chat/channels/wechat/official-account`

Setup notes:

- Set `GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_TOKEN` to the same token configured in the WeChat official account backend.
- This placeholder currently supports both plaintext mode and AES safe mode.
- Text messages are forwarded into the existing chat routing flow.
- `subscribe` events return a passive welcome message without entering chat routing.
- `unsubscribe` events return a plain `success` acknowledgement.
- `CLICK` menu events can either return a fixed reply or inject a preset prompt into the existing chat routing flow.
- `scancode_push` and `location_select` menu events can normalize scanned content or chosen location into the existing chat routing flow.
- `image` messages currently return a stable picture-guidance reply; if smart analysis is enabled globally or granted to the user, they can call the media-analysis adapter. Intentionally blank providers still stay on the pending path, while declared-but-broken image analysis now returns an explicit unavailable reply and failed event.
- `video` and `shortvideo` messages currently return a stable video-guidance reply; under `openai_compatible`, unsupported attempts now persist as explicit failed records instead of misleading pending events.
- `voice` messages can reuse the existing chat routing flow when WeChat provides `Recognition` text.
- `location` messages currently normalize the shared label and coordinates into the existing chat routing flow.
- `link` messages currently normalize the shared title, description, and URL into the existing chat routing flow.
- `pic_sysphoto`, `pic_photo_or_album`, and `pic_weixin` currently acknowledge received images and guide the user back to text input.
- AES safe mode is now supported for URL verification and text-message callbacks.
- Other message and event types return a passive text reply that says they are not yet supported.

Behavior notes:

- `GET` is used by WeChat for initial signature verification and returns `echostr` when the signature is valid.
- `POST` accepts WeChat XML, normalizes text messages into the existing `wechat` chat channel, and returns passive reply XML.
- If the token is missing, the endpoint responds with `503` so the callback is not accidentally exposed without verification.
- If the official account backend is set to AES safe mode, also configure:
  - `GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_APP_ID`
  - `GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_ENCODING_AES_KEY`
- In AES mode, the API verifies `msg_signature`, decrypts the callback payload, processes the plain XML, then encrypts the passive reply XML before returning it.
- For local AES troubleshooting, use `scripts/wechat_aes_helper.py` from the repo root:

```powershell
python scripts/wechat_aes_helper.py sign `
  --value "<Encrypt payload>" `
  --token "<wechat token>" `
  --timestamp "1710000000" `
  --nonce "nonce-123"
```

```powershell
python scripts/wechat_aes_helper.py decrypt `
  --value "<Encrypt payload>" `
  --app-id "<wechat app id>" `
  --encoding-aes-key "<43-char aes key>"
```

```powershell
python scripts/wechat_aes_helper.py encrypt `
  --value "<xml>...</xml>" `
  --app-id "<wechat app id>" `
  --encoding-aes-key "<43-char aes key>"
```
- For callback-only acceptance, run the dedicated smoke script:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke-wechat-official-account.ps1 `
  -ApiBaseUrl http://127.0.0.1:8000 `
  -ApiEnvFilePath apps\api\.env
```

For a remote or production-style domain, pass the real callback values
explicitly:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke-wechat-official-account.ps1 `
  -ApiBaseUrl https://your-domain.example `
  -WechatOfficialAccountToken "<wechat token>" `
  -WechatOfficialAccountAppId "<wechat app id>" `
  -WechatOfficialAccountEncodingAesKey "<43-char aes key>"
```
- Media-analysis adapter config is now reserved for future image/video parsing:
  - `GAOKAO_AGENT_MEDIA_ANALYSIS_PROVIDER`
  - `GAOKAO_AGENT_MEDIA_ANALYSIS_BASE_URL`
  - `GAOKAO_AGENT_MEDIA_ANALYSIS_API_KEY`
  - `GAOKAO_AGENT_MEDIA_ANALYSIS_MODEL`
  - `GAOKAO_AGENT_MEDIA_ANALYSIS_TIMEOUT_SECONDS`
- `openai_compatible` media analysis is currently wired for official-account image callbacks that contain `PicUrl`.
- The media-analysis adapter now normalizes provider output into `summary`, `extracted_fields`, and `rendered_reply`; if `rendered_reply` is absent but `summary` exists, the callback still replies with the extracted summary.
- If `extracted_fields` contains enough admission-planning context, the official-account image callback can now synthesize a normalized gaokao analysis prompt and route it into the existing chat flow automatically.
- Admins can manually retry a stored image-analysis record from the dashboard; the retry creates a new `admin_media_analysis_retry` event so the original record remains unchanged.
- Failed media-analysis requests now persist a readable `context.failure_reason`, and `/admin` surfaces that reason directly in each media-analysis card for troubleshooting.
- `/admin` now marks whether each media-analysis record is retryable. Non-image records and image records missing `pic_url` stay visible, but the dashboard shows a readable block reason instead of a misleading retry button.
- If no media-analysis provider is configured, enabled users still receive the reserved "media analysis pending integration" reply.
- If `openai_compatible` is selected but `BASE_URL / API_KEY / MODEL` are incomplete, image analysis now returns an explicit failed result with a readable configuration reason.
- If image media analysis explicitly fails after invocation, the callback now returns an "image analysis temporarily unavailable" reply instead of the generic pending-integration text.
- `scripts/start-local-stack.ps1 -RunSmoke` now injects default AES local values and verifies both plaintext and AES callback flows.

Default menu keys:

- `menu_usage_help`: return a short usage guide directly
- `menu_score_assessment`: inject `请帮我做分数定位。`
- `menu_major_recommendation`: inject `请给我做专业推荐。`
- `menu_volunteer_strategy`: inject `请给我一份志愿填报策略建议。`

Unknown menu keys fall back to a passive text hint instead of failing the callback.
