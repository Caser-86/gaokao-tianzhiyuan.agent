# Platform Entitlements Preview Design

## Summary

Add an anonymous entitlement preview to the public homepage so users can select one or more platform products and immediately see the combined capabilities returned by `/api/platform/entitlements/evaluate`.

This closes the gap between the existing product shelf and the existing entitlement evaluation API without introducing login, checkout, persistence, or account state.

## Goals

- Reuse the existing platform product catalog already shown on the homepage.
- Surface the existing entitlement evaluation API in a user-visible way.
- Keep the interaction local to the homepage product shelf.
- Keep failures isolated to the entitlement preview area.

## Non-Goals

- User accounts or authentication
- Checkout, payment, or order state
- Persisting selected products across refreshes
- URL-driven selection state
- Server-side entitlement evaluation during initial page render

## Recommended Approach

Implement a client-side multi-select entitlement preview inside the existing homepage product shelf.

Users can select one or more products from the product shelf. The shelf will call `/api/platform/entitlements/evaluate` with the selected product slugs and render the merged entitlement list below the products.

This approach best matches the capability of the existing API while keeping the scope small and the homepage architecture stable.

## Alternatives Considered

### Single-product preview only

Show entitlement output for only one selected product at a time.

This is simpler, but it underuses the existing API and hides the combined entitlement behavior that is already supported.

### Checkout-style flow

Turn the homepage into a product selection and purchase funnel.

This would expand scope into identity, persistence, payment, and post-purchase behavior, which is out of scope for the current phase.

## User Experience

### Default state

- The homepage continues to render the platform product shelf.
- No products are selected initially.
- The entitlement preview area shows a short empty-state prompt telling the user to select products to view bundled capabilities.

### Selection state

- Each product card exposes a selectable control.
- Users may select multiple products.
- Selection is local to the page session and is not persisted.

### Preview state

- When one or more products are selected, the client calls `/api/platform/entitlements/evaluate`.
- The preview area renders the merged entitlement list from the API response.
- The preview also shows which product slugs were evaluated if that helps explain the result.

### Error state

- If entitlement evaluation fails, the product shelf remains interactive.
- Only the preview area shows a local error message.
- Users can retry by changing selection again.

## Architecture

### Server-rendered responsibilities

The homepage server component continues to fetch:

- public search entry
- public school summaries
- public major summaries
- platform product catalog

The homepage also passes the platform API base URL into the client product shelf, following the already-established pattern used for platform event tracking.

### Client-rendered responsibilities

The product shelf client component owns:

- selected product slugs
- loading state for entitlement evaluation
- local error state
- rendering of the entitlement preview

This keeps interactivity localized and avoids pushing transient selection state into the server page.

## Component Boundaries

### `apps/web/app/page.tsx`

- Continues to fetch platform product data on the server.
- Passes `apiBaseUrl` and `products` into the homepage product shelf.
- Does not evaluate entitlements itself.

### `apps/web/components/public/platform-homepage-shelf.tsx`

- Remains the homepage product interaction surface.
- Gains product selection UI.
- Calls the entitlement evaluation helper when selection changes.
- Renders the entitlement preview area below the products.

### `apps/web/lib/platform-entitlements.ts`

New helper that wraps `POST /api/platform/entitlements/evaluate`.

Responsibilities:

- accept selected product slugs
- accept an optional explicit API base URL
- post the request payload
- normalize non-OK responses into thrown errors

## Data Flow

1. Server page fetches product catalog.
2. Server page passes `products` and `apiBaseUrl` to the client shelf.
3. User selects one or more products.
4. Shelf sends selected `product_slugs` to the entitlement helper.
5. Helper posts to `/api/platform/entitlements/evaluate`.
6. Shelf renders:
   - empty prompt when nothing is selected
   - loading state while the request is in flight
   - entitlement list on success
   - local error message on failure

## API Contract

### Request

`POST /api/platform/entitlements/evaluate`

```json
{
  "product_slugs": ["insight-weekly", "deep-dive-pack"]
}
```

### Response

```json
{
  "product_slugs": ["insight-weekly", "deep-dive-pack"],
  "entitlements": [
    "major_basic_access",
    "major_deep_dive_access",
    "region_compare_access",
    "risk_alert_access",
    "school_basic_access",
    "school_deep_dive_access"
  ]
}
```

## Error Handling

- Product catalog failure remains handled by the existing homepage product fallback.
- Entitlement preview failure is local to the client shelf.
- Event tracking remains best-effort and independent from entitlement evaluation.
- No entitlement error should collapse the whole homepage.

## Testing Strategy

### New tests

- `apps/web/tests/platform-entitlements.test.ts`
  - verifies the helper posts selected product slugs to the correct endpoint
  - verifies explicit API base URL overrides fallback resolution

- `apps/web/tests/platform-homepage-shelf.test.tsx`
  - selecting one product requests entitlements and renders the returned capability list
  - selecting multiple products renders merged entitlements
  - no selection shows the empty prompt
  - request failure shows a local error message

### Existing tests to update

- `apps/web/tests/public-pages.test.tsx`
  - keep homepage coverage focused on server-rendered product loading

### Verification

- targeted vitest runs for the new helper and shelf tests
- full `apps/web` vitest run
- `next build` in `apps/web`

## Risks And Mitigations

### Risk: overloading the shelf component

Mitigation:
- keep logic focused on selection, entitlement fetch, and rendering
- do not add checkout or persistence logic

### Risk: client-side API base URL drift

Mitigation:
- continue passing explicit `apiBaseUrl` from the server page into the client shelf and helper

### Risk: entitlement preview introduces noisy homepage failures

Mitigation:
- localize all entitlement request errors to the preview area only

## Completion Criteria

- Homepage product shelf supports selecting multiple products.
- Selected products trigger `/api/platform/entitlements/evaluate`.
- Returned entitlements are rendered in a dedicated preview area.
- Empty, loading, success, and local error states are covered by tests.
- `apps/web` tests and build both pass.
