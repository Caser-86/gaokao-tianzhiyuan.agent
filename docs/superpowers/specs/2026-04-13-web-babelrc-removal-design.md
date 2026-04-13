# Web Babelrc Removal Design

## Goal

Verify whether `apps/web/.babelrc` is required by the current web workspace, and remove it if the web test and build pipeline do not depend on it.

## Current Context

- The foundation-file regularization work reduced the untracked workspace residue to a single file: `apps/web/.babelrc`.
- That file currently contains only:

```json
{
  "presets": ["next/babel"]
}
```

- The current targeted web test suite passes without any evidence that this file is necessary.
- Because Babel configuration can affect build behavior more than test behavior, the final decision should be based on both testing and building.

## Scope

This design covers:

1. Verifying whether `apps/web/.babelrc` is required by the current project
2. Removing `apps/web/.babelrc` if the web workspace works without it
3. Confirming removal with fresh web test and build verification

This design does not cover:

- Introducing a replacement Babel configuration
- Changing Next.js compiler behavior
- Refactoring frontend code
- Broader workspace cleanup beyond this single residual file

## Recommended Approach

Treat `.babelrc` as a suspect residual configuration, not as an assumed requirement. Remove it, then run the current web verification set plus a real `next build`. If both succeed, keep the file deleted. If build verification fails, stop and investigate the specific compiler dependency before deciding on any replacement configuration.

This approach favors evidence over inertia and avoids formalizing configuration that may no longer serve a purpose.

## Alternatives Considered

### Option A: Track `.babelrc` as-is

Commit the file and treat it as part of the web baseline.

Pros:

- lowest immediate risk
- no build-path change

Cons:

- adds long-term maintenance surface without evidence it is needed
- may pin the project to an unnecessary Babel layer

### Option B: Validate and remove `.babelrc` if unnecessary (recommended)

Delete the file and prove the web workspace still tests and builds successfully.

Pros:

- repository stays lean
- removes unexplained configuration
- bases the decision on real build evidence

Cons:

- requires an extra build verification step

### Option C: Ignore the file

Leave it untracked and unresolved.

Pros:

- no immediate work

Cons:

- keeps the repository inconsistent with the workspace
- leaves future contributors guessing whether the file matters

## Architecture

### Configuration boundary

This work is about configuration ownership, not behavior redesign.

- if `.babelrc` is unnecessary, it should not remain in the workspace
- if it is required, that requirement should be proven by build failure and handled intentionally in a separate follow-up

### Verification boundary

Use two types of evidence:

- web tests for current application behavior
- `next build` for compiler and bundling behavior

The file should only survive if one of those verification steps demonstrates a real need.

## Error Handling

If removing `.babelrc` causes build or test failures:

- do not guess at replacement configuration
- inspect the actual failure first
- only add configuration back if the failure proves the file is required

If removal causes no failures, keep the deletion and do not add compensating configuration.

## Testing Strategy

Run from `apps/web`:

- the current targeted Vitest suite:
  - `tests/toolchain-config.test.ts`
  - `tests/public-content-api.test.ts`
  - `tests/public-pages.test.tsx`
  - `tests/public-content.test.tsx`
- `node ./node_modules/next/dist/bin/next build`

This is the minimum proof needed to say the file is not required by the current workspace.

## File Impact

Expected implementation work will likely touch:

- `apps/web/.babelrc`

The likely outcome is deletion, not modification.

## Success Criteria

The work is complete when:

- `apps/web/.babelrc` is either deleted or explicitly proven necessary
- the targeted web Vitest suite still passes
- `apps/web` still builds successfully with `next build`
- the repository no longer carries or tolerates this unexplained residual config file without evidence
