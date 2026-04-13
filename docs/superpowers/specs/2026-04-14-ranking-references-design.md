# Ranking References Design

## Summary

Add a structured `ranking_references` field to both school and major detail content so detail pages can show reference ranking cards with source context.

The current catalog data supports summaries, tags, and narrative sections, but it has no first-class way to represent rankings, subject evaluations, or list-based references that readers may want to use as one input into a decision. We should add a lightweight structured field that supports both schools and majors without turning this into a full ranking product.

## Goals

- Support ranking and list references on both school and major detail pages.
- Keep the data model structured enough to show source, year, result label, and optional citation context.
- Make the UI clearly present these items as references, not as the only truth.
- Reuse the existing public catalog data flow from `data/catalog.json` through API to web pages.

## Non-Goals

- Building a standalone rankings index or leaderboard page
- Adding ranking-based search, filtering, or sorting
- Adding admin editing flows for ranking references in this iteration
- Normalizing every ranking source into a new backend table

## Recommended Approach

Add a `ranking_references` array to both school and major detail records in `data/catalog.json`, pass it through the public API detail responses, and render a dedicated `参考榜单` section on detail pages only when the array is present.

Each reference should support:

- `source`: ranking or evaluation source name
- `year`: year string or number
- `label`: the main result text users should notice
- `scope`: optional context for the ranking dimension
- `note`: optional explanatory note
- `url`: optional source link

This is the best fit for the current architecture because it keeps the implementation inside the existing catalog-content pipeline while giving rankings their own structured presentation instead of hiding them inside freeform text sections.

## Alternatives Considered

### Put ranking references into existing `sections`

This is fast, but it collapses sourced references into narrative content and makes it harder to render source, year, and link consistently.

### Build a dedicated rankings domain model

This could support full ranking experiences later, but it is too heavy for the current need. We do not need ranking aggregation, sorting, or cross-entity indexing yet.

## Current State

The current school and major detail content includes:

- summary text
- tags or recommended regions
- narrative sections
- related schools or majors

But there is no supported field for:

- source-backed rankings
- year-specific list references
- ranking result labels
- links to original ranking sources

## Data Model

### `ranking_references`

Add an optional `ranking_references` field to both school and major detail records.

Each item should follow this shape:

```json
{
  "source": "软科中国大学排名",
  "year": 2025,
  "label": "全国第 15 名",
  "scope": "综合类高校",
  "note": "用于综合实力参考，不等同于具体专业优势。",
  "url": "https://example.com/rankings/2025"
}
```

Field guidance:

- `source`: required
- `year`: required
- `label`: required
- `scope`: optional
- `note`: optional
- `url`: optional

This shape supports both numeric rankings and non-numeric outcomes such as:

- `学科评估 A-`
- `全国前 10%`
- `华东地区重点参考榜单`

## API Changes

### Public catalog detail responses

The school detail and major detail responses should include `ranking_references` when present.

This applies to:

- school detail response
- major detail response

The list endpoints do not need this field in the first iteration. Ranking references are detail-page context, not list-card metadata.

## Web UI

### School detail page

Render a `参考榜单` section when `ranking_references` exists and has at least one item.

Each item should show:

- source and year together
- label as the main line
- optional scope
- optional note
- optional link text such as `查看来源`

### Major detail page

Render the same `参考榜单` section with the same card pattern.

### Empty behavior

If `ranking_references` is missing or empty, do not render the section at all.

## Presentation Guidance

The section title should explicitly frame rankings as references:

- `参考榜单`

This avoids overstating authority and leaves room for mixed sources with different methodologies.

The UI should not imply:

- official endorsement
- universal comparability across sources
- one definitive ranking truth

## Architecture

### `data/catalog.json`

Add `ranking_references` examples to at least one school and one major so the feature is exercised end to end.

### API catalog services and schemas

Update the public catalog model parsing and response serialization so the new field is carried through detail endpoints.

### Web detail pages

Render ranking references in a dedicated section using the existing detail-page composition pattern. If a small shared renderer is helpful, keep it focused on ranking references only.

## Testing Strategy

### API tests

- school detail endpoint returns `ranking_references` when present
- major detail endpoint returns `ranking_references` when present

### Web tests

- school detail page renders `参考榜单` when references exist
- major detail page renders `参考榜单` when references exist
- source links render when `url` is present
- section is omitted when references are absent

### Verification

- targeted API tests for public catalog detail responses
- targeted web tests for school and major detail pages
- full `apps/web` Vitest run
- relevant `apps/api` pytest run
- `next build` in `apps/web`

## Risks And Mitigations

### Risk: ranking sources use different methodologies

Mitigation:
- label the section as `参考榜单`
- support optional `scope` and `note` for context

### Risk: ranking references clutter detail pages

Mitigation:
- render them only on detail pages
- omit the section entirely when there is no data

### Risk: future admin workflows need a different shape

Mitigation:
- keep the field structured now so it is easy to move into reviewed content flows later

## Completion Criteria

- School and major detail data support `ranking_references`.
- Public detail APIs include the new field.
- School and major pages render a `参考榜单` section when ranking references exist.
- Ranking items can show source, year, label, and optional context.
- Tests cover API and web rendering behavior.
