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
- `GAOKAO_AGENT_ZHANGXUEFENG_SKILL_PATH=<absolute path to SKILL.md>`

Example:

```env
GAOKAO_AGENT_LLM_PROVIDER=openai_compatible
GAOKAO_AGENT_LLM_BASE_URL=https://your-relay.example
GAOKAO_AGENT_LLM_API_KEY=your-relay-api-key
GAOKAO_AGENT_LLM_MODEL=gpt-4o-mini
GAOKAO_AGENT_ZHANGXUEFENG_SKILL_PATH=D:/skills/zhangxuefeng-skill/SKILL.md
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
