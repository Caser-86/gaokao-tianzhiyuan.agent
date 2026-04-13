# Platform Success CTA Copy Design

## Summary

Refine the homepage platform product CTA copy so it describes the actual interaction more clearly.

The current success-state button language is based on “selection”, while the real behavior is that chosen products are added into the entitlement preview below. The CTA should reflect that more directly.

## Goals

- Make product CTA copy match the actual preview behavior.
- Keep the existing interaction model unchanged.
- Improve the success-state language without changing tracking or API behavior.

## Non-Goals

- Changing event names or analytics payloads
- Reworking the entitlement preview interaction flow
- Adding a new comparison UI
- Changing platform API contracts

## Recommended Approach

Update the homepage platform product button copy from a generic selection phrase to a preview-oriented phrase:

- unselected: `\u52a0\u5165\u80fd\u529b\u9884\u89c8{product.name}`
- selected: `\u5df2\u52a0\u5165\u80fd\u529b\u9884\u89c8{product.name}`

This is the best fit for the current behavior because clicking a product does not start checkout or open a separate compare view. It simply adds that product to the capability preview state below.

## Alternatives Considered

### Keep `\u9009\u62e9 / \u53d6\u6d88\u9009\u62e9`

This is functional, but it describes an internal state toggle rather than the user-facing outcome.

### Use `\u52a0\u5165\u80fd\u529b\u5bf9\u6bd4`

This sounds product-like, but it overpromises. The current UI shows a merged entitlement preview rather than a true side-by-side comparison.

## Current State

The product card CTA currently behaves like this:

- click -> product slug joins the selected set
- selected set -> entitlement preview request updates

But the button copy still says `\u9009\u62e9 / \u53d6\u6d88\u9009\u62e9`, which is technically correct but vague about what the user is building.

## Architecture

### `apps/web/components/public/platform-homepage-shelf.tsx`

This component should keep the same toggle logic and event tracking.

Only the CTA label logic changes:

- unselected label becomes preview-oriented
- selected label becomes a selected-preview state

### `apps/web/tests/platform-homepage-shelf.test.tsx`

The button queries and any copy assertions should be updated to the new wording.

One additional assertion should verify that a selected product switches to the selected-preview label.

## UI Behavior

### Unselected product

CTA label:

- `\u52a0\u5165\u80fd\u529b\u9884\u89c8{product.name}`

### Selected product

CTA label:

- `\u5df2\u52a0\u5165\u80fd\u529b\u9884\u89c8{product.name}`

The button remains a toggle and keeps the same `aria-pressed` behavior.

## Testing Strategy

### Updated tests

- `apps/web/tests/platform-homepage-shelf.test.tsx`
  - queries use the new CTA wording
  - selected state updates the button label
  - existing entitlement preview behavior remains covered

### Verification

- targeted Vitest run for the shelf test
- full `apps/web` Vitest run
- `next build` in `apps/web`

## Risks And Mitigations

### Risk: wording still feels too long

Mitigation:
- keep the change scoped to copy only
- if needed, iterate later after seeing it in the real UI

### Risk: CTA text and preview semantics drift again

Mitigation:
- base wording on the current actual behavior, not future plans

## Completion Criteria

- Homepage platform CTA copy no longer uses the generic selection wording.
- CTA text reflects the entitlement preview behavior.
- Shelf tests cover the new button wording and selected-state label change.
- `apps/web` tests and build pass.
