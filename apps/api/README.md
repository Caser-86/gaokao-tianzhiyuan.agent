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

During the transition period, request `metadata.entitlements` is still accepted, but persisted DB state is preferred when available.
