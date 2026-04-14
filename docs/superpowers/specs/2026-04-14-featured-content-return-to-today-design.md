# Featured Content Return-To-Today Shortcut Design

**Date:** 2026-04-14

**Goal:** Add a lightweight `回到今天` shortcut to the admin selected-date preview so operators can quickly return from an arbitrary preview date to today's featured-content result.

## Summary

The admin dashboard already supports:

- today's featured preview
- next-rotation preview
- seven-day schedule
- selected-date preview
- previous-day and next-day shortcuts for the selected-date preview

This change adds one more lightweight shortcut, `回到今天`, when the current selected preview date is valid and not equal to today's date.

The feature remains fully server-rendered and query-parameter driven. It does not add client-side date state or change the API.

## Recommended Approach

Render a `回到今天` link in the selected-date preview shortcut row when:

- `preview_date` exists
- it parses as a valid ISO date
- it is not equal to today's ISO date

The link target is:

- `/admin?preview_date=<today-iso-date>`

## Why This Approach

- It matches the existing admin interaction model.
- It is more useful than clearing the selected date completely, because the operator stays in the selected-date preview flow and sees today's result in the same section.
- It avoids introducing client-side navigation logic or additional API work.

## Interaction Rules

### Valid non-today selected date

Show:

- `查看前一天`
- `回到今天`
- `查看后一天`

### Valid selected date that is already today

Show:

- `查看前一天`
- `查看后一天`

Do not show `回到今天`, because it would be redundant.

### Missing selected date

Show no shortcut links.

### Invalid selected date

Show no shortcut links.

Keep the existing local validation message:

- `预览日期格式无效`

## Architecture

This feature is web-only.

- `apps/web/app/(admin)/admin/page.tsx` computes today's ISO date and, when applicable, builds `todayPreviewDateHref`
- `apps/web/components/admin/dashboard-shell.tsx` receives `todayPreviewDateHref` and renders the `回到今天` link when present
- The API remains unchanged

## Testing

Update:

- `apps/web/tests/admin-page.test.tsx`
- `apps/web/tests/admin-dashboard.test.tsx`

Cover:

- valid non-today selected date shows `回到今天`
- the link points to the expected today's ISO date
- selected date equal to today hides `回到今天`
- invalid or missing selected date hides `回到今天`

## Scope Boundaries

This does not include:

- clearing `preview_date`
- a today button outside the selected-date preview block
- API changes
- client-side date navigation
