# Featured Content Rotation Design

## Summary

Extend the existing featured-content admin layer so schools and majors can rotate automatically on a configurable cadence instead of relying only on manual show or hide toggles.

The current system already lets operators:

- choose which schools appear on the homepage
- choose which majors appear on the homepage
- maintain a manual school image URL

That gives us a stable curation layer. The next step is to let operators decide how featured items rotate over time without introducing a scheduler, a background job runner, or a separate planning system.

## Goals

- Let the admin side configure automatic rotation for schools.
- Let the admin side configure automatic rotation for majors.
- Let school and major rotation rules be configured independently.
- Let operators control rotation frequency in days.
- Let operators control how many items appear in the rotation window.
- Let operators control the ordered sequence used for rotation.
- Keep manual featured toggles in place as the eligibility layer.

## Non-Goals

- Background cron jobs or scheduled file rewrites
- Drag-and-drop ordering UI
- Calendar-style campaign planning
- Start and end dates for future rotation plans
- Automatic image crawling
- Per-item publish windows

## Recommended Approach

Keep the existing `data/featured-content.json` file and extend it with a dedicated `rotation` section for schools and majors.

The public API should not expose new rotation endpoints. Instead, it should compute the currently visible school and major lists at request time by combining:

- the manually featured entities
- the configured ordered slug list
- the configured frequency in days
- the configured window size
- the current date

This is the best next step because it adds daily rotation behavior without needing a task runner or a job queue. It also preserves the existing manual curation workflow: operators still decide which items are eligible, and rotation only chooses which eligible items are shown today.

## Alternatives Considered

### Rewrite featured content on a timer

This would require a scheduler or background task system to update files or database state on a cadence. That is more operational complexity than the current MVP needs.

### Randomly select featured schools and majors

Random selection would be easy to compute, but it is harder for operators to predict, review, and explain. Ordered rotation is a better fit for homepage operations.

### Add a full campaign planner

This would support richer scheduling, but it would expand the project into a much larger content-operations system before the simpler daily rotation layer has proven useful.

## Current State

The current featured-content flow works like this:

- `data/featured-content.json` stores manual school and major inclusion state
- schools can also carry `hero_image_url`
- the admin API reads and updates one school or major row at a time
- the public school and major list endpoints only return manually featured entities
- the homepage renders whatever the public list endpoints return

This means manual curation already exists, but time-based rotation does not.

## Data Model

### Existing file: `data/featured-content.json`

Extend the file with a new `rotation` object:

```json
{
  "schools": [
    {
      "slug": "southeast-university",
      "is_featured": true,
      "hero_image_url": ""
    }
  ],
  "majors": [
    {
      "slug": "clinical-medicine",
      "is_featured": true
    }
  ],
  "rotation": {
    "schools": {
      "enabled": true,
      "frequency_days": 1,
      "window_size": 4,
      "ordered_slugs": [
        "southeast-university",
        "west-china-medical-center",
        "zhejiang-university",
        "wuhan-university"
      ]
    },
    "majors": {
      "enabled": true,
      "frequency_days": 2,
      "window_size": 6,
      "ordered_slugs": [
        "clinical-medicine",
        "computer-science",
        "finance",
        "law"
      ]
    }
  }
}
```

### Design rules

- `rotation.schools` and `rotation.majors` are independent.
- `enabled` controls whether automatic rotation is active for that entity type.
- `frequency_days` means how many calendar days elapse before the window advances.
- `window_size` means how many entities are visible at once.
- `ordered_slugs` defines the rotation order.
- Manual `is_featured` remains the eligibility gate.
- If a slug appears in `ordered_slugs` but is not manually featured, it stays in the rule but is ignored by current-window calculation until it becomes featured.

## Rotation Calculation

### Execution model

Use request-time calculation in the API service layer.

The service should:

1. collect all manually featured entities of the requested type
2. apply the rotation rule if it is enabled and valid
3. return only the current window

### Window calculation

Use a fixed reference date inside the service as the rotation anchor.

Recommended first version:

- define a single constant date in the API service, for example `2026-04-14`
- use that same anchor for both schools and majors
- treat the anchor as an implementation constant, not an admin-configurable field

Then compute:

- elapsed days since the anchor date
- rotation step = `floor(elapsed_days / frequency_days)`
- start index = `rotation step mod eligible ordered item count`

The service should then take `window_size` items from the ordered list, wrapping around when needed.

### Fallback behavior

If any of these conditions are true, fall back to the current manual-featured behavior:

- rotation is disabled
- `ordered_slugs` is empty
- no manually featured items match the ordered list
- `frequency_days < 1`
- `window_size < 1`

Fallback should be explicit in code, not accidental.

## Admin API Changes

### Existing endpoint: `GET /api/admin/featured-content`

Extend the response so it also returns:

- `rotation.schools`
- `rotation.majors`

### New endpoints

- `POST /api/admin/featured-content/rotation/schools`
- `POST /api/admin/featured-content/rotation/majors`

Each request body should include:

- `enabled`
- `frequency_days`
- `window_size`
- `ordered_slugs`

### Validation rules

- `frequency_days` must be greater than or equal to `1`
- `window_size` must be greater than or equal to `1`
- every slug in `ordered_slugs` must exist in `catalog.json`
- duplicate slugs should be rejected

If validation fails, the admin API should return a clear 422-style validation response instead of silently fixing the input.

## Public API Changes

Do not add new public routes.

The existing public routes should now return the current rotated window:

- `GET /api/public/schools`
- `GET /api/public/majors`

The public response remains intentionally simple. It should not expose:

- whether rotation is enabled
- rotation frequency
- ordered slug lists

The public side only needs the current visible entities.

## Admin UI

### Admin page structure

Extend the current admin page with two additional operational sections:

- `学校轮换规则`
- `专业轮换规则`

### Fields

Each rotation section should render:

- one checkbox for `enabled`
- one numeric input for `frequency_days`
- one numeric input for `window_size`
- one multiline textarea for `ordered_slugs`
- one save action

### Interaction model

- One section, one form, one save action
- The textarea uses one slug per line
- Successful saves refresh the admin page
- Existing school and major featured-row editing stays intact

This keeps the admin UI operational and understandable without requiring a more advanced scheduling interface yet.

## Public Web UI

The homepage should not add any new client-side rotation logic.

It should continue to:

- call the public API
- render returned schools
- render returned majors

This keeps all scheduling logic centralized in the API layer and avoids duplicating date-based behavior in the browser.

## Architecture

### `data/featured-content.json`

Stores both manual featured-content state and rotation rules.

### `apps/api/app/services/featured_content.py`

Should become the home for:

- reading and writing rotation config
- validating rotation rule slugs
- computing current rotated windows

### `apps/api/app/services/catalog.py`

Should continue to build public list responses, but it should consume the computed rotated school and major sets instead of only reading manual featured flags.

### `apps/api/app/routers/admin.py`

Should expose rotation config in the admin payload and add update endpoints for school and major rotation rules.

### `apps/web/lib/admin-featured-content-api.ts`

Should map rotation config between API snake case and web camel case.

### `apps/web/app/(admin)/admin/actions.ts`

Should add one action for school rotation updates and one action for major rotation updates.

### `apps/web/app/(admin)/admin/page.tsx`

Should load rotation config alongside the existing featured school and major configuration.

### `apps/web/components/admin/dashboard-shell.tsx`

Should render the new rotation forms beneath the existing featured-content controls.

## Error Handling

### Admin side

- If the featured-content payload fails to load, the admin page should show a clear error block.
- If saving rotation rules fails, the page should stay usable and show a clear message.
- Invalid slugs or invalid numeric values should surface as validation errors, not silent fallbacks.

### Public side

- Rotation misconfiguration should fall back to the current manual featured lists.
- Missing or partial rotation configuration should never break the homepage response.
- The homepage should not need any new special-case error handling for rotation.

## Testing Strategy

### API tests

Verify:

- admin featured-content payload includes rotation rules
- school rotation rule updates persist correctly
- major rotation rule updates persist correctly
- invalid rotation input is rejected
- public school lists return only the current rotation window when enabled
- public major lists return only the current rotation window when enabled
- public lists fall back to all manually featured entities when rotation is disabled

### Web admin tests

Verify:

- admin page renders school and major rotation forms
- rotation forms show frequency, window size, and ordered slug textareas
- save actions call the correct admin API endpoints
- existing featured row editing and review-queue rendering still work

### Public web tests

Verify:

- homepage still renders whatever the public API returns
- no additional browser-side rotation logic is introduced

### Verification

- focused `apps/api` admin and public API tests
- focused `apps/web` admin and homepage tests
- full `apps/web` Vitest run
- `next build` in `apps/web`

## Risks And Mitigations

### Risk: operators configure a rotation order that does not match featured eligibility

Mitigation:

- allow the rule to exist
- compute visibility only from currently featured items
- keep validation focused on slug existence, not current featured state

### Risk: date-based logic becomes hard to reason about

Mitigation:

- centralize rotation calculation in one API service
- use a fixed anchor date
- cover the algorithm with explicit API tests

### Risk: admin UI becomes too complex too quickly

Mitigation:

- keep the first version to checkbox, numeric inputs, and one textarea
- avoid drag-and-drop or scheduling calendars

## Completion Criteria

- Admin can configure school rotation rules independently from major rotation rules.
- Admin can control whether rotation is enabled, how often it advances, how many items display, and the ordered slug sequence.
- Public school and major lists return the current rotated window when rotation is active.
- Public lists fall back to manual featured items when rotation is disabled or invalid.
- Admin tests, API tests, homepage tests, and build pass.
