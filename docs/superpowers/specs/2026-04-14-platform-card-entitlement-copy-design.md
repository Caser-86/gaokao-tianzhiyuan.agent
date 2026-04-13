# Platform Card Entitlement Copy Design

## Summary

Replace raw entitlement keys in the homepage product card metadata with the same user-facing entitlement titles already used by the entitlement preview.

This keeps the homepage product shelf consistent without changing the platform API or expanding the current interaction model.

## Goals

- Remove raw entitlement keys from product card metadata for known capabilities.
- Reuse the existing Web entitlement copy helper instead of creating a second mapping path.
- Keep unknown entitlement keys visible so new API values do not disappear silently.
- Keep the entitlement preview behavior unchanged.

## Non-Goals

- Changing the FastAPI platform product payload
- Reworking the product shelf layout or interaction flow
- Adding richer product explanations inside the card metadata area
- Introducing localization infrastructure

## Recommended Approach

Update the homepage product shelf so each product card maps `product.entitlements` through the existing `platform-entitlement-labels` helper before rendering metadata chips.

Known entitlement keys will render their user-facing `title`.

Unknown entitlement keys will continue to render their raw key so the UI remains transparent when the API introduces a capability that the Web mapping does not know yet.

The entitlement preview section will stay as-is: it already shows title, description, and unknown-key fallback.

## Alternatives Considered

### Leave product cards as raw keys

This avoids any additional change, but it leaves the homepage inconsistent because the card uses internal keys while the preview uses user-facing copy.

### Show full descriptions inside each product card

This would provide more context, but it would also make each card visually heavier and duplicate the job of the entitlement preview area.

## Current State

The homepage product shelf currently has two entitlement display layers:

- product card metadata chips
- entitlement preview list

After the previous entitlement copy work, only the preview list uses the centralized label helper. The card metadata chips still render raw entitlement keys directly from the API payload.

## Architecture

### `apps/web/lib/platform-entitlement-labels.ts`

No API contract change is required.

This helper remains the single source of truth for Web-side entitlement copy. The card metadata should call the same lookup function already used by the preview list.

### `apps/web/components/public/platform-homepage-shelf.tsx`

The product card metadata area will:

- map each entitlement key through `getPlatformEntitlementCopy`
- render `title` for known keys
- render `rawKey` when the entitlement is unknown

The preview area will remain unchanged.

## UI Behavior

### Known entitlements in product cards

Render compact metadata chips using the user-facing entitlement title only.

The exact displayed titles should come from the existing `platform-entitlement-labels` helper so the cards stay aligned with the entitlement preview.

### Unknown entitlements in product cards

Render the raw key as the chip text.

This preserves visibility and makes it obvious when the Web copy map needs to be updated.

## Testing Strategy

### Updated tests

- `apps/web/tests/platform-homepage-shelf.test.tsx`
  - card metadata shows known entitlement titles
  - card metadata no longer shows known raw keys
  - unknown product entitlements still show the raw key

### Verification

- targeted Vitest run for the shelf test
- full `apps/web` Vitest run
- `next build` in `apps/web`

## Risks And Mitigations

### Risk: card and preview copy drift again

Mitigation:
- keep both surfaces on the same helper module

### Risk: unknown entitlements become hidden

Mitigation:
- continue rendering the raw key when the helper falls back

### Risk: cards become too verbose

Mitigation:
- cards use title-only chips
- preview keeps the detailed descriptions

## Completion Criteria

- Known entitlement keys no longer appear as raw strings in homepage product card metadata.
- Product cards reuse the centralized Web entitlement copy helper.
- Unknown entitlement keys still remain visible in product cards.
- Shelf tests cover the new card metadata behavior.
- `apps/web` tests and build pass.
