# Featured Content Next Rotation Preview Design

## Summary

Extend the existing admin featured-content preview so operators can see the next rotation result as a dedicated read-only block.

The project already supports:

- manual featured-school and featured-major toggles
- independent school and major rotation rules
- a lightweight admin today preview
- a seven-day rotation schedule preview

That means the system already has enough information to answer a smaller operational question:

- if the current rotation advances one step, what will be shown next?

This feature should keep that answer lightweight, explicit, and consistent with the same API-side rotation logic already used by the homepage and admin previews.

## Goals

- Show the next featured-school result in the admin UI.
- Show the next featured-major result in the admin UI.
- Keep the next preview read-only.
- Reuse the existing rotation algorithm and fallback rules.

## Non-Goals

- Buttons that trigger a manual preview state
- Editing rotation rules from the next-preview block
- New scheduling endpoints
- Alternative date pickers or custom preview dates
- Visual timeline redesigns

## Recommended Approach

Extend the existing `GET /api/admin/featured-content` payload so `preview` includes:

- `today`
- `next`
- `schedule`

`preview.next` should be a minimal object:

```json
{
  "next": {
    "schools": [
      {
        "slug": "west-china-medical-center",
        "name": "West China Medical Center"
      }
    ],
    "majors": [
      {
        "slug": "computer-science",
        "name": "Computer Science"
      }
    ]
  }
}
```

Each item remains minimal:

- `slug`
- `name`

This is the best first version because it:

- gives operators a direct answer without reading a full seven-day list
- avoids introducing new interaction states
- keeps admin and public behavior aligned
- fits naturally between today and future schedule

## Alternatives Considered

### Put the next result only inside the seven-day schedule

This keeps the payload smaller, but it makes the operational answer less obvious. Operators still need to interpret which row counts as next.

### Add a button to reveal the next result

This adds interaction and client state without adding much value. The information is lightweight enough to show by default.

### Create a separate next-preview endpoint

This would work, but it adds another route and another fetch path for data that still belongs to the existing featured-content admin payload.

## Current State

Right now the admin featured-content payload includes:

- school configuration
- major configuration
- school rotation rules
- major rotation rules
- today preview
- a seven-day schedule preview

The API already computes rotation results for arbitrary dates. The missing piece is a dedicated next-step summary.

## API Changes

### Existing endpoint: `GET /api/admin/featured-content`

Extend `preview` to include:

```json
{
  "preview": {
    "today": {
      "schools": [],
      "majors": []
    },
    "next": {
      "schools": [],
      "majors": []
    },
    "schedule": []
  }
}
```

### Design Rules

- `preview.next.schools` and `preview.next.majors` must use the same minimal item shape as `preview.today`.
- `preview.next` must be derived from the same API-side rotation logic used by public featured lists.
- No extra item metadata should be included.

## Service Design

### `apps/api/app/services/featured_content.py`

The service layer should compute the next preview by advancing one rotation interval from today.

That means:

- for schools, use `today + school frequency_days` when school auto-rotation is enabled
- for majors, use `today + major frequency_days` when major auto-rotation is enabled
- if auto-rotation is disabled or the rule is not usable, fall back to the current eligible featured set

The important boundary is:

- the service computes next-preview items
- the router only maps those items into response models

## Next Preview Semantics

### Enabled auto-rotation

If auto-rotation is enabled and the rule is valid:

- `preview.next` should be the result of moving forward one configured rotation interval

Examples:

- `frequency_days = 1` means use tomorrow's rotation window
- `frequency_days = 3` means use the rotation window three days from today

### Disabled or incomplete rotation

If auto-rotation is disabled, the ordered slug list is empty, or the rule cannot rotate:

- `preview.next` should fall back to the same featured-set semantics as the current preview

This keeps the admin preview consistent with current public fallback behavior.

## Web Admin UI

### Admin page structure

Keep the existing:

- the today school preview section
- the today major preview section
- the seven-day schedule preview section

Add two new lightweight sections between today and the seven-day schedule:

- `下一轮展示学校`
- `下一轮展示专业`

### Display format

Each next-preview block should show:

- name
- slug

This should match the existing today-preview style so operators can compare current and next at a glance.

### Empty state

If the next preview contains no schools or no majors, show:

- `当前没有下一轮展示学校`
- `当前没有下一轮展示专业`

## Architecture

### `apps/api/app/services/featured_content.py`

Add a small helper for next-preview calculation that reuses the existing arbitrary-date rotation path.

### `apps/api/app/routers/admin.py`

Expand the preview response model so it includes:

- `today`
- `next`
- `schedule`

### `apps/web/lib/admin-featured-content-api.ts`

Map the nested next-preview payload into camelCase admin types.

### `apps/web/app/(admin)/admin/page.tsx`

Load the next-preview data from the existing featured-content fetch.

### `apps/web/components/admin/dashboard-shell.tsx`

Render the new next-preview sections between the current preview and seven-day preview.

## Error Handling

### Admin side

- If the featured-content payload fails entirely, continue using the existing page-level error block.
- The next-preview blocks should not introduce a separate error state in this version.

### Empty results

- An empty next school preview is valid and should render the explicit school empty-state copy.
- An empty next major preview is valid and should render the explicit major empty-state copy.

## Testing Strategy

### API tests

Verify:

- featured-content response includes `preview.next`
- `preview.next.schools` follows the next school rotation step when enabled
- `preview.next.majors` follows the next major rotation step when enabled
- disabled rotation falls back to current eligible featured items

### Web tests

Verify:

- admin page renders `下一轮展示学校`
- admin page renders `下一轮展示专业`
- next-preview blocks show names and slugs
- next-preview empty states render explicitly when needed

### Verification

- focused `apps/api` admin API tests
- focused `apps/web` admin API and page tests
- full `apps/web` Vitest run
- `next build`

## Risks And Mitigations

### Risk: next preview diverges from the seven-day schedule

Mitigation:

- compute `preview.next` from the same service-layer date-based helper used by the schedule

### Risk: unclear meaning when rotation is disabled

Mitigation:

- make fallback behavior explicit in the API contract and keep it aligned with current featured-set semantics

## Completion Criteria

- Admin featured-content payload includes `preview.next`.
- `preview.next` uses the same minimal item shape as the current preview.
- Admin page shows `下一轮展示学校` and `下一轮展示专业`.
- Operators can compare current, next, and seven-day results on one page.
- API tests, admin tests, full web tests, and build pass.
