# Featured Content Seven-Day Preview Design

## Summary

Extend the existing admin featured-content preview so operators can see not only today's featured schools and majors, but also the next seven days of rotation results.

The project already supports:

- manual featured-school and featured-major toggles
- independent school and major rotation rules
- a lightweight admin "today preview"

That means the system already knows how to compute the current visible window. This feature should reuse that same API-side logic to expose a simple seven-day schedule for operations planning.

## Goals

- Show the next seven days of featured-school results in the admin UI.
- Show the next seven days of featured-major results in the admin UI.
- Include explicit date and weekday labels for each day.
- Reuse the same rotation algorithm that drives the public homepage and current admin preview.

## Non-Goals

- Thirty-day scheduling views
- A dedicated scheduling page
- Drag-and-drop timeline editing
- Export or download features
- Client-side recomputation of rotation results

## Recommended Approach

Extend the existing `GET /api/admin/featured-content` payload so `preview` includes:

- `today`
- `schedule`

`preview.today` keeps the current lightweight result for the current day.

`preview.schedule` returns seven records, one for each day starting from today, where each record includes:

- `date`
- `weekday`
- `schools`
- `majors`

Each school and major item remains minimal:

- `slug`
- `name`

This is the best first version because it:

- keeps admin and public behavior aligned
- avoids duplicating rotation logic in TypeScript
- gives operators a useful planning view without turning the admin into a scheduling product

## Alternatives Considered

### Compute the seven-day schedule in the web admin layer

This would duplicate the rotation algorithm in TypeScript and make it easier for the admin view to drift away from the public API behavior.

### Add a separate schedule endpoint

This would work, but it introduces another route and another fetch path for data that still belongs to the existing featured-content admin payload.

### Show only a "next rotation" preview

This is cheaper than a seven-day preview, but less useful for operations. The project already has "today"; the next meaningful step is a short planning horizon.

## Current State

Right now the admin featured-content payload includes:

- school configuration
- major configuration
- school rotation rules
- major rotation rules
- today's preview

The API already has a single source of truth for featured rotation. The missing piece is a short forward-looking schedule.

## API Changes

### Existing endpoint: `GET /api/admin/featured-content`

Extend the `preview` object from a flat "today" structure to this shape:

```json
{
  "preview": {
    "today": {
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
    },
    "schedule": [
      {
        "date": "2026-04-14",
        "weekday": "周二",
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
    ]
  }
}
```

### Design Rules

- `preview.today.schools` and `preview.today.majors` must keep the same semantics as the current preview.
- `preview.schedule` must contain exactly seven entries, starting from the current date.
- Each `schedule` entry must use the same API-side rotation logic as the public school and major list endpoints.
- The payload stays minimal:
  - no image URLs
  - no summaries
  - no tags
  - no per-item rotation metadata

## Service Design

### `apps/api/app/services/featured_content.py`

The service layer should expose helpers that compute featured items for an arbitrary date, not only for today.

That means:

- keep the current rotation algorithm as the single source of truth
- reuse `_current_rotation_window(..., today=...)`
- add a helper that builds one preview entry for a specific date
- add a helper that builds the seven-day schedule by iterating from today through six days ahead

The important boundary is:

- the service computes schedule records
- the router only maps those records into response models

## Web Admin UI

### Admin page structure

Keep the existing:

- `今日展示学校`
- `今日展示专业`

Then add a new section:

- `未来 7 天轮换预览`

### Display format

Within that section, render seven day groups. Each group should show:

- date
- weekday
- school names and slugs
- major names and slugs

The layout should stay text-first and operational. This is an operations planning view, not a marketing preview.

### Empty state

If a given day has no schools or no majors:

- show an explicit empty-state line for that subsection
- do not leave the area blank

Recommended copy:

- `当天没有可展示学校`
- `当天没有可展示专业`

## Architecture

### `apps/api/app/services/featured_content.py`

Add schedule-building helpers that return:

- today's preview
- a seven-day schedule

### `apps/api/app/routers/admin.py`

Expand the `preview` response model so it includes:

- `today`
- `schedule`

### `apps/web/lib/admin-featured-content-api.ts`

Map the nested preview payload into camelCase admin types.

### `apps/web/app/(admin)/admin/page.tsx`

Load the seven-day schedule from the existing featured-content fetch.

### `apps/web/components/admin/dashboard-shell.tsx`

Render the new seven-day schedule section under the existing today preview.

## Error Handling

### Admin side

- If the featured-content payload fails entirely, continue using the existing page-level error block.
- The seven-day schedule should not introduce a separate error state in this version.

### Empty results

- A day with no schools is valid and should render the explicit school empty-state copy.
- A day with no majors is valid and should render the explicit major empty-state copy.

## Testing Strategy

### API tests

Verify:

- featured-content response includes `preview.today`
- featured-content response includes `preview.schedule`
- `preview.schedule` has seven entries
- each entry includes `date`, `weekday`, `schools`, and `majors`
- schedule entries follow the current rotation progression when rotation is enabled

### Web tests

Verify:

- admin page renders `未来 7 天轮换预览`
- schedule rows show date and weekday
- schedule rows show school and major entries
- per-day empty states render explicitly when needed

### Verification

- focused `apps/api` admin API tests
- focused `apps/web` admin API and page tests
- full `apps/web` Vitest run
- `next build`

## Risks And Mitigations

### Risk: seven-day preview drifts away from homepage behavior

Mitigation:

- compute the schedule entirely in the API service layer
- reuse the same rotation helper used by the public list behavior

### Risk: payload grows too quickly

Mitigation:

- keep schedule entries minimal
- only include `date`, `weekday`, `schools`, and `majors`

### Risk: the admin starts becoming a full scheduler too early

Mitigation:

- explicitly limit the first version to a read-only seven-day preview
- keep editing in the existing rule forms only

## Completion Criteria

- Admin featured-content payload includes `preview.today` and `preview.schedule`.
- `preview.schedule` returns seven day records with date and weekday labels.
- Admin page shows `未来 7 天轮换预览`.
- Operators can see which schools and majors are scheduled for each of the next seven days.
- Empty schedule sublists are explicit.
- API tests, admin tests, full web tests, and build pass.
