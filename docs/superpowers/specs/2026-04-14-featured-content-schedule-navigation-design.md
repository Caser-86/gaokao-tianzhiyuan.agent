# Featured Content Schedule Navigation Design

## Goal

Turn the existing seven-day featured-content schedule into a lightweight navigation surface for the admin selected-date preview.

## Recommendation

Make each schedule day title link to `/admin?preview_date=<date>` unless that day is already the highlighted date.

This keeps the page fully server-rendered, reuses the existing selected-date preview flow, and removes the need for operators to manually type dates.

## Options

### 1. Add a separate "查看该日" link

Simple, but visually redundant because the date already communicates the same thing.

### 2. Make the date title itself the link

Recommended. Most natural interaction and no extra visual clutter.

### 3. Add client-side partial refresh

Higher interaction cost and unnecessary state for a small admin affordance.

## Design

### Schedule item behavior

In `apps/web/components/admin/dashboard-shell.tsx`:

- render non-highlighted schedule dates as links to `/admin?preview_date=${day.date}`
- keep the highlighted date as plain text
- continue to render the `当前查看` marker for the highlighted date

### Data flow

No API changes.

`apps/web/app/(admin)/admin/page.tsx` keeps passing the existing `highlightedScheduleDate` and does not need new schedule data.

### Error handling

- empty schedule stays unchanged
- invalid `preview_date` still produces no highlighted day
- when no day is highlighted, all schedule dates remain navigable

### Testing

Update admin Web tests to cover:

- non-highlighted days render links with the correct `preview_date`
- highlighted day keeps the `当前查看` marker
- highlighted day is not rendered as a link
