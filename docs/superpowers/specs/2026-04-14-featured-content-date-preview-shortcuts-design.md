# Featured Content Date Preview Shortcuts Design

**Date:** 2026-04-14

**Goal:** Make the admin date preview easier to use by adding lightweight previous-day and next-day shortcuts around the existing selected-date preview flow.

## Summary

The admin dashboard already supports a `preview_date` query parameter and renders a selected-date featured-content preview. This design keeps that server-rendered flow intact and adds two shortcut links, `查看前一天` and `查看后一天`, when the current `preview_date` is valid.

The shortcuts do not introduce any client-side state or new API routes. They only compute adjacent ISO dates in the web admin layer and navigate to the existing `/admin?preview_date=...` URL.

## Approach

### Recommended option

Keep the current date input plus `查看该日轮换` submit button, and add:

- `查看前一天`
- `查看后一天`

These links appear only when the current `preview_date` exists and parses as a valid `YYYY-MM-DD` value.

### Why this option

- It keeps the admin page server-rendered and easy to reason about.
- It avoids duplicating rotation logic in the client.
- It supports the two real operator workflows:
  - jump directly to a known date
  - quickly step forward or backward while checking nearby dates

## Interaction Design

### When `preview_date` is valid

The `指定日期预览` block shows:

- date input
- `查看该日轮换` button
- `查看前一天` link
- `查看后一天` link
- selected-date result block

The shortcut links point to:

- `/admin?preview_date=<previous-day>`
- `/admin?preview_date=<next-day>`

### When `preview_date` is missing

The block shows:

- date input
- `查看该日轮换` button
- helper text: `选择一个日期查看当天轮换结果`

It does not show previous-day or next-day shortcuts.

### When `preview_date` is invalid

The block shows:

- date input
- `查看该日轮换` button
- local error: `预览日期格式无效`

It does not show previous-day or next-day shortcuts, because there is no valid anchor date to offset from.

## Architecture

This feature is web-only.

- The API remains unchanged.
- `apps/web/app/(admin)/admin/page.tsx` continues to read `preview_date` from `searchParams`.
- A small date-offset helper computes previous and next ISO dates from the selected preview date.
- `apps/web/components/admin/dashboard-shell.tsx` receives optional previous/next shortcut targets and renders them only when present.

## Data and Types

No API schema changes are required.

The admin page should derive:

- `selectedPreviewDateValue`
- `previousPreviewDateHref?: string`
- `nextPreviewDateHref?: string`

The shell should accept:

- `previousPreviewDateHref?: string`
- `nextPreviewDateHref?: string`

## Error Handling

- Missing `preview_date` is not an error.
- Invalid `preview_date` continues to use the existing local message: `预览日期格式无效`
- Invalid dates do not get shortcut links.
- General featured-content loading failures continue to use the existing page-level error state.

## Testing

### Web tests

Update:

- `apps/web/tests/admin-page.test.tsx`
- `apps/web/tests/admin-dashboard.test.tsx`

Cover:

- valid selected date shows `查看前一天` and `查看后一天`
- shortcut links point to the correct adjacent dates
- no selected date means no shortcut links
- invalid selected date means no shortcut links

## Scope Boundaries

This change does not include:

- a `回到今天` shortcut
- month navigation
- calendar UI
- client-side stateful date browsing
- API changes
