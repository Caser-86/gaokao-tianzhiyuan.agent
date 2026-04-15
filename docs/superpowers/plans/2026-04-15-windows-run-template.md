# Windows Run Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Windows 11 operator assets that support long-running local usage through reusable env templates, a stop script, and a Windows-focused runbook.

**Architecture:** Extend the existing local startup flow instead of replacing it. The startup script should keep doing the launch work, but it will also persist runtime state so a matching stop script can terminate the actual listener processes later. Deployment-oriented Windows files should live under `deploy/windows/` and operator docs should point to them from the main runbook.

**Tech Stack:** PowerShell, FastAPI/Uvicorn, Next.js, existing repo scripts

---

### Task 1: Add persistent startup state and a matching stop script

**Files:**
- Modify: `scripts/start-local-stack.ps1`
- Create: `scripts/stop-local-stack.ps1`

- [ ] **Step 1: Validate the missing stop entry point**

Run: `powershell -ExecutionPolicy Bypass -File scripts/stop-local-stack.ps1 -DryRun`

Expected: PowerShell fails because the script does not exist yet.

- [ ] **Step 2: Extend startup to persist runtime state**

Update `scripts/start-local-stack.ps1` so it records a JSON state file under `.tmp/` that includes:

- API listener pid
- Web listener pid
- API port
- Web port
- API base URL
- Web base URL
- log file paths
- timestamp

- [ ] **Step 3: Add the stop script**

Create `scripts/stop-local-stack.ps1` with support for:

- reading the default state file from `.tmp/`
- optional `-StateFilePath`
- optional `-ApiPort` and `-WebPort` fallback process lookup
- `-DryRun`

The script should stop the stored listener pids first, then fall back to port-based cleanup if needed.

- [ ] **Step 4: Verify stop script dry run**

Run: `powershell -ExecutionPolicy Bypass -File scripts/stop-local-stack.ps1 -DryRun`

Expected: The script prints what it would stop without killing anything.

### Task 2: Add Windows deployment templates and docs

**Files:**
- Create: `deploy/windows/api.production.env.example`
- Create: `deploy/windows/web.production.env.example`
- Create: `deploy/windows/README.md`
- Modify: `README.md`
- Modify: `docs/operations/local-handover-runbook.md`

- [ ] **Step 1: Add Windows env examples**

Create API and Web examples with placeholders for:

- admin token
- SQLite path
- relay provider configuration
- API URL values used by the Web app

- [ ] **Step 2: Add a Windows operator readme**

Document:

- copying env examples into runtime env files
- starting the stack
- stopping the stack
- log file locations
- optional Task Scheduler usage notes

- [ ] **Step 3: Link Windows docs from existing docs**

Update `README.md` and `docs/operations/local-handover-runbook.md` to point to the new Windows deployment material.

### Task 3: Verify the Windows operator flow

**Files:**
- Verify: `scripts/start-local-stack.ps1`
- Verify: `scripts/stop-local-stack.ps1`
- Verify: `deploy/windows/README.md`

- [ ] **Step 1: Run formatting check**

Run: `git diff --check`

Expected: no diff formatting errors.

- [ ] **Step 2: Run startup in dry run mode**

Run: `powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 -DryRun`

Expected: startup plan output only.

- [ ] **Step 3: Run stop in dry run mode**

Run: `powershell -ExecutionPolicy Bypass -File scripts/stop-local-stack.ps1 -DryRun`

Expected: stop plan output only.

- [ ] **Step 4: Run live startup**

Run: `powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 -ApiPort 8018 -WebPort 3018 -RunSmoke`

Expected: startup completes, smoke passes, and a state file is written.

- [ ] **Step 5: Run live stop**

Run: `powershell -ExecutionPolicy Bypass -File scripts/stop-local-stack.ps1`

Expected: the saved API and Web listener processes are stopped and the ports are released.

- [ ] **Step 6: Run repo verification**

Run: `powershell -ExecutionPolicy Bypass -File scripts/verify-project.ps1`

Expected: API tests pass, Web tests pass, Web build passes.

- [ ] **Step 7: Commit**

```bash
git add scripts/start-local-stack.ps1 scripts/stop-local-stack.ps1 deploy/windows/api.production.env.example deploy/windows/web.production.env.example deploy/windows/README.md README.md docs/operations/local-handover-runbook.md docs/superpowers/plans/2026-04-15-windows-run-template.md
git commit -m "chore(ops): add windows run templates"
```
