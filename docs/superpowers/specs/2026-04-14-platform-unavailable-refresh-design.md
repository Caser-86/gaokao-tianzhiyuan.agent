# Platform Unavailable Refresh Design

## Summary

Make the homepage platform unavailable panel’s secondary action behave like a true retry instead of a generic homepage link.

This keeps the current local degraded-state design, but makes the `\u7a0d\u540e\u518d\u8bd5` action match the user’s expectation by refreshing the current route data.

## Goals

- Turn the unavailable panel’s retry-later action into a real refresh action.
- Preserve the existing primary action that sends users to the school section.
- Keep homepage data branching unchanged.
- Limit the change to the unavailable panel interaction layer.

## Non-Goals

- Reworking the homepage platform data loading flow
- Adding client-side loading states for retries
- Introducing local retry counters, backoff, or toast notifications
- Changing analytics behavior in this iteration

## Recommended Approach

Convert `apps/web/components/public/platform-unavailable-panel.tsx` into a lightweight client component and use the Next app-router refresh mechanism for the secondary action.

Recommended behavior:

- primary action: keep the anchor link to `#school-catalog`
- secondary action: trigger `router.refresh()`

This keeps the action aligned with the label `\u7a0d\u540e\u518d\u8bd5` without introducing new client-side fetch orchestration.

## Alternatives Considered

### Keep `Link href="/"` as-is

This is minimal, but it reads like navigation rather than retry. It does not match the user’s mental model of “try loading this again”.

### Use `window.location.reload()`

This would work, but it is heavier than necessary and less idiomatic in a Next app-router surface.

### Add a local fetch retry just for the platform panel

This would create a more complex state machine in exchange for very little extra value at the current stage.

## Current State

The unavailable panel currently renders:

- a school-section anchor
- a second link pointing to `/`

That second action is usable, but it is semantically weak because it behaves like home navigation instead of a retry operation.

## Architecture

### `apps/web/components/public/platform-unavailable-panel.tsx`

This component should become a client component.

Responsibilities after the change:

- render the unavailable copy
- keep the school anchor as a normal link
- use `useRouter()` and `router.refresh()` for the retry action

### `apps/web/app/page.tsx`

No behavioral changes required.

The page should continue to decide whether to render:

- `PlatformHomepageShelf`
- `PlatformUnavailablePanel`

## UI Behavior

### Primary action

- label: `\u5148\u53bb\u67e5\u5b66\u6821`
- behavior: jump to `#school-catalog`

### Secondary action

- label: `\u7a0d\u540e\u518d\u8bd5`
- behavior: refresh the current route

The visual treatment can stay close to the current degraded-state panel. The main change is interaction semantics, not layout.

## Testing Strategy

### Updated tests

- `apps/web/tests/platform-unavailable-panel.test.tsx`
  - school action remains an anchor link
  - retry action triggers `router.refresh()`

### Existing homepage tests

- `apps/web/tests/public-pages.test.tsx`
  - continue verifying that the unavailable panel appears on platform failures
  - continue verifying that both actions are visible

### Verification

- targeted Vitest run for unavailable panel and homepage tests
- full `apps/web` Vitest run
- `next build` in `apps/web`

## Risks And Mitigations

### Risk: client conversion expands component scope

Mitigation:
- keep the panel state-free
- only add router access for the retry action

### Risk: retry action feels invisible in tests

Mitigation:
- explicitly mock `next/navigation` and assert `router.refresh()` is called

### Risk: homepage behavior changes accidentally

Mitigation:
- leave `apps/web/app/page.tsx` unchanged
- keep page tests focused on render branching only

## Completion Criteria

- The unavailable panel still shows both actions.
- `\u5148\u53bb\u67e5\u5b66\u6821` remains an anchor to `#school-catalog`.
- `\u7a0d\u540e\u518d\u8bd5` triggers a real route refresh.
- Panel tests and homepage tests pass.
- `apps/web` tests and build pass.
