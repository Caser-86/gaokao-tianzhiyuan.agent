# Ranking Reference Listing Badge Design

## Summary

Add a lightweight `含参考榜单` discovery hint to school and major listing cards so users can more easily find detail pages that contain ranking-reference content.

The ranking-reference module now exists on detail pages and has seeded content for multiple schools and majors, but there is no signal from the listing pages that some detail pages include this extra reference material. We should add a small listing-level hint without making the cards heavier or adding new click targets.

## Goals

- Help users discover which school and major detail pages include ranking-reference content.
- Keep school and major listing cards lightweight.
- Avoid sending full ranking-reference payloads in list responses.
- Preserve the current “whole card is the link” interaction pattern.

## Non-Goals

- Rendering ranking details directly on list cards
- Adding a dedicated `查看榜单参考` button
- Changing detail page behavior
- Returning full `ranking_references` arrays in list endpoints

## Recommended Approach

Add a boolean field to public list responses:

- schools: `has_ranking_references`
- majors: `has_ranking_references`

Then render a small `含参考榜单` badge in list-card metadata only when that field is true.

This is the best fit for the current product shape because it improves discoverability without increasing card complexity or overloading listing payloads.

## Alternatives Considered

### Static badge without API support

This would require duplicating knowledge on the web side or heuristically inferring which entities have ranking references. That would drift quickly.

### Dedicated list-card button

This makes the signal more explicit, but it adds interaction noise and competes with the current full-card navigation pattern.

## Current State

Listing cards currently show:

- school cards
  - name
  - summary
  - region, city, tags
- major cards
  - name
  - summary
  - discipline, recommended regions

They do not currently indicate whether the destination detail page contains:

- ranking-reference content
- any extra “reference” style information

## API Changes

### School list response

Add:

- `has_ranking_references: bool`

### Major list response

Add:

- `has_ranking_references: bool`

This field should be derived from whether `ranking_references` exists and is non-empty in the underlying catalog record.

## Web UI

### School listing cards

When `has_ranking_references` is true, add a small metadata tag:

- `含参考榜单`

### Major listing cards

Use the same tag:

- `含参考榜单`

### Placement

Append the tag into the existing `meta` row so it feels like a lightweight content attribute rather than a new action.

## Architecture

### `apps/api/app/services/catalog.py`

Update the school and major list serializers to include `has_ranking_references`.

### `apps/web/lib/public-content-api.ts`

Extend summary types and list payload mapping to include `hasRankingReferences`.

### `apps/web/app/page.tsx`

Render the badge in school and major cards only when the corresponding summary item has `hasRankingReferences`.

## Testing Strategy

### API tests

Verify list responses include:

- `has_ranking_references: true` for seeded entities with ranking references
- `has_ranking_references: false` for entities without them

### Web tests

Verify homepage listing cards:

- show `含参考榜单` on seeded school/major examples
- do not show the badge for items without ranking references

### Verification

- targeted `apps/api` public catalog tests
- targeted homepage web tests
- full `apps/web` Vitest run
- `next build` in `apps/web`

## Risks And Mitigations

### Risk: the badge makes cards feel noisy

Mitigation:
- keep the copy short
- place it inside existing metadata instead of adding a new row or button

### Risk: list and detail data drift

Mitigation:
- derive `has_ranking_references` directly from the same catalog records that power detail pages

## Completion Criteria

- School and major list responses include `has_ranking_references`.
- Homepage listing cards show `含参考榜单` only for entities with ranking references.
- Existing list-card navigation remains unchanged.
- API tests, web tests, and build pass.
