# Featured Content Date Preview Design

## Summary

Extend the admin featured-content preview so operators can inspect the rotation result for one explicitly chosen date.

The project already supports:

- manual featured-school and featured-major toggles
- independent school and major rotation rules
- a today preview
- a next preview
- a seven-day schedule preview

That means the system already has enough information to answer a slightly different operational question:

- what will be shown on one specific date I care about?

This feature should keep that answer lightweight, read-only, and consistent with the same API-side rotation logic already used by the homepage and existing admin previews.

## Goals

- Let operators select one date in the admin UI.
- Show the featured-school result for that date.
- Show the featured-major result for that date.
- Keep the feature read-only.
- Reuse the existing date-based rotation helper.

## Non-Goals

- Editing rotation rules from the date-preview block
- Multiple-date comparison views
- Calendar widgets beyond a basic date input
- Client-side recomputation of rotation results
- A separate admin page for date preview

## Recommended Approach

Continue using the existing `GET /api/admin/featured-content` endpoint and support an optional query parameter:

- `preview_date=YYYY-MM-DD`

When the query parameter is present and valid, the response should include:

- `preview.selected_date`

That object should use the same shape as one `schedule` day:

- `date`
- `weekday`
- `schools`
- `majors`

This is the best first version because it:

- keeps all admin preview variants in one payload
- avoids duplicating rotation logic in TypeScript
- fits naturally into the current server-rendered admin page
- is easy for operators to understand and use

## Alternatives Considered

### Compute the date preview in the web admin layer

This would duplicate the rotation algorithm in TypeScript and increase drift risk between admin and public behavior.

### Add a separate preview-by-date endpoint

This would work, but it introduces another route and another fetch path for data that still belongs to the existing featured-content admin payload.

### Create a dedicated date-preview page

This makes the feature heavier than it needs to be. The current admin page already has the right context for this preview.

## Current State

Right now the admin featured-content payload includes:

- school configuration
- major configuration
- school rotation rules
- major rotation rules
- today preview
- next preview
- seven-day schedule preview

The service layer already knows how to compute a preview entry for an arbitrary date. The missing piece is exposing that result for one chosen date and wiring it into the admin page.

## API Changes

### Existing endpoint: `GET /api/admin/featured-content`

Support optional query parameter:

- `preview_date=YYYY-MM-DD`

Extend `preview` to optionally include:

```json
{
  "preview": {
    "today": {},
    "next": {},
    "schedule": [],
    "selected_date": {
      "date": "2026-04-20",
      "weekday": "周一",
      "schools": [],
      "majors": []
    }
  }
}
```

### Design Rules

- `preview.selected_date` must use the same shape as a single `schedule` record.
- If `preview_date` is absent, `preview.selected_date` may be omitted or `null`.
- If `preview_date` is valid, `preview.selected_date` must be derived from the same API-side rotation logic used by public featured lists.

## Service Design

### `apps/api/app/services/featured_content.py`

The service layer should keep using the existing arbitrary-date preview helper.

That means:

- parse the requested date once
- if valid, pass it into the same helper used to build schedule entries
- if absent, skip selected-date generation
- if invalid, return a clear validation signal to the router

The important boundary is:

- the service computes date-preview items
- the router validates request input and maps output into response models

## Input Validation

### Valid date

If `preview_date` is a valid ISO date string:

- return `preview.selected_date`

### Missing date

If `preview_date` is absent:

- this is not an error
- do not include a selected-date result

### Invalid date

If `preview_date` is not a valid ISO date string:

- do not fail the entire admin page
- surface a local date-preview error that the page can render in the selected-date block

Recommended error copy:

- `预览日期格式无效`

## Web Admin UI

### Admin page structure

Keep the existing:

- today preview sections
- next preview sections
- seven-day schedule preview section

Add one new lightweight block:

- `指定日期预览`

Inside it, render:

- a date input
- a submit button
- a selected-date result area

### Interaction model

Use query-parameter-driven server rendering:

- initial page: `/admin`
- selected date page: `/admin?preview_date=2026-04-20`

This keeps the feature simple and consistent with the rest of the server-rendered admin page.

### Result display

When a valid date is selected, show:

- `该日展示学校`
- `该日展示专业`

Each list item should show:

- name
- slug

### Empty state

If a selected date has no schools or no majors, show:

- `该日没有展示学校`
- `该日没有展示专业`

### No-selection state

If no date is selected:

- show the input and submit button
- do not show a result list
- optionally show one short helper line

Recommended helper copy:

- `选择一个日期查看当天轮换结果`

## Architecture

### `apps/api/app/routers/admin.py`

Accept optional `preview_date` query input and include optional `selected_date` in the response model.

### `apps/api/app/services/featured_content.py`

Expose a helper that returns a preview entry for a chosen date.

### `apps/web/lib/admin-featured-content-api.ts`

Map optional `selected_date` into camelCase admin types.

### `apps/web/app/(admin)/admin/page.tsx`

Read `searchParams.preview_date`, pass it to the admin API client, and render the result.

### `apps/web/components/admin/dashboard-shell.tsx`

Render the date form, helper/error states, and selected-date preview block.

## Error Handling

### Admin featured-content fetch fails

- Continue using the existing page-level error block.

### Invalid selected date

- Do not treat this as a full-page failure.
- Render a local message in the date-preview block:
  - `预览日期格式无效`

### No selected date

- Do not show an error.
- Only show the helper copy.

## Testing Strategy

### API tests

Verify:

- valid `preview_date` returns `preview.selected_date`
- returned schools and majors match the chosen date's rotation window
- missing `preview_date` does not fail
- invalid `preview_date` returns a clear validation signal or response shape consistent with the chosen strategy

### Web tests

Verify:

- admin page renders the date input and submit button
- page renders selected-date preview when `searchParams.preview_date` is present
- page renders helper copy when no date is selected
- page renders local invalid-date error copy when needed
- selected-date empty states render explicitly

### Verification

- focused `apps/api` admin API tests
- focused `apps/web` admin API and page tests
- full `apps/web` Vitest run
- `next build`

## Risks And Mitigations

### Risk: selected-date preview diverges from schedule entries

Mitigation:

- build selected-date preview from the same service-layer helper used for schedule entries

### Risk: invalid input breaks the whole admin page

Mitigation:

- keep invalid-date handling local to the selected-date preview block

## Completion Criteria

- Admin featured-content supports `preview_date`.
- Valid requests return `preview.selected_date`.
- Admin page includes a `指定日期预览` block with date input and submit button.
- Operators can inspect the featured schools and majors for one chosen date.
- Invalid input stays local to the date-preview block.
- API tests, admin tests, full web tests, and build pass.
