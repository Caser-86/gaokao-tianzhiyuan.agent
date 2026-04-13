# Foundation Files Regularization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Track the currently untracked public web foundation files, platform API foundation files, and catalog data, while adding ignore rules that keep local artifacts out of the repository.

**Architecture:** Use tiny repository-verification scripts to test the actual regularization requirement: which files must be tracked and which local artifacts must be ignored. Then stage the existing foundation files as tracked project assets, and verify them with the already-existing targeted API and web test suites.

**Tech Stack:** PowerShell, git, FastAPI, pytest, Next.js App Router, Vitest, Testing Library

---

## File Structure

- `.gitignore`: root ignore rules for node, Next.js, Python bytecode, and local caches
- `scripts/verify-gitignore.ps1`: asserts representative local artifact paths are ignored by git
- `scripts/verify-public-foundation.ps1`: asserts the public web foundation files and catalog data are tracked by git
- `scripts/verify-platform-foundation.ps1`: asserts the platform API foundation files are tracked by git
- `apps/web/app/layout.tsx`: tracked app layout baseline
- `apps/web/app/globals.css`: tracked public site styling baseline
- `apps/web/components/public/page-section-renderer.tsx`: tracked public presentational component
- `apps/web/components/public/search-entry.tsx`: tracked public presentational component
- `apps/web/tests/public-content.test.tsx`: tracked public component rendering tests
- `apps/web/tsconfig.json`: tracked TypeScript config for the web workspace
- `apps/web/next-env.d.ts`: tracked Next.js type metadata for the web workspace
- `data/catalog.json`: tracked API-backed catalog data asset
- `apps/api/app/routers/platform.py`: tracked platform API router
- `apps/api/app/services/platform.py`: tracked platform service logic
- `apps/api/tests/test_platform_api.py`: tracked platform API tests

### Task 1: Add Root Ignore Rules And Prove They Work

**Files:**
- Create: `.gitignore`
- Create: `scripts/verify-gitignore.ps1`
- Test: `scripts/verify-gitignore.ps1`

- [ ] **Step 1: Write the failing test**

Create `scripts/verify-gitignore.ps1` with:

```powershell
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$pathsThatMustBeIgnored = @(
  'apps/web/.next/cache/test-entry',
  'apps/web/node_modules/react/index.js',
  'apps/api/__pycache__/main.cpython-313.pyc',
  'apps/api/.pytest_cache/v/cache/nodeids'
)

Push-Location $repoRoot
try {
  foreach ($path in $pathsThatMustBeIgnored) {
    git check-ignore $path | Out-Null
    if ($LASTEXITCODE -ne 0) {
      throw "Expected git to ignore $path"
    }
  }
}
finally {
  Pop-Location
}
```

- [ ] **Step 2: Run test to verify it fails**

Run from the repository root: `powershell -ExecutionPolicy Bypass -File .\scripts\verify-gitignore.ps1`

Expected: `FAIL` because the repository does not yet define ignore rules for the sample `.next`, `node_modules`, `__pycache__`, and `.pytest_cache` paths.

- [ ] **Step 3: Write minimal implementation**

Create `.gitignore` with:

```gitignore
# Node and Next.js
**/node_modules/
**/.next/

# Python bytecode and test caches
**/__pycache__/
**/.pytest_cache/
*.pyc
*.pyo

# OS and editor noise
.DS_Store
Thumbs.db
```

- [ ] **Step 4: Run test to verify it passes**

Run from the repository root: `powershell -ExecutionPolicy Bypass -File .\scripts\verify-gitignore.ps1`

Expected: `PASS` with no output and exit code `0`.

- [ ] **Step 5: Commit**

```bash
git add .gitignore scripts/verify-gitignore.ps1
git commit -m "chore: add repository ignore rules"
```

### Task 2: Track The Public Web Foundation Files And Catalog Data

**Files:**
- Create: `scripts/verify-public-foundation.ps1`
- Create: `apps/web/app/layout.tsx`
- Create: `apps/web/app/globals.css`
- Create: `apps/web/components/public/page-section-renderer.tsx`
- Create: `apps/web/components/public/search-entry.tsx`
- Create: `apps/web/tests/public-content.test.tsx`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/next-env.d.ts`
- Create: `data/catalog.json`
- Test: `scripts/verify-public-foundation.ps1`
- Test: `apps/web/tests/public-content.test.tsx`
- Test: `apps/web/tests/toolchain-config.test.ts`
- Test: `apps/web/tests/public-content-api.test.ts`
- Test: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `scripts/verify-public-foundation.ps1` with:

```powershell
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$pathsThatMustBeTracked = @(
  'apps/web/app/layout.tsx',
  'apps/web/app/globals.css',
  'apps/web/components/public/page-section-renderer.tsx',
  'apps/web/components/public/search-entry.tsx',
  'apps/web/tests/public-content.test.tsx',
  'apps/web/tsconfig.json',
  'apps/web/next-env.d.ts',
  'data/catalog.json'
)

Push-Location $repoRoot
try {
  foreach ($path in $pathsThatMustBeTracked) {
    git ls-files --error-unmatch -- $path | Out-Null
    if ($LASTEXITCODE -ne 0) {
      throw "Expected git to track $path"
    }
  }
}
finally {
  Pop-Location
}
```

- [ ] **Step 2: Run test to verify it fails**

Run from the repository root: `powershell -ExecutionPolicy Bypass -File .\scripts\verify-public-foundation.ps1`

Expected: `FAIL` because these public web foundation files and `data/catalog.json` are currently present in the workspace but not yet tracked by git.

- [ ] **Step 3: Write minimal implementation**

No content changes are required for the public foundation files in this task. Stage the existing files exactly as they are, along with the new verification script:

```bash
git add scripts/verify-public-foundation.ps1
git add apps/web/app/layout.tsx
git add apps/web/app/globals.css
git add apps/web/components/public/page-section-renderer.tsx
git add apps/web/components/public/search-entry.tsx
git add apps/web/tests/public-content.test.tsx
git add apps/web/tsconfig.json
git add apps/web/next-env.d.ts
git add data/catalog.json
```

- [ ] **Step 4: Run test to verify it passes**

Run from the repository root:

```bash
powershell -ExecutionPolicy Bypass -File .\scripts\verify-public-foundation.ps1
```

Run from `apps/web`:

```bash
node ./node_modules/vitest/vitest.mjs run tests/toolchain-config.test.ts tests/public-content-api.test.ts tests/public-pages.test.tsx tests/public-content.test.tsx
```

Expected:

- the PowerShell verification exits `0`
- the Vitest command reports `14 passed`

- [ ] **Step 5: Commit**

```bash
git add scripts/verify-public-foundation.ps1
git add apps/web/app/layout.tsx apps/web/app/globals.css
git add apps/web/components/public/page-section-renderer.tsx apps/web/components/public/search-entry.tsx
git add apps/web/tests/public-content.test.tsx apps/web/tsconfig.json apps/web/next-env.d.ts
git add data/catalog.json
git commit -m "chore: track public foundation files"
```

### Task 3: Track The Platform API Foundation Files

**Files:**
- Create: `scripts/verify-platform-foundation.ps1`
- Create: `apps/api/app/routers/platform.py`
- Create: `apps/api/app/services/platform.py`
- Create: `apps/api/tests/test_platform_api.py`
- Test: `scripts/verify-platform-foundation.ps1`
- Test: `apps/api/tests/test_platform_api.py`
- Test: `apps/api/tests/test_public_catalog_api.py`

- [ ] **Step 1: Write the failing test**

Create `scripts/verify-platform-foundation.ps1` with:

```powershell
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$pathsThatMustBeTracked = @(
  'apps/api/app/routers/platform.py',
  'apps/api/app/services/platform.py',
  'apps/api/tests/test_platform_api.py'
)

Push-Location $repoRoot
try {
  foreach ($path in $pathsThatMustBeTracked) {
    git ls-files --error-unmatch -- $path | Out-Null
    if ($LASTEXITCODE -ne 0) {
      throw "Expected git to track $path"
    }
  }
}
finally {
  Pop-Location
}
```

- [ ] **Step 2: Run test to verify it fails**

Run from the repository root: `powershell -ExecutionPolicy Bypass -File .\scripts\verify-platform-foundation.ps1`

Expected: `FAIL` because the platform router, service, and tests are currently present in the workspace but not yet tracked by git.

- [ ] **Step 3: Write minimal implementation**

No content changes are required for the platform foundation files in this task. Stage the existing files along with the verification script:

```bash
git add scripts/verify-platform-foundation.ps1
git add apps/api/app/routers/platform.py
git add apps/api/app/services/platform.py
git add apps/api/tests/test_platform_api.py
```

- [ ] **Step 4: Run test to verify it passes**

Run from the repository root:

```bash
powershell -ExecutionPolicy Bypass -File .\scripts\verify-platform-foundation.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\verify-gitignore.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\verify-public-foundation.ps1
```

Run from `apps/api`:

```bash
python -m pytest tests/test_platform_api.py tests/test_public_catalog_api.py -v
```

Run from `apps/web`:

```bash
node ./node_modules/vitest/vitest.mjs run tests/toolchain-config.test.ts tests/public-content-api.test.ts tests/public-pages.test.tsx tests/public-content.test.tsx
```

Expected:

- all three PowerShell verification scripts exit `0`
- the pytest command reports `7 passed`
- the Vitest command reports `14 passed`

- [ ] **Step 5: Commit**

```bash
git add scripts/verify-platform-foundation.ps1
git add apps/api/app/routers/platform.py apps/api/app/services/platform.py apps/api/tests/test_platform_api.py
git commit -m "chore: track platform foundation files"
```
