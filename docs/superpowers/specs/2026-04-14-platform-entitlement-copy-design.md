# Platform Entitlement Copy Design

## Summary

Replace raw entitlement keys in the homepage entitlement preview with user-readable Chinese copy, while keeping the API contract unchanged.

The Web app will own a small, static entitlement label map so the preview can explain platform capabilities in plain language without expanding the current API scope.

## Goals

- Make entitlement preview output understandable to end users.
- Keep the existing platform entitlement API unchanged.
- Centralize entitlement copy in one reusable Web module.
- Provide a safe fallback for unknown entitlement keys.

## Non-Goals

- Changing the FastAPI entitlement response shape
- Adding CMS-driven or database-driven copy management
- Localizing the entitlement copy into multiple languages
- Reworking the product shelf interaction model

## Recommended Approach

Add a dedicated `platform-entitlement-labels` module in `apps/web/lib` that maps entitlement keys to display copy.

The homepage product shelf will use this module to transform raw entitlement keys into:

- a user-facing title
- a short explanatory description
- the original key for fallback or debugging

This keeps copy decisions out of the UI component and avoids growing the API surface area.

## Alternatives Considered

### Inline copy mapping inside the homepage shelf

This is fast, but it couples entitlement meaning to a single component and becomes awkward as soon as another page or admin surface needs the same labels.

### API-driven display labels

This would make the front end thinner, but it would also turn a simple copy improvement into a server-contract change. That is too much scope for the current iteration.

## Display Model

Each entitlement key should resolve to a display object with these fields:

- `title`
- `description`
- `rawKey`

The first two fields are user-facing. `rawKey` is preserved so unknown capabilities can still be rendered safely.

## Initial Mapping Scope

The first version only needs to cover the entitlement keys already returned by the current platform service:

- `school_basic_access`
- `major_basic_access`
- `risk_alert_access`
- `school_deep_dive_access`
- `major_deep_dive_access`
- `region_compare_access`

This keeps the change tightly aligned to the current API output.

## Unknown Key Behavior

Unknown entitlement keys must still render.

Recommended fallback behavior:

- title: `更多平台能力`
- description: `该能力已开通，详细说明即将补充。`
- rawKey: original entitlement key

The shelf can show the fallback title and description, and optionally keep the raw key visible in smaller text for transparency and debugging.

## Architecture

### `apps/web/lib/platform-entitlement-labels.ts`

New module responsible for converting raw entitlement keys into user-facing copy.

Responsibilities:

- store the known entitlement copy map
- expose a single lookup function
- return a fallback object for unknown keys

Recommended public API:

```ts
export type PlatformEntitlementCopy = {
  title: string;
  description: string;
  rawKey: string;
};

export function getPlatformEntitlementCopy(key: string): PlatformEntitlementCopy;
```

### `apps/web/components/public/platform-homepage-shelf.tsx`

Continues to own entitlement preview rendering, but stops rendering raw keys directly for known capabilities.

Responsibilities after this change:

- map entitlement keys through `getPlatformEntitlementCopy`
- render user-facing title and description in the preview area
- preserve fallback behavior for unknown keys

## UI Behavior

### Known entitlement keys

Render each entitlement as a small descriptive item:

- title as the primary text
- description as supporting copy

### Unknown entitlement keys

Render the fallback title and description, and keep the raw key visible as a secondary detail.

This avoids silent data loss when the API introduces a new key before the Web mapping is updated.

## Testing Strategy

### New tests

- `apps/web/tests/platform-entitlement-labels.test.ts`
  - known key returns expected title and description
  - unknown key returns fallback copy and preserves `rawKey`

### Updated tests

- `apps/web/tests/platform-homepage-shelf.test.tsx`
  - entitlement preview assertions switch from raw keys to user-facing copy
  - unknown key case is covered

### Verification

- targeted Vitest run for the label module and shelf tests
- full `apps/web` Vitest run
- `next build` in `apps/web`

## Risks And Mitigations

### Risk: copy becomes duplicated across components

Mitigation:
- keep all entitlement copy in the dedicated labels module

### Risk: new API entitlements appear without mapped copy

Mitigation:
- return a robust fallback object for unknown keys

### Risk: too much copy logic in the shelf

Mitigation:
- keep the shelf focused on rendering and interaction
- keep key-to-copy transformation inside the helper module

## Completion Criteria

- Homepage entitlement preview no longer shows raw keys for known capabilities.
- A dedicated Web label module exists for entitlement copy.
- Unknown keys render with safe fallback copy.
- Shelf tests and label tests cover both known and unknown cases.
- `apps/web` tests and build pass.
