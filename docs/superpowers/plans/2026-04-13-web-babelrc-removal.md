# Web Babelrc Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove `apps/web/.babelrc` if the current web workspace does not require it to test and build successfully.

**Architecture:** Use a tiny repository-verification script to make the residual file's presence explicit, then delete the file and verify the current web workspace with both the targeted Vitest suite and a real Next.js build. If both pass, keep the deletion and do not replace the config.

**Tech Stack:** PowerShell, git, Next.js 15, Vitest, Testing Library

---

## File Structure

- `scripts/verify-web-babelrc.ps1`: checks whether `apps/web/.babelrc` still exists in the workspace
- `apps/web/.babelrc`: residual Babel config expected to be removed

### Task 1: Verify And Remove The Residual Web Babel Config

**Files:**
- Create: `scripts/verify-web-babelrc.ps1`
- Delete: `apps/web/.babelrc`
- Test: `scripts/verify-web-babelrc.ps1`

- [ ] **Step 1: Write the failing test**

Create `scripts/verify-web-babelrc.ps1` with:

```powershell
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$babelConfigPath = Join-Path $repoRoot 'apps\web\.babelrc'

if (Test-Path $babelConfigPath) {
  throw "Expected apps/web/.babelrc to be removed"
}
```

- [ ] **Step 2: Run test to verify it fails**

Run from the repository root: `powershell -ExecutionPolicy Bypass -File .\scripts\verify-web-babelrc.ps1`

Expected: `FAIL` because `apps/web/.babelrc` still exists.

- [ ] **Step 3: Write minimal implementation**

Delete `apps/web/.babelrc`.

- [ ] **Step 4: Run test to verify it passes**

Run from the repository root:

```bash
powershell -ExecutionPolicy Bypass -File .\scripts\verify-web-babelrc.ps1
```

Run from `apps/web`:

```bash
node ./node_modules/vitest/vitest.mjs run tests/toolchain-config.test.ts tests/public-content-api.test.ts tests/public-pages.test.tsx tests/public-content.test.tsx
node ./node_modules/next/dist/bin/next build
```

Expected:

- the PowerShell verification exits `0`
- the Vitest command reports `14 passed`
- the Next.js build exits `0`

- [ ] **Step 5: Commit**

```bash
git add scripts/verify-web-babelrc.ps1
git rm apps/web/.babelrc
git commit -m "chore(web): remove residual babel config"
```
