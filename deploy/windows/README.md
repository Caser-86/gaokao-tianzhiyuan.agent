# Windows 11 Run Template

This folder contains Windows-oriented operator assets for running the current
Gaokao Agent MVP as a long-running local stack.

## Included files

- `api.production.env.example`
- `web.production.env.example`

## Recommended layout

Example local layout:

```text
D:\gaokao-agent\
  apps\
  deploy\
  scripts\
  vendor\
  .tmp\
```

## Setup

### API

Copy the template and fill in your real values:

```powershell
Copy-Item deploy\windows\api.production.env.example apps\api\.env
```

Pay attention to:

- `GAOKAO_AGENT_ADMIN_TOKEN`
- `GAOKAO_AGENT_DATABASE_URL`
- relay credentials
- `GAOKAO_AGENT_ZHANGXUEFENG_SKILL_PATH`

### Web

Copy the template and fill in your real values:

```powershell
Copy-Item deploy\windows\web.production.env.example apps\web\.env.local
```

The Web admin token must match the API token.

## Start

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1
```

Start plus smoke:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 -RunSmoke
```

The script writes:

- runtime logs into `.tmp/`
- runtime state into `.tmp/start-local-stack.state.json`

## Stop

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-local-stack.ps1
```

Dry-run stop:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-local-stack.ps1 -DryRun
```

## Logs

Look in `.tmp/` first:

- `start-local-stack-api.*.out.log`
- `start-local-stack-api.*.err.log`
- `start-local-stack-web.*.out.log`
- `start-local-stack-web.*.err.log`

## Optional Task Scheduler usage

If you want the stack to come back after login:

1. Create a Task Scheduler task that runs:
   `powershell -ExecutionPolicy Bypass -File D:\gaokao-agent\scripts\start-local-stack.ps1`
2. Set the task to run at user logon
3. Keep the working repo path stable
4. Re-run `scripts/smoke-local-stack.ps1` after major updates

This phase does not register Windows services. It keeps the operating model
simple and repo-controlled.
