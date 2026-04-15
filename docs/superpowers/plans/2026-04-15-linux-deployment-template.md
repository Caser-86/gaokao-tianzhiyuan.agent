# Linux Deployment Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reusable Linux deployment templates for the current Gaokao Agent MVP using environment examples, `systemd` units, `nginx` reverse proxying, and an operator runbook.

**Architecture:** Keep the repo deployment assets text-only and adaptation-friendly. Put Linux-specific material under `deploy/linux/`, using production-oriented env examples, separate `systemd` unit templates for API and Web, a single `nginx` site config, and a Linux README that explains directory layout, startup, restart, logs, smoke checks, and rollback checks.

**Tech Stack:** FastAPI/Uvicorn, Next.js, Linux, systemd, nginx, existing repo docs

---

### Task 1: Add Linux deployment templates

**Files:**
- Create: `deploy/linux/api.production.env.example`
- Create: `deploy/linux/web.production.env.example`
- Create: `deploy/linux/systemd/gaokao-agent-api.service`
- Create: `deploy/linux/systemd/gaokao-agent-web.service`
- Create: `deploy/linux/nginx/gaokao-agent.conf`

- [ ] **Step 1: Create Linux API env example**

Include placeholders for:

- production admin token
- Linux SQLite path
- relay configuration
- optional ZhangXueFeng skill path

- [ ] **Step 2: Create Linux Web env example**

Include:

- API base URL
- public API base URL
- admin token

- [ ] **Step 3: Create API systemd unit template**

Use:

- `WorkingDirectory=/srv/gaokao-agent/apps/api`
- `EnvironmentFile=/etc/gaokao-agent/api.env`
- `ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
- restart policy and standard `systemd` service settings

- [ ] **Step 4: Create Web systemd unit template**

Use:

- `WorkingDirectory=/srv/gaokao-agent/apps/web`
- `EnvironmentFile=/etc/gaokao-agent/web.env`
- `ExecStart=/usr/bin/node ./node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3000`
- restart policy and standard `systemd` service settings

- [ ] **Step 5: Create nginx site config template**

Route:

- `/api/` to `127.0.0.1:8000`
- `/health` to the API
- all other traffic to `127.0.0.1:3000`

### Task 2: Add Linux operator documentation

**Files:**
- Create: `deploy/linux/README.md`
- Modify: `README.md`
- Modify: `docs/operations/local-handover-runbook.md`

- [ ] **Step 1: Create Linux deployment readme**

Document:

- suggested server directory layout
- where to copy env files
- required build command for the Web app
- `systemctl daemon-reload`, enable, start, restart, status
- `nginx -t` and reload flow
- health checks and smoke checks
- rollback-oriented checks

- [ ] **Step 2: Link Linux docs from repo docs**

Update the main docs so operators can discover `deploy/linux/README.md`.

### Task 3: Verify and commit

**Files:**
- Verify: `deploy/linux/*`
- Verify: `README.md`
- Verify: `docs/operations/local-handover-runbook.md`

- [ ] **Step 1: Run formatting check**

Run: `git diff --check`

Expected: no diff formatting errors.

- [ ] **Step 2: Inspect the Linux templates**

Run: `Get-ChildItem -Recurse -File deploy/linux | Select-Object FullName`

Expected: env examples, `systemd` units, nginx config, and Linux README all exist.

- [ ] **Step 3: Run repo verification**

Run: `powershell -ExecutionPolicy Bypass -File scripts/verify-project.ps1`

Expected: API tests pass, Web tests pass, Web build passes.

- [ ] **Step 4: Commit**

```bash
git add deploy/linux/api.production.env.example deploy/linux/web.production.env.example deploy/linux/systemd/gaokao-agent-api.service deploy/linux/systemd/gaokao-agent-web.service deploy/linux/nginx/gaokao-agent.conf deploy/linux/README.md README.md docs/operations/local-handover-runbook.md docs/superpowers/plans/2026-04-15-linux-deployment-template.md
git commit -m "chore(ops): add linux deployment templates"
```
