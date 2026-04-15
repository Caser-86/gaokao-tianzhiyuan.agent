# Local Stack Startup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a one-command local startup script that launches the API and Web apps together and can optionally run the existing live smoke test.

**Architecture:** Add one root PowerShell launcher under `scripts/` that starts the API and Web in separate child PowerShell processes, writes logs to `.tmp/`, waits for both services to become reachable, and optionally invokes the existing smoke script. Keep the implementation local-dev oriented and non-destructive so it complements the existing verification and smoke scripts.

**Tech Stack:** PowerShell, FastAPI/Uvicorn, Next.js, existing repo scripts

---

### Task 1: Add the startup launcher

**Files:**
- Create: `scripts/start-local-stack.ps1`
- Reference: `scripts/smoke-local-stack.ps1`
- Reference: `scripts/verify-project.ps1`

- [ ] **Step 1: Validate the missing entry point**

Run: `powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 -DryRun`

Expected: PowerShell fails because the script does not exist yet.

- [ ] **Step 2: Create the startup script**

Create a script that:

- accepts `ApiPort`, `WebPort`, `AdminToken`, `DatabasePath`, `ApiBaseUrl`, `WebBaseUrl`, `RunSmoke`, and `DryRun`
- starts API and Web in child PowerShell processes
- writes logs to `.tmp/start-local-stack-api.*.log` and `.tmp/start-local-stack-web.*.log`
- waits for `/health` and `/`
- prints process ids, URLs, and log locations
- optionally calls `scripts/smoke-local-stack.ps1`

- [ ] **Step 3: Run the launcher in dry-run mode**

Run: `powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 -DryRun`

Expected: The script prints the startup plan, target URLs, and log paths without trying to launch processes.

### Task 2: Document the new startup flow

**Files:**
- Modify: `README.md`
- Modify: `docs/operations/local-handover-runbook.md`

- [ ] **Step 1: Add README usage**

Document:

- one-command startup
- optional `-RunSmoke`
- where logs are written

- [ ] **Step 2: Add runbook usage**

Document:

- startup command
- expected URLs
- how to stop the spawned processes
- how startup interacts with the existing smoke script

### Task 3: Verify the end-to-end flow

**Files:**
- Verify: `scripts/start-local-stack.ps1`
- Verify: `scripts/smoke-local-stack.ps1`
- Verify: `scripts/verify-project.ps1`

- [ ] **Step 1: Run syntax and formatting checks**

Run: `git diff --check`

Expected: no diff formatting errors.

- [ ] **Step 2: Run the launcher in dry-run mode**

Run: `powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 -DryRun`

Expected: planned startup output only, exit code 0.

- [ ] **Step 3: Run the launcher with live smoke**

Run: `powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 -RunSmoke`

Expected: API and Web start locally, smoke probes pass, and the launcher reports the process ids and URLs.

- [ ] **Step 4: Run the full repo verification command**

Run: `powershell -ExecutionPolicy Bypass -File scripts/verify-project.ps1`

Expected: API tests pass, Web tests pass, Web build passes.

- [ ] **Step 5: Commit**

```bash
git add scripts/start-local-stack.ps1 README.md docs/operations/local-handover-runbook.md docs/superpowers/plans/2026-04-15-local-stack-startup.md
git commit -m "chore(ops): add local stack startup script"
```
