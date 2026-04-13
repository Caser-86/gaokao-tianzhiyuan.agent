# Web Build Environment Design

## Summary

`apps/web` currently passes its Vitest suite but cannot complete `next build` on this Windows workstation. The failure is environmental, not caused by `apps/web/.babelrc`: native SWC loading is blocked by local application control, and Next's wasm fallback fails before compilation completes. This subproject adds a repository-owned build path so `apps/web` can build reproducibly on this machine without relying on hand-edited `node_modules`.

## Goals

- Make `apps/web` build successfully with `node ./node_modules/next/dist/bin/next build` on this workstation.
- Keep `apps/web/.babelrc` removed if the build no longer depends on it.
- Express the workaround in tracked project files, not local `node_modules` mutations.
- Preserve the already-working Vitest workflow for `apps/web`.

## Non-Goals

- Reworking public or admin page behavior.
- Optimizing production build performance.
- Solving generic Next.js build portability for every possible environment.
- Refactoring unrelated web tooling beyond what the build fix requires.

## Current Findings

- `apps/web/.babelrc` deletion does not change the build outcome.
- Native SWC loading fails because the machine blocks `@next/swc-win32-x64-msvc`.
- Next's wasm fallback then fails while loading `apps/web/node_modules/next/wasm/@next/swc-wasm-nodejs/wasm.js`, which requires `env`.
- The existing test toolchain is already normalized and passes with the current dependency set.

## Recommended Approach

Add a minimal tracked Next configuration that explicitly steers this workspace toward a supported wasm-based build path on this machine. If the wasm path still requires a small compatibility shim for `env`, add that shim in tracked configuration so the build remains reproducible after a clean install. Keep the change set narrow: only the files needed to make `build` succeed and to document or verify that `.babelrc` stays removed.

## Architecture

### Build Configuration

- Add a tracked Next config file under `apps/web` if one does not already exist.
- Use that config to prefer the wasm compiler path in this constrained Windows environment.
- Keep the configuration focused on compiler loading; do not mix in unrelated routing, image, or experimental page behavior.

### Compatibility Shim

- If the wasm path still fails because `require('env')` is unresolved, introduce the smallest tracked compatibility layer needed to satisfy that import.
- Prefer a repository-owned alias or shim file over patching installed packages.
- Keep the shim isolated so it can be removed cleanly if a future Next update fixes the issue.

### Babel Cleanup

- Leave `apps/web/.babelrc` deleted.
- Keep a lightweight verification script that fails if `.babelrc` returns unexpectedly.
- Treat `.babelrc` removal as complete only once both tests and `next build` pass without it.

## Verification

The implementation is complete when all of the following hold:

- `powershell -ExecutionPolicy Bypass -File .\scripts\verify-web-babelrc.ps1` passes.
- `node ./node_modules/vitest/vitest.mjs run` passes from `apps/web`.
- `node ./node_modules/next/dist/bin/next build` passes from `apps/web`.
- No manual edits under `apps/web/node_modules` are required after install.

## Risks And Mitigations

- Next's internal wasm loading behavior may change across patch releases.
  - Mitigation: keep the workaround minimal and repository-scoped so it is easy to revisit.
- A compatibility shim could accidentally affect runtime code paths outside build.
  - Mitigation: scope the shim to the build/compiler import path only.
- The issue may partly reflect machine policy that cannot be fully overridden in repo code.
  - Mitigation: verify the fix with the exact local build command before claiming success.
