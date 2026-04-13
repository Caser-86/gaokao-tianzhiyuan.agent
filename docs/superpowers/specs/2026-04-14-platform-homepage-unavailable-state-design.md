# Platform Homepage Unavailable State Design

## Summary

Replace the current “empty products” fallback on the homepage with an explicit platform-unavailable panel that gives the user a clear next step.

This keeps the homepage usable when the platform product API is unavailable and makes the failure state visible instead of disguising it as an empty catalog.

## Goals

- Show an explicit local degraded state when platform products fail to load.
- Keep the rest of the homepage usable.
- Give users a clear next action instead of only showing a passive error sentence.
- Avoid treating platform API failure as an empty product list.

## Non-Goals

- Adding client-side retry state management
- Redesigning the entire homepage layout
- Changing the platform API contract
- Introducing analytics changes for degraded-state actions in this iteration

## Recommended Approach

Handle platform product failure explicitly in the homepage server component and render a dedicated unavailable panel in place of the normal platform shelf.

The unavailable panel should include:

- a clear title stating that the platform service is temporarily unavailable
- a short explanation that product plans and entitlement preview cannot be loaded right now
- a primary action that lets the user continue with the homepage’s core task
- a secondary action that supports trying again later

The recommended primary action is `\u5148\u53bb\u67e5\u5b66\u6821`, implemented as an in-page anchor to the existing school section on the homepage.

The recommended secondary action is `\u7a0d\u540e\u518d\u8bd5`, implemented as a normal page refresh entry point rather than a client-side retry flow.

## Alternatives Considered

### Keep the current empty-state sentence

This is simple, but it hides the difference between “no products exist” and “the platform service failed”.

### Trigger client-side retry logic inside the shelf

This would allow a richer interaction model, but it adds unnecessary state management for a small degraded-state improvement.

## Current State

The homepage currently loads platform products like this:

- `listPlatformProducts().catch(() => ({ items: [] }))`

That means a real API failure is converted into an empty product array, and the shelf renders its generic no-products message.

This keeps the page alive, but it loses useful meaning: users cannot tell whether the service is temporarily unavailable or whether no products exist.

## Architecture

### `apps/web/app/page.tsx`

This file should explicitly distinguish between:

- platform products loaded successfully
- platform product request failed

When the request fails, the page should render the unavailable panel instead of the shelf.

### `apps/web/components/public/platform-unavailable-panel.tsx`

Recommended new component for the degraded state.

Responsibilities:

- render the unavailable title and explanation
- render a primary action pointing to the homepage school section
- render a secondary action that refreshes the current page

This keeps the homepage file focused on data branching and the panel focused on presentation.

## UI Behavior

### Success case

If platform products load successfully, the homepage continues rendering the normal platform shelf.

### Failure case

If platform products fail to load:

- the platform shelf is replaced by the unavailable panel
- school and major sections remain available
- the panel communicates that the problem is local to platform services

### Actions

Primary action:

- label: `\u5148\u53bb\u67e5\u5b66\u6821`
- behavior: jump to the school section on the homepage

Secondary action:

- label: `\u7a0d\u540e\u518d\u8bd5`
- behavior: reload the current page

## Testing Strategy

### Updated tests

- `apps/web/tests/public-pages.test.tsx`
  - homepage still renders the normal shelf when platform products load
  - homepage renders the unavailable panel when platform products fail
  - unavailable panel includes `\u5148\u53bb\u67e5\u5b66\u6821` and `\u7a0d\u540e\u518d\u8bd5`

### New tests

- `apps/web/tests/platform-unavailable-panel.test.tsx`
  - panel renders the expected title, explanation, and actions

### Verification

- targeted Vitest run for homepage and panel tests
- full `apps/web` Vitest run
- `next build` in `apps/web`

## Risks And Mitigations

### Risk: degraded state looks like a full-page error

Mitigation:
- keep the panel local to the platform section
- leave school and major content intact

### Risk: actions are decorative rather than useful

Mitigation:
- implement real navigation for both actions

### Risk: page branching becomes harder to read

Mitigation:
- keep the unavailable UI in a dedicated component

## Completion Criteria

- Homepage no longer converts platform API failure into a generic empty product state.
- A dedicated platform unavailable panel is shown on homepage platform failures.
- The panel includes a clear next-step action and a retry-later action.
- Homepage tests and panel tests cover both success and failure paths.
- `apps/web` tests and build pass.
