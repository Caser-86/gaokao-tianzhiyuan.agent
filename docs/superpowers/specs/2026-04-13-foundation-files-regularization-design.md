# Foundation Files Regularization Design

## Goal

Regularize the currently untracked public web foundation files and platform API foundation files so the repository reflects the code and assets the project already depends on at runtime and in tests.

## Current Context

- The repository now has an API-backed public web flow and an API-backed admin review flow.
- Several files that support the public site and platform API still exist only as untracked workspace files.
- Those files are not optional scaffolding. They are part of the running system:
  - public web layout and styling
  - public presentational components
  - TypeScript and Next.js app metadata files
  - seed catalog data used by the API
  - platform API router, service, and tests
- Keeping those files untracked means the project can appear to work locally while the repository remains incomplete.

## Scope

This design covers:

1. Bringing the public web foundation files under version control
2. Bringing the platform API foundation files under version control
3. Adding or updating `.gitignore` so local build artifacts are not committed
4. Verifying that the tracked files are exercised by real tests

This design does not cover:

- New product features
- Public site redesign
- Platform API expansion beyond the already-present routes
- Catalog schema redesign
- Content editing workflows

## Recommended Approach

Treat this as a regularization pass, not a refactor. Track the missing foundation files, make only the smallest correctness or hygiene adjustments required to keep them coherent with the current codebase, and verify them with the existing targeted API and web tests.

This keeps the repository honest without turning a cleanup task into a new product initiative.

## Alternatives Considered

### Option A: Add the files exactly as-is

Commit the untracked files with no content adjustments.

Pros:

- fastest path
- minimal churn

Cons:

- may lock in small inconsistencies that are easy to correct now
- does not address ignore rules for local artifacts

### Option B: Regularize with minimal cleanup (recommended)

Track the files, add `.gitignore`, and make only the smallest changes needed for consistency with the already-running project.

Pros:

- repository becomes complete and reproducible
- avoids over-refactoring
- keeps current test coverage meaningful

Cons:

- slightly larger than a pure add-only commit

### Option C: Regularize and refactor structure

Track the files and also redesign public component boundaries, styling organization, and platform service structure.

Pros:

- potentially cleaner long-term layout

Cons:

- too much scope for a regularization pass
- raises risk and review overhead without direct product benefit

## Architecture

### Public web foundation layer

The following files form the current public-site foundation and should be tracked as a coherent unit:

- `apps/web/app/layout.tsx`
- `apps/web/app/globals.css`
- `apps/web/components/public/page-section-renderer.tsx`
- `apps/web/components/public/search-entry.tsx`
- `apps/web/tests/public-content.test.tsx`
- `apps/web/tsconfig.json`
- `apps/web/next-env.d.ts`

Responsibilities:

- define the app-wide public layout baseline
- provide the shared visual language for the public pages
- render reusable presentational blocks already used by the public routes
- provide the TypeScript and Next.js metadata required by the app workspace

This work should not redesign these files. It should only ensure they are formally part of the repository and remain aligned with current imports and tests.

### Catalog data foundation

`data/catalog.json` should be tracked as a project data asset.

Responsibilities:

- supply the source data used by the public catalog API
- anchor the sample content currently exercised by the public API tests

This file is not a temporary fixture anymore. The API depends on it, so the repository should reflect that dependency.

### Platform API foundation layer

The following files form the current platform API baseline and should be tracked together:

- `apps/api/app/routers/platform.py`
- `apps/api/app/services/platform.py`
- `apps/api/tests/test_platform_api.py`

Responsibilities:

- expose platform-facing product catalog endpoints
- evaluate entitlement bundles
- accept platform event payloads
- verify those routes with API tests

These files should be treated as the initial platform API foundation, not as an invitation to broaden the platform scope during this pass.

### Ignore rules

Add or update `.gitignore` at the repository root.

Responsibilities:

- ignore build outputs such as `.next/`
- ignore dependency directories such as `node_modules/`
- ignore local caches such as pytest caches and Python bytecode
- avoid swallowing tracked source files

The result should be that repository state reflects intentional source assets rather than machine-local outputs.

## Data And Dependency Boundaries

### Public runtime boundary

The public web app now depends on:

- server-rendered page entry files
- presentational public components
- API responses from `apps/api`
- `data/catalog.json` indirectly through the API

This means all of those supporting files must be tracked. Otherwise the runtime dependency chain is incomplete in version control.

### Platform baseline boundary

The platform routes already included in `app.main` depend on the platform router and service modules. Those modules should therefore be regularized together with their tests so the main application import graph is fully represented in the repository.

## Error Handling

This regularization pass should keep behavior stable.

- Do not add new fallback behavior
- Do not change platform route semantics
- Do not alter public page error handling introduced in the previous sub-project unless a tracked-file inconsistency requires it

If a minimal cleanup is required for consistency, it should preserve existing external behavior.

## Testing Strategy

### Web verification

Run the existing targeted web suite that covers:

- toolchain configuration
- public content API client
- public public-component rendering
- public page rendering and error behavior

These tests already prove the tracked public foundation files are part of the active code path.

### API verification

Run:

- platform API tests
- public catalog API tests

This confirms the regularized API foundation files are active and coherent with the current application wiring.

### Git verification

Review `git status` before and after the work.

Success means:

- the intended foundation files become tracked
- local build artifacts remain ignored
- unrelated generated directories are not accidentally added

## File Impact

Expected implementation work will likely touch:

- `.gitignore`
- `apps/api/app/routers/platform.py`
- `apps/api/app/services/platform.py`
- `apps/api/tests/test_platform_api.py`
- `apps/web/app/layout.tsx`
- `apps/web/app/globals.css`
- `apps/web/components/public/page-section-renderer.tsx`
- `apps/web/components/public/search-entry.tsx`
- `apps/web/tests/public-content.test.tsx`
- `apps/web/tsconfig.json`
- `apps/web/next-env.d.ts`
- `data/catalog.json`

The likely outcome for many of these files is that they are added as tracked files with little or no content change.

## Success Criteria

The work is complete when:

- the currently used public web foundation files are tracked in git
- the currently used platform API foundation files are tracked in git
- `data/catalog.json` is tracked as a project data asset
- `.gitignore` prevents obvious local build artifacts from being added
- targeted API and web test suites still pass
- the repository no longer depends on these foundation files existing only in a local workspace
