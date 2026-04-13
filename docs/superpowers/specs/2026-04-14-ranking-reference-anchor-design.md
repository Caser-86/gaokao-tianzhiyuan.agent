# Ranking Reference Anchor Design

## Summary

Add a lightweight in-page anchor entry on school and major detail pages so users can jump directly from the masthead to the existing `参考榜单` section.

The ranking-reference module now exists, has trust-copy, and is discoverable from homepage cards, but detail pages still rely on users noticing the section lower on the page. We should tighten the discovery flow without introducing a heavier table of contents or any new data requirements.

## Goals

- Help users quickly reach ranking-reference content after landing on a detail page.
- Keep the detail-page masthead simple and consistent with existing link-row actions.
- Reuse the existing ranking-reference section instead of duplicating content.

## Non-Goals

- Building a full page table of contents
- Adding sticky navigation
- Changing ranking-reference data or API responses
- Reworking the ranking-reference card layout

## Recommended Approach

Add a `查看参考榜单` anchor link to the detail-page masthead only when ranking references exist, and give the ranking-reference section a stable `id="ranking-references"`.

This is the best fit because it improves discoverability with minimal UI weight, preserves the existing page structure, and avoids introducing new client-side behavior.

## Alternatives Considered

### Do nothing

This keeps the page minimal, but users still have to notice the ranking module on their own after scrolling.

### Add a full in-page directory

This would make deep-linking stronger, but it is too heavy for the current amount of content and would complicate otherwise simple detail pages.

## Current State

School and major detail pages already render:

- a masthead with metadata and related-entity links
- content sections through `PageSectionRenderer`
- ranking references through `RankingReferenceList`

The ranking-reference section currently has no stable anchor target, and the masthead gives no hint that this reference content exists.

## Web UI Changes

### Masthead link row

When `rankingReferences.length > 0`, append:

- `查看参考榜单`

The link should target:

- `#ranking-references`

This link belongs in the existing `link-row` so it feels like a peer to the related-school and related-major shortcuts.

### Ranking reference section

The `参考榜单` section should expose:

- `id="ranking-references"`

This makes the anchor stable for both school and major detail pages.

## Architecture

### `apps/web/components/public/ranking-reference-list.tsx`

Add the section `id` to the existing outer `<section>`.

### `apps/web/app/schools/[slug]/page.tsx`

Render the masthead anchor only when `school.rankingReferences.length > 0`.

### `apps/web/app/majors/[slug]/page.tsx`

Render the same masthead anchor only when `major.rankingReferences.length > 0`.

## Testing Strategy

### Page tests

Verify:

- school detail pages with ranking references show `查看参考榜单` linking to `#ranking-references`
- school detail pages without ranking references omit that link
- major detail pages with ranking references show the same link

These checks belong in the existing public page tests because the behavior is page-level discoverability, not ranking-card internals.

### Verification

- targeted `apps/web` page tests
- full `apps/web` Vitest run
- `next build` in `apps/web`

## Risks And Mitigations

### Risk: masthead actions get noisy

Mitigation:

- only show the anchor when ranking references exist
- keep the label short and action-oriented

### Risk: anchor drift

Mitigation:

- define a single stable section id in `RankingReferenceList`
- reuse that same id from both detail pages

## Completion Criteria

- School and major detail pages with ranking references show `查看参考榜单`.
- The link jumps to `#ranking-references`.
- Detail pages without ranking references do not show the entry.
- Existing detail-page behavior, tests, and build remain green.
