# Ranking Reference Seed Data Design

## Summary

Expand the ranking-reference sample data so the new `参考榜单` module feels like a real content feature instead of a single-example proof of concept.

Right now the ranking-reference pipeline is implemented end to end, but only one school and one major have seeded ranking-reference content. We should extend that to a small but representative set of detail pages so the feature is more useful in demos and less obviously “just supported in theory.”

## Goals

- Add more seeded ranking-reference content to both school and major detail data.
- Keep the data set small, consistent, and easy to maintain.
- Exercise the reference module on more than one school and more than one major.
- Avoid changing the ranking-reference schema or UI behavior.

## Non-Goals

- Filling ranking references for every entity in the catalog
- Building a rankings content management workflow
- Changing API contracts
- Reworking the ranking-reference component

## Recommended Approach

Extend the seeded ranking-reference data to these four core entities:

- schools
  - `southeast-university`
  - `west-china-medical-center`
- majors
  - `clinical-medicine`
  - `computer-science`

Each entity should get one or two ranking references with the current structured shape.

This is the best fit for the current stage because it improves the usefulness and credibility of the feature without turning the catalog into a large manual data-entry task.

## Alternatives Considered

### Keep the current two examples only

This is the smallest option, but it leaves the feature looking thin and overly tailored to one school and one major.

### Populate the entire catalog

This sounds complete, but without a curated source list it would encourage rushed or low-quality seed content. That is not a good tradeoff right now.

## Current State

The ranking-reference module is already implemented and rendered on detail pages, but the seeded data is narrow:

- one school has ranking references
- one major has ranking references

That means the module still looks more like a feature flag than a stable content shape.

## Data Scope

### Schools

Seed ranking references for:

- `southeast-university`
- `west-china-medical-center`

### Majors

Seed ranking references for:

- `clinical-medicine`
- `computer-science`

Each of these should have at least one reference. One or two references per entity is enough for this iteration.

## Content Guidance

Each reference should continue to use the existing fields:

- `source`
- `year`
- `label`
- `scope`
- `note`
- `url`

Content should remain explicitly reference-oriented:

- no “definitive” language
- no unsupported scoring or confidence labels
- no mixing of ranking references into narrative sections

## Architecture

### `data/catalog.json`

This is the only required production-data file for this iteration.

Update the four target entities with ranking-reference sample content using the existing structure.

### API behavior

No API code changes should be required if the catalog detail service continues to return complete records.

### Web behavior

No component logic changes should be required if the detail pages already consume `rankingReferences`.

## Testing Strategy

### API tests

Expand public catalog API coverage so it verifies:

- `west-china-medical-center` returns `ranking_references`
- `computer-science` returns `ranking_references`

The existing `southeast-university` and `clinical-medicine` tests should remain.

### Web tests

Do not hard-code the entire expanded data set into page tests.

The existing detail-page rendering tests are already enough to prove that ranking references render when present and disappear when absent. The purpose of this iteration is mainly seed-data coverage, not new UI behavior.

### Verification

- targeted `apps/api` public catalog tests
- full `apps/web` Vitest run
- `next build` in `apps/web`

## Risks And Mitigations

### Risk: seed data grows inconsistently

Mitigation:
- keep the scope to four entities
- keep each entity to one or two references

### Risk: sample links look too placeholder-like

Mitigation:
- keep the schema stable now
- if needed, later do a dedicated pass to replace placeholder URLs with curated real sources

### Risk: tests become too tightly coupled to content volume

Mitigation:
- add API checks for targeted entities
- keep web tests focused on behavior, not exhaustive seed content lists

## Completion Criteria

- `southeast-university`, `west-china-medical-center`, `clinical-medicine`, and `computer-science` all have seeded `ranking_references`.
- Public catalog API tests cover the added school and major examples.
- Existing web behavior remains green.
- `apps/web` tests and build pass.
