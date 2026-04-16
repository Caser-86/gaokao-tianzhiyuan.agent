# Local Handover Runbook

This runbook is the operator-facing checklist for the current Gaokao Agent MVP.
Use it when you need to boot the stack locally, validate the main flows, or hand
the project to another developer for continued integration.

## Scope

The current workspace includes:

- `apps/api`: FastAPI backend for public content, admin endpoints, chat routing,
  smart-analysis policy, and skill invocation.
- `apps/web`: Next.js frontend for public pages, `/chat`, and `/admin`.
- `vendor/zhangxuefeng-skill` or `.tmp/zhangxuefeng-skill`: optional local skill
  checkout for the ZhangXueFeng integration.
- `deploy/windows`: Windows 11 operator templates and env examples
- `deploy/linux`: Linux deployment templates for `systemd` and `nginx`

## Prerequisites

- Python 3.12+ available as `python`
- Node.js 20+ and `npm`
- PowerShell
- Optional network access if you want model-backed smart analysis through an
  OpenAI-compatible relay

## Environment Setup

### API

From `apps/api`:

```powershell
Copy-Item .env.example .env
```

Fill in these values before using relay-backed smart analysis:

- `GAOKAO_AGENT_ADMIN_TOKEN`
- `GAOKAO_AGENT_DATABASE_URL`
- `GAOKAO_AGENT_LLM_PROVIDER`
- `GAOKAO_AGENT_LLM_BASE_URL`
- `GAOKAO_AGENT_LLM_API_KEY`
- `GAOKAO_AGENT_LLM_MODEL`

Optional:

- `GAOKAO_AGENT_SMART_ANALYSIS_MODE`
- `GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_TOKEN`
- `GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_APP_ID`
- `GAOKAO_AGENT_WECHAT_OFFICIAL_ACCOUNT_ENCODING_AES_KEY`
- `GAOKAO_AGENT_ZHANGXUEFENG_SKILL_PATH`

### Web

From `apps/web`:

```powershell
Copy-Item .env.example .env.local
```

Required values:

- `GAOKAO_AGENT_API_URL`
- `NEXT_PUBLIC_GAOKAO_AGENT_API_URL`
- `GAOKAO_AGENT_ADMIN_TOKEN`

The admin token in `apps/web/.env.local` must match the API token.

## ZhangXueFeng Skill Resolution

If `GAOKAO_AGENT_ZHANGXUEFENG_SKILL_PATH` is blank, the API automatically tries:

1. `vendor/zhangxuefeng-skill/SKILL.md`
2. `.tmp/zhangxuefeng-skill/SKILL.md`

To prepare the local skill checkout:

```powershell
git clone https://github.com/alchaincyf/zhangxuefeng-skill.git vendor/zhangxuefeng-skill
```

If the skill file is missing or the relay fails, chat still falls back to
structured rule-based output instead of crashing.

## Smart Analysis Control Model

The current smart-analysis gate has three layers:

1. Global runtime mode in SQLite
2. Per-user `smart_analysis` entitlement in SQLite
3. Legacy request metadata entitlement during the transition period

Supported global modes:

- `off`: nobody gets model-backed smart analysis
- `gated`: only entitled users get model-backed smart analysis
- `on`: everyone gets model-backed smart analysis

Admin endpoints:

- `GET /api/admin/smart-analysis/settings`
- `PUT /api/admin/smart-analysis/settings`
- `GET /api/admin/smart-analysis/users/{user_id}`
- `PUT /api/admin/smart-analysis/users/{user_id}`
- `GET /api/admin/media-analysis-events?limit=10`
  - optional filters: `status`, `user_id`, `auto_routed_to_chat`
- `POST /api/admin/media-analysis-events/{event_id}/retry`
  - currently retries image records with a persisted `context.pic_url`

Fallback reasons exposed in `debug.notes` include:

- `smart_analysis_disabled_globally`
- `smart_analysis_entitlement_required`
- `provider_not_configured`
- `provider_request_failed`
- `provider_insufficient_balance`
- `provider_invalid_response`

## Startup Order

### 1. Preferred one-command startup

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1
```

Optional:

- add `-RunSmoke` to run the existing live smoke checks right after startup
- add `-ApiEnvFilePath apps\api\.env` or `-WebEnvFilePath apps\web\.env.local` if you want to point at non-default env files explicitly
- logs are written to `.tmp/`
- the script auto-loads `apps/api/.env` and `apps/web/.env.local` when those files exist
- the script prints `Stop-Process` commands for the spawned API and Web processes
- startup state is written to `.tmp/start-local-stack.state.json`
- startup output and state now mask or omit raw admin and WeChat callback secrets

Example with explicit env files plus smoke:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 `
  -ApiEnvFilePath apps\api\.env `
  -WebEnvFilePath apps\web\.env.local `
  -RunSmoke
```

### Windows operator templates

Windows-specific env examples and operator notes:

```text
deploy/windows/
```

### Linux operator templates

Linux deployment templates and operator notes:

```text
deploy/linux/
```

This includes:

- production-style API and Web env examples
- `systemd` unit templates
- an `nginx` site config template
- a Linux deployment readme

Stop the running stack with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-local-stack.ps1
```

### 2. Manual API startup

```powershell
cd apps/api
python -m uvicorn app.main:app --reload --port 8000
```

Expected checks:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/chat/health
```

### 3. Manual Web startup

```powershell
cd apps/web
npm install
npm run dev
```

Expected local URLs:

- `http://127.0.0.1:3000/`
- `http://127.0.0.1:3000/chat`
- `http://127.0.0.1:3000/admin`

## Smoke Test Checklist

### Public pages

- Open the homepage and confirm it renders
- Open at least one school detail page
- Open at least one major detail page

### Admin flows

- Open `/admin`
- Confirm the dashboard loads without a token mismatch error
- Change the smart-analysis global mode and refresh
- Check one user entitlement record through the admin API

### Chat flows

- Open `/chat`
- Submit a normal consultation prompt
- Submit a ZhangXueFeng-style prompt
- Confirm the API returns either model-backed output or a structured fallback

### Direct API probe

```powershell
$body = @{
  channel = "wechat"
  user_id = "wx-local-test"
  message = "Henan 560 points, finance major, what should I target?"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/chat/messages `
  -ContentType "application/json" `
  -Body $body
```

If the relay has no balance or is disabled, the request should still return a
valid fallback payload instead of a 500 crash.

### One-command live smoke

After the API and Web services are already running:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke-local-stack.ps1
```

Useful options:

- `-ApiBaseUrl http://127.0.0.1:8000`
- `-WebBaseUrl http://127.0.0.1:3000`
- `-ApiEnvFilePath apps\api\.env`
- `-AdminToken <your admin token>`
- `-WechatOfficialAccountToken <your wechat callback token>`
- `-WechatOfficialAccountAppId <your wechat app id>`
- `-WechatOfficialAccountEncodingAesKey <your 43-char aes key>`
- `-RequiredSkillIds zhangxuefeng,catalog_lookup`
- `-SkipAdminCheck`
- `-SkipChatProbe`
- `-SkipWechatProbe`
- `-SkipWechatOfficialAccountProbe`
- `-DryRun`

If `apps/api/.env` exists, the smoke script auto-loads it and reuses the admin
token plus official-account callback settings automatically.

The official-account smoke probe now verifies:

- signature handshake
- passive text-message reply
- passive subscribe welcome reply
- passive menu-click reply
- official-account callback event routing
- picture-event guidance reply
- direct image-message guidance reply
- direct video-message guidance reply
- voice-message recognition routing
- location-message routing
- link-message routing
- AES-mode handshake
- AES-mode encrypted passive reply

The chat skill listing smoke probe now expects both built-in skills by default:

- `zhangxuefeng`
- `catalog_lookup`

When you need to hand-debug an official-account AES callback outside the smoke
script, use the repo helper:

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

For callback-only acceptance without checking homepage/admin/chat, use the
dedicated probe:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke-wechat-official-account.ps1 `
  -ApiBaseUrl http://127.0.0.1:8000 `
  -ApiEnvFilePath apps\api\.env
```

Useful options:

- `-WechatOfficialAccountToken <your wechat callback token>`
- `-WechatOfficialAccountAppId <your wechat app id>`
- `-WechatOfficialAccountEncodingAesKey <your 43-char aes key>`
- `-SkipPlaintextProbes`
- `-SkipAesProbes`
- `-DryRun`

Note:

- Direct `image` / `video` official-account messages now reuse the existing smart-analysis global mode and user-entitlement gate.
- When media analysis is enabled for the current user, intentionally blank media-analysis providers still use the reserved pending reply, but explicit image-analysis failures now return a dedicated temporary-unavailable reply and persist a failed event reason.
- The adapter layer already reserves `GAOKAO_AGENT_MEDIA_ANALYSIS_PROVIDER / BASE_URL / API_KEY / MODEL / TIMEOUT_SECONDS`; later provider integration should plug into that layer instead of modifying the callback router again.
- The current `openai_compatible` adapter performs real media analysis only for official-account `image` callbacks with `PicUrl`; `video` / `shortvideo` are still unsupported and do not enter a real upstream analysis flow yet.
- Official-account `video` / `shortvideo` attempts under `openai_compatible` now persist as explicit failed records with a readable unsupported-media reason, while user-facing replies stay on the normal video guidance text.
- Successful media-analysis results are now normalized into `summary / extracted_fields / rendered_reply`, so later routing can consume extracted fields without changing provider-specific parsing again.
- Admin dashboard operators can manually retry a stored image-analysis event; the retry writes a new `admin_media_analysis_retry` record so audit history stays intact.
- Failed media-analysis requests now persist a readable `context.failure_reason`, and the `/admin` media-analysis cards render that reason directly for triage.
- The `/admin` media-analysis area now shows current-list failure counts plus one-click failed-only or all-record shortcuts, so support can narrow triage faster without rebuilding filters.
- Recent media-analysis cards now label whether a row is the original record or a manual retry record, and original rows surface the latest visible retry id/status when one exists in the current list.
- The `/admin` media-analysis list now also exposes `retryable` vs blocked records. Only image rows with persisted `pic_url` render the retry action; blocked rows show a readable reason such as unsupported non-image media or missing `pic_url`.
- When extracted image fields are rich enough, the callback now auto-synthesizes a normalized gaokao prompt and routes it into the existing chat flow instead of stopping at a media summary.
- Each official-account media-analysis attempt now writes a lightweight SQLite record, and `/admin` shows the most recent records so operators can verify provider output, extracted fields, retained callback context, and whether an image was auto-routed into the main gaokao flow.
- Operators can now narrow that list by `status`, `user_id`, and the “auto-routed into main analysis” flag when investigating a bad extraction or a specific user complaint.
- Each record now has a detail expander so support can inspect raw callback context such as `msg_id`, `media_id`, `pic_url`, and `create_time` without querying SQLite directly.

## Verification Commands

Run these before calling the current branch ready for handoff:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify-project.ps1
```

```powershell
cd apps/api
python -m pytest -q
```

```powershell
cd apps/web
npm test --
npm run build
```

## Production-like Notes

- The database is SQLite in the current MVP, so keep file paths stable and back
  up the DB file before major admin changes.
- The Next.js build may warn that native SWC binaries are blocked on Windows.
  The project is configured to fall back to wasm builds through
  `experimental.useWasmBinary`, so a successful build is still acceptable.
- Keep local relay keys only in `.env` or platform secrets. Do not commit them.

## Handover Status

The current branch is in a usable MVP state when all of the following are true:

- API health checks pass
- Web dev server boots and `/`, `/chat`, `/admin` render
- API tests pass
- Web tests pass
- Web production build passes
- Smart-analysis mode changes persist
- ZhangXueFeng prompts produce either routed model output or a graceful fallback
