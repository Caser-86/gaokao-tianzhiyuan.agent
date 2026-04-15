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
- logs are written to `.tmp/`
- the script prints `Stop-Process` commands for the spawned API and Web processes
- startup state is written to `.tmp/start-local-stack.state.json`

### Windows operator templates

Windows-specific env examples and operator notes:

```text
deploy/windows/
```

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
- `-AdminToken <your admin token>`
- `-SkipAdminCheck`
- `-SkipChatProbe`
- `-SkipWechatProbe`
- `-DryRun`

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
