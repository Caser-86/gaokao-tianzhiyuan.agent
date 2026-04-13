# Platform Shelf Copy Consistency Design

## Summary

Align the homepage product shelf tests with the same Chinese product naming and description semantics used by the real platform product data.

This is a test-and-copy consistency cleanup, not a platform API contract change.

## Goals

- Make shelf tests use the same user-facing product language as the real platform products.
- Keep test assertions focused on user-visible behavior instead of fragile placeholder strings.
- Preserve the current product API contract and shelf interaction behavior.

## Non-Goals

- Changing the FastAPI platform product payload shape
- Introducing a shared platform fixture system
- Reworking the homepage shelf UI
- Adding localization infrastructure

## Recommended Approach

Update `apps/web/tests/platform-homepage-shelf.test.tsx` so its local product fixtures use the same Chinese naming and description intent as the platform products returned by the API service.

The tests should still focus on behavior:

- entitlement labels render correctly
- CTA interactions work
- entitlement preview states behave correctly

The change is primarily about removing misleading English placeholder content from the shelf tests.

## Current State

The production product data served by the platform API already uses Chinese product names and descriptions.

The homepage shelf tests still define local mock products with English placeholders such as:

- `Insight Weekly`
- `Deep Dive Pack`

That mismatch makes the tests less representative of the real UI even though the component behavior is correct.

## Architecture

### `apps/web/tests/platform-homepage-shelf.test.tsx`

This file remains the only place that needs to change.

Responsibilities after this cleanup:

- define local mock products using realistic Chinese copy
- keep behavior-oriented assertions intact
- update button assertions to use the same product naming shown to users

No production file changes are required unless the test structure reveals a small readability improvement that directly supports the cleanup.

## Test Behavior

### Product fixture copy

The local test fixtures for:

- `insight-weekly`
- `deep-dive-pack`

should be updated to match the Chinese product naming and description style already represented in the API layer.

### Assertions

Tests should continue to assert:

- card entitlement copy behavior
- unknown entitlement fallback behavior
- entitlement preview loading and error behavior
- event tracking with the correct product slug

Button-triggering assertions should use the updated user-facing product names.

## Testing Strategy

### Updated tests

- `apps/web/tests/platform-homepage-shelf.test.tsx`
  - uses realistic Chinese product fixtures
  - keeps behavior coverage unchanged

### Verification

- targeted Vitest run for the shelf test
- full `apps/web` Vitest run
- `next build` in `apps/web`

## Risks And Mitigations

### Risk: tests become too tied to long literal copy

Mitigation:
- update fixture copy, but keep assertions focused on the minimum user-visible text needed for each scenario

### Risk: cleanup drifts into API or production copy editing

Mitigation:
- keep the scope limited to shelf test fixtures and any directly related assertions

## Completion Criteria

- Shelf tests no longer use English placeholder product names for the main homepage products.
- Shelf tests remain behavior-focused and continue to cover the current interaction model.
- `apps/web` tests and build pass.
