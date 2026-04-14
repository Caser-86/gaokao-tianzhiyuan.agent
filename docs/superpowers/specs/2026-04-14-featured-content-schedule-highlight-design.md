# Featured Content Schedule Highlight Design

## Goal

Make the admin featured-content dashboard easier to scan by highlighting the relevant day inside the existing seven-day schedule preview.

## Recommendation

Use a pure Web-layer highlight:

- highlight the selected `preview_date` when it is valid
- otherwise highlight today's date
- show no highlight when `preview_date` is invalid

This keeps the behavior aligned with the existing server-rendered admin page and avoids unnecessary API changes.

## Approach Options

### 1. Highlight today only

Smallest change, but it does not help when an operator is checking a future campaign date.

### 2. Highlight selected date, otherwise today

Recommended. This makes the selected-date preview and seven-day schedule work together without introducing new navigation or state.

### 3. Turn the seven-day preview into navigation

Richer interaction, but unnecessarily expands scope for a small operator affordance.

## Design

### Server page

Update `apps/web/app/(admin)/admin/page.tsx` to compute a `highlightedScheduleDate` value:

- valid `preview_date` -> use that date
- no `preview_date` -> use today's ISO date
- invalid `preview_date` -> `undefined`

Pass the value into `DashboardShell`.

### Dashboard shell

Update `apps/web/components/admin/dashboard-shell.tsx` to accept `highlightedScheduleDate?: string`.

Inside the existing `未来 7 天轮换预览` section:

- compare each schedule day with `highlightedScheduleDate`
- render a lightweight marker such as `当前查看` on the matching day
- do not change the schedule payload shape or add new controls

### Error handling

- invalid selected-date preview keeps its existing local error message
- invalid `preview_date` does not highlight any day in the schedule
- empty schedule keeps its current empty state

### Testing

Update Web tests to cover:

- selected `preview_date` highlights the matching schedule day
- no selected date highlights today
- invalid `preview_date` renders no highlight
- `DashboardShell` shows the marker only on the matching day
