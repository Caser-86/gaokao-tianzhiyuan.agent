# Platform Homepage Integration Design

## Summary

`apps/api` already exposes a small platform surface for product catalog, entitlement evaluation, and event intake, but `apps/web` does not consume any of it. This subproject connects the public homepage to the existing platform API by adding a minimal product shelf and lightweight client-side event tracking for homepage interactions.

## Goals

- Render platform product data on the public homepage using the existing `/api/platform/products` endpoint.
- Track a small set of homepage interactions through the existing `/api/platform/events` endpoint.
- Keep the integration aligned with the current public-page structure and testing style.
- Avoid introducing auth, checkout, or membership state in this iteration.

## Non-Goals

- Building a purchase flow or payment integration.
- Wiring `/api/platform/entitlements/evaluate` into the homepage.
- Adding analytics storage, dashboards, retries, or event batching.
- Redesigning the public homepage layout beyond the minimum needed to surface products.

## Recommended Approach

Add a small platform API client in `apps/web/lib`, extend the homepage to fetch product catalog data alongside the existing public content payloads, and introduce one focused client component that renders product CTA elements and posts fire-and-forget tracking events. Reuse the current homepage shell instead of adding new routes or global client state.

## Architecture

### Data Flow

- `apps/web/app/page.tsx` remains the server entrypoint for the homepage.
- The homepage fetches platform products in parallel with `getSearchEntry()`, `listSchools()`, and `listMajors()`.
- Product data is passed into a small public-facing component that renders a simple product shelf.
- User clicks on quick prompts and product CTA buttons trigger non-blocking event submissions to `/api/platform/events`.

### Web Client Boundaries

- Add a server-only platform client module for reading product data.
- Add a browser-safe event helper for posting interaction events.
- Keep event tracking isolated to a small client component so the rest of the homepage stays server-rendered.
- Reuse existing public components where possible; only add new components for platform-specific UI.

### Event Scope

The first tracked interactions should stay small and obvious:

- quick prompt click
- product CTA click

Each event payload should continue to fit the existing platform API:

- `event_name`
- `step`
- `metadata`

Suggested event names:

- `quick_prompt_clicked`
- `product_cta_clicked`

Suggested `step` values:

- `homepage_masthead`
- `homepage_product_shelf`

### Error Handling

- If product catalog loading fails, the homepage should still render its existing public content sections.
- Product shelf failures should degrade locally instead of turning the whole homepage into an error state.
- Event tracking should be fire-and-forget; failed event posts should not block navigation or user interaction.

## Testing Strategy

- Add web client tests for the new platform API helpers.
- Extend homepage tests to verify product shelf rendering when platform data is available.
- Add client component tests for event submission behavior using mocked `fetch`.
- Keep API validation focused on the existing `apps/api/tests/test_platform_api.py`; no new API behavior is required for this subproject.

## Risks And Mitigations

- Existing platform copy currently contains encoding issues in API fixtures.
  - Mitigation: normalize only the strings needed for homepage display in this implementation rather than widening scope into a full content cleanup.
- Adding client event tracking to the homepage can accidentally force too much of the page to the client.
  - Mitigation: isolate tracking to a small dedicated client component.
- A platform fetch failure could reduce homepage resilience if handled at the page level.
  - Mitigation: treat product loading as an optional panel with its own fallback state.
