# Featured Content Preview Design

## Summary

Add a lightweight "today preview" to the admin featured-content payload and admin page so operators can immediately see which schools and majors are currently selected by the rotation rules.

The project already supports:

- manual featured toggles for schools and majors
- school image URLs
- independent school and major rotation rules
- public list endpoints that already return the current rotation window

That means the system knows what should appear today, but the admin side does not yet show it directly. Operators currently have to infer the result from rotation settings or inspect the public homepage. This feature should close that gap with the smallest possible addition.

## Goals

- Show which schools are featured today in the admin interface.
- Show which majors are featured today in the admin interface.
- Reuse the same API-side rotation logic that drives the public homepage.
- Keep the first version minimal and operational.

## Non-Goals

- Future-date previews
- Seven-day scheduling previews
- A dedicated preview page
- Card-style visual previews
- Preview-specific API routes

## Recommended Approach

Extend `GET /api/admin/featured-content` so it returns a new `preview` object:

- `preview.schools`
- `preview.majors`

Each preview item should contain only:

- `slug`
- `name`

The preview should be computed by reusing the same rotation result that already determines what the public school and major list endpoints return today.

This is the best first version because it is:

- fast to ship
- hard to get out of sync
- easy for operators to understand

## Alternatives Considered

### Compute preview in the Web admin layer

This would duplicate rotation logic in TypeScript and make it easier for the admin view to drift away from the API behavior.

### Create a separate admin preview endpoint

This would work, but it adds an extra route and another fetch path for a very small amount of data that already belongs to the featured-content admin payload.

### Show a seven-day schedule immediately

This would be useful eventually, but it is a bigger scope jump. The best next step is to confirm today's result first.

## Current State

Right now the admin featured-content payload includes:

- school config rows
- major config rows
- school rotation rules
- major rotation rules

The public list endpoints already return the current rotation window, but the admin page does not surface that result.

## API Changes

### Existing endpoint: `GET /api/admin/featured-content`

Extend the response with:

```json
{
  "preview": {
    "schools": [
      {
        "slug": "southeast-university",
        "name": "东南大学"
      }
    ],
    "majors": [
      {
        "slug": "clinical-medicine",
        "name": "临床医学"
      }
    ]
  }
}
```

### Design rules

- `preview.schools` must come from the same API-side current school rotation window used by `/api/public/schools`
- `preview.majors` must come from the same API-side current major rotation window used by `/api/public/majors`
- The preview payload should stay minimal:
  - no image URL
  - no summary
  - no tags
  - no rotation metadata per item

## Web Admin UI

### Admin page structure

Add two lightweight sections to the current admin page:

- `今日展示学校`
- `今日展示专业`

### Display format

Each section should show a simple list of:

- entity name
- entity slug

This should remain operational and text-first. The point is confirmation, not presentation polish.

### Empty state

If a preview list is empty:

- school preview shows `当前没有可展示学校`
- major preview shows `当前没有可展示专业`

## Architecture

### `apps/api/app/services/featured_content.py`

Should expose helpers that return the current visible school and major items, or reuse the existing helpers that already compute them.

### `apps/api/app/routers/admin.py`

Should map the current visible school and major items into a new `preview` field on the featured-content response.

### `apps/web/lib/admin-featured-content-api.ts`

Should map the new `preview` payload into camelCase admin types.

### `apps/web/app/(admin)/admin/page.tsx`

Should load the preview alongside the existing featured-content configuration.

### `apps/web/components/admin/dashboard-shell.tsx`

Should render the two preview sections under the rotation controls.

## Error Handling

### Admin side

- If the featured-content payload fails entirely, continue using the existing page-level error state.
- The preview should not introduce a second independent error state in this version.

### Empty results

- An empty preview is valid and should render the explicit empty-state text instead of being treated as an error.

## Testing Strategy

### API tests

Verify:

- featured-content response includes `preview`
- `preview.schools` matches the current school rotation window
- `preview.majors` matches the current major rotation window

### Web tests

Verify:

- admin page renders `今日展示学校`
- admin page renders `今日展示专业`
- preview entries show name and slug
- empty preview lists render the expected empty-state text

### Verification

- focused `apps/api` admin API tests
- focused `apps/web` admin API and page tests
- full `apps/web` Vitest run
- `next build`

## Risks And Mitigations

### Risk: admin preview disagrees with homepage behavior

Mitigation:

- compute preview from the same API-side rotation result used by the public endpoints
- avoid front-end recomputation

### Risk: payload grows unnecessarily

Mitigation:

- keep preview items to `slug` and `name`
- do not include full card data

### Risk: this turns into a scheduling dashboard

Mitigation:

- explicitly limit the first version to today's preview only
- keep future previews out of scope

## Completion Criteria

- Admin featured-content payload includes a `preview` object.
- Admin page shows `今日展示学校` and `今日展示专业`.
- Preview items match the current rotation result.
- Empty preview states are explicit.
- API tests, admin tests, full Web tests, and build pass.
