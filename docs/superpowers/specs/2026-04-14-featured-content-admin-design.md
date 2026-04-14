# Featured Content Admin Design

## Summary

Add a lightweight admin-managed featured-content layer so operators can manually decide which schools and majors appear on the public homepage, while also maintaining a school image URL for cards that should show a photo.

The current public catalog is entirely file-driven through `data/catalog.json`, which makes content demos possible but keeps homepage curation locked in code and data files. We should introduce a small operations layer that lets the admin side manually switch featured schools and majors without taking on the larger scope of scheduling, CMS-style content editing, or automatic image scraping.

## Goals

- Let the admin side manually control which schools appear on the public homepage.
- Let the admin side manually control which majors appear on the public homepage.
- Let the admin side maintain a school image URL for featured school cards.
- Keep the first version simple enough to operate without introducing a new scheduler or crawler.

## Non-Goals

- Automatic time-based rotation of schools or majors
- Crawling school sites for images
- Full CMS editing for school and major summaries, sections, or ranking references
- Drag-and-drop ordering
- Professional media asset management

## Recommended Approach

Add a separate featured-content configuration file, managed through the admin UI, that stores:

- which school slugs are currently featured
- which major slugs are currently featured
- which featured schools have a manually maintained image URL

Then update the public list endpoints so homepage content is driven by that configuration instead of simply exposing the full catalog.

This is the best first step because it moves control into the admin surface without forcing the project to solve scheduling, image crawling, or full content editing all at once.

## Alternatives Considered

### Continue expanding `catalog.json`

This keeps everything file-based, but it does not solve the real operations problem. The homepage would still require manual file edits for every curation change.

### Add `is_featured` directly to each catalog entity

This works technically, but it mixes durable content data with short-lived homepage curation decisions. It also makes future scheduling harder because there is no dedicated configuration layer to extend.

### Build full scheduling and image ingestion now

This would move closer to the final product vision, but it introduces too much complexity at once: job execution, fallback rules, crawl reliability, and provenance concerns.

## Current State

The public side currently behaves like this:

- homepage school and major cards are populated from public API list endpoints
- those list endpoints are backed by `data/catalog.json`
- schools and majors are content entities, not curated homepage picks
- schools do not currently expose a homepage image field
- the admin side already has a review dashboard shell and admin API patterns, but not a content-curation interface

## Data Model

### New file: `data/featured-content.json`

The first version should introduce a dedicated featured-content file with this shape:

```json
{
  "schools": [
    {
      "slug": "southeast-university",
      "is_featured": true,
      "hero_image_url": "https://example.com/images/southeast-campus.jpg"
    }
  ],
  "majors": [
    {
      "slug": "clinical-medicine",
      "is_featured": true
    }
  ]
}
```

### Design rules

- The featured-content file is the source of truth for homepage inclusion.
- `slug` must correspond to an entity already present in `data/catalog.json`.
- School image handling is manual:
  - the admin side maintains a URL
  - the system does not crawl or upload media in this version
- Majors do not need an image field in this version.

## API Changes

### Admin API

Add small admin endpoints for featured-content management:

- `GET /api/admin/featured-content`
- `POST /api/admin/featured-content/schools/{slug}`
- `POST /api/admin/featured-content/majors/{slug}`

These endpoints should:

- read the current featured-content configuration
- update one school or one major at a time
- preserve existing entries when another row is edited

### Public API

Update the public list endpoints so they only return featured entities:

- `GET /api/public/schools`
- `GET /api/public/majors`

For schools, include:

- `hero_image_url`

The public response should remain light. It should not expose admin-only flags such as `is_featured`.

## Admin UI

### Admin page structure

Extend the existing admin page with two simple sections:

- `学校展示配置`
- `专业展示配置`

### School configuration rows

Each row should show:

- school name
- slug
- whether it is currently featured
- an input for `hero_image_url`
- a save action

### Major configuration rows

Each row should show:

- major name
- slug
- whether it is currently featured
- a save action

### Interaction model

- One row, one form, one save action
- Successful saves refresh the admin page
- The admin view is intentionally plain and operational, not a polished CMS

This is the right tradeoff for the first version because the main job is to unlock curation, not to optimize batch workflows.

## Public Web UI

### Homepage school cards

If a featured school has `hero_image_url`, render the image in the school card.

If the image URL is missing:

- keep the current text-first card
- do not fail the page

### Homepage major cards

Majors remain text-first in this version. No image support is needed yet.

### Content scope

Homepage cards should only show entities returned by the filtered public API lists. That means the admin side becomes the practical control point for homepage curation.

## Architecture

### `data/featured-content.json`

Stores the current featured-content configuration.

### `apps/api/app/services/catalog.py`

Reads featured-content configuration, filters school and major list responses, and maps `hero_image_url` into school summaries.

### `apps/api/app/routers/admin.py`

Adds featured-content admin endpoints using the existing admin auth pattern.

### `apps/web/lib/public-content-api.ts`

Extends school summaries to accept `heroImageUrl`.

### `apps/web/lib/admin-review-api.ts` or a new admin config client

Add a small admin-side client for featured-content reads and updates.

### `apps/web/app/(admin)/admin/page.tsx`

Loads featured-content configuration and renders the new school/major curation sections.

### `apps/web/components/admin/dashboard-shell.tsx`

Extends the admin shell to render the new operational configuration panels alongside the existing review queue.

## Error Handling

### Admin side

- If featured-content configuration fails to load, show a clear admin error block.
- If a row update fails, keep the rest of the page usable and surface a localized row or page-level error.

### Public side

- Missing `hero_image_url` should never be treated as an error.
- If featured-content configuration is unreadable at the API layer, prefer a safe empty list over exposing unintended content.

## Testing Strategy

### API tests

Verify:

- featured-content admin endpoints require admin auth
- reading featured content returns current school and major configuration
- updating a school can change `is_featured` and `hero_image_url`
- updating a major can change `is_featured`
- public school and major list endpoints only return featured entities
- public school list items expose `hero_image_url`

### Web admin tests

Verify:

- admin page renders featured school and major configuration rows
- school rows include an image URL input
- major rows do not include an image URL input
- existing review-queue rendering remains intact

### Public web tests

Verify:

- homepage school cards render images when `heroImageUrl` is present
- homepage still renders text-only school cards when it is absent
- homepage only renders featured schools and majors provided by the API

### Verification

- focused `apps/api` admin and public API tests
- focused `apps/web` admin and homepage tests
- full `apps/web` Vitest run
- `next build` in `apps/web`

## Risks And Mitigations

### Risk: configuration drifts from catalog entities

Mitigation:

- validate slugs against `catalog.json` when updating featured-content entries
- reject unknown slugs at the admin API layer

### Risk: homepage becomes too dependent on image availability

Mitigation:

- treat school images as optional enhancement
- keep text-first rendering as the fallback

### Risk: this creates pressure for scheduling immediately

Mitigation:

- isolate curation state in `featured-content.json`
- treat scheduling as a later extension of the same configuration layer

## Completion Criteria

- Admin can manually feature or unfeature schools and majors.
- Admin can manually maintain a school image URL.
- Public homepage school and major cards are driven by featured-content configuration.
- Featured school cards render a photo when available and fall back gracefully when not.
- API tests, admin tests, homepage tests, and build pass.
