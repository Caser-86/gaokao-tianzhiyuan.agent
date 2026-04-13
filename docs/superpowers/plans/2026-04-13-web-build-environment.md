# Web Build Environment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `apps/web` build successfully on this constrained Windows workstation while keeping `apps/web/.babelrc` removed.

**Architecture:** Add a tracked Next config that opts into the wasm compiler path, then provide a repository-owned `env` bridge package that exposes the N-API imports expected by `@next/swc-wasm-nodejs`. Finish by tracking the Babel cleanup verifier and proving the full web verification path passes without manual `node_modules` edits.

**Tech Stack:** Next.js 15.4.0, React 19.1.0, Vitest, PowerShell, npm local file dependency, `@emnapi/core`, `@emnapi/runtime`

---

### Task 1: Add Wasm Build Runtime Coverage And Shim

**Files:**
- Create: `apps/web/next.config.ts`
- Create: `apps/web/tests/next-build-runtime.test.ts`
- Create: `apps/web/vendor/env-shim/package.json`
- Create: `apps/web/vendor/env-shim/index.js`
- Modify: `apps/web/package.json`
- Modify: `apps/web/package-lock.json`
- Modify: `apps/web/tests/toolchain-config.test.ts`

- [ ] **Step 1: Write the failing regression tests**

```ts
// apps/web/tests/next-build-runtime.test.ts
import nextConfig from '../next.config';

test('opts into the wasm compiler path for constrained builds', () => {
  expect(nextConfig.experimental?.useWasmBinary).toBe(true);
});

test('loads the Next wasm bindings through the repository-owned env bridge', async () => {
  const bindings = await import('next/wasm/@next/swc-wasm-nodejs/wasm.js');

  expect(bindings.transformSync).toEqual(expect.any(Function));
});
```

```ts
// apps/web/tests/toolchain-config.test.ts
import packageJson from '../package.json';

test('declares a reproducible vitest toolchain for the web workspace', () => {
  expect(packageJson.scripts.dev).toBe('node ./node_modules/next/dist/bin/next dev');
  expect(packageJson.scripts.build).toBe('node ./node_modules/next/dist/bin/next build');
  expect(packageJson.scripts.test).toBe('node ./node_modules/vitest/vitest.mjs run');
  expect(packageJson.devDependencies.rollup).toBe('npm:@rollup/wasm-node@4.60.1');
  expect(packageJson.dependencies['@emnapi/core']).toBe('1.9.2');
  expect(packageJson.dependencies['@emnapi/runtime']).toBe('1.9.2');
  expect(packageJson.dependencies.env).toBe('file:./vendor/env-shim');
});
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run: `node ./node_modules/vitest/vitest.mjs run tests/toolchain-config.test.ts tests/next-build-runtime.test.ts` from `apps/web`

Expected: FAIL because `apps/web/next.config.ts` does not exist yet and `next/wasm/@next/swc-wasm-nodejs/wasm.js` still cannot resolve a working `env` module.

- [ ] **Step 3: Write the minimal tracked implementation**

```ts
// apps/web/next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  experimental: {
    useWasmBinary: true,
  },
};

export default nextConfig;
```

```json
// apps/web/package.json
{
  "name": "gaokao-agent-web",
  "private": true,
  "scripts": {
    "dev": "node ./node_modules/next/dist/bin/next dev",
    "build": "node ./node_modules/next/dist/bin/next build",
    "test": "node ./node_modules/vitest/vitest.mjs run"
  },
  "dependencies": {
    "@emnapi/core": "1.9.2",
    "@emnapi/runtime": "1.9.2",
    "env": "file:./vendor/env-shim",
    "next": "15.4.0",
    "react": "19.1.0",
    "react-dom": "19.1.0",
    "server-only": "^0.0.1"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.9.1",
    "@testing-library/react": "^16.3.2",
    "@types/node": "^22.15.3",
    "@types/react": "^19.1.0",
    "jsdom": "^29.0.2",
    "rollup": "npm:@rollup/wasm-node@4.60.1",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.5.0",
    "vitest": "^1.3.0"
  }
}
```

```json
// apps/web/vendor/env-shim/package.json
{
  "name": "env",
  "private": true,
  "main": "index.js"
}
```

```js
// apps/web/vendor/env-shim/index.js
const { createNapiModule } = require('@emnapi/core');
const { createContext } = require('@emnapi/runtime');

const napiModule = createNapiModule({
  context: createContext(),
  filename: 'next-swc-wasm-nodejs',
});

module.exports = {
  ...napiModule.imports.env,
  ...napiModule.imports.napi,
};
```

Run: `npm install` from `apps/web`

Expected: `apps/web/package-lock.json` updates to include `@emnapi/core`, `@emnapi/runtime`, and the local `env` package.

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run: `node ./node_modules/vitest/vitest.mjs run tests/toolchain-config.test.ts tests/next-build-runtime.test.ts` from `apps/web`

Expected: PASS with the new Next config present and the wasm bindings import succeeding.

- [ ] **Step 5: Commit**

```bash
git add apps/web/next.config.ts apps/web/package.json apps/web/package-lock.json apps/web/tests/toolchain-config.test.ts apps/web/tests/next-build-runtime.test.ts apps/web/vendor/env-shim/package.json apps/web/vendor/env-shim/index.js
git commit -m "feat(web): add wasm build runtime shim"
```

### Task 2: Track Babel Cleanup Verification And Prove The Full Build Path

**Files:**
- Create: `scripts/verify-web-babelrc.ps1`

- [ ] **Step 1: Add the Babel cleanup verifier**

```powershell
# scripts/verify-web-babelrc.ps1
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$babelConfigPath = Join-Path $repoRoot 'apps\web\.babelrc'

if (Test-Path $babelConfigPath) {
  throw "Expected apps/web/.babelrc to be removed"
}
```

- [ ] **Step 2: Run the verifier to confirm the stale Babel config stays removed**

Run: `powershell -ExecutionPolicy Bypass -File .\scripts\verify-web-babelrc.ps1` from the repo root

Expected: PASS with no output.

- [ ] **Step 3: Run the full web verification path**

Run: `node ./node_modules/vitest/vitest.mjs run` from `apps/web`

Expected: PASS for the full web test suite.

Run: `node ./node_modules/next/dist/bin/next build` from `apps/web`

Expected: PASS, proving the tracked wasm build path works on this machine without restoring `.babelrc`.

- [ ] **Step 4: Commit**

```bash
git add scripts/verify-web-babelrc.ps1
git commit -m "chore(web): track babel cleanup verifier"
```
