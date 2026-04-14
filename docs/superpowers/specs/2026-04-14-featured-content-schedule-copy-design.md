# Featured Content Schedule Copy Design

## Goal

Make the seven-day featured-content schedule easier to read by showing item names and slugs instead of slug-only lists.

## Recommendation

Reuse the existing `PreviewList` rendering style for schedule entries so the admin page shows the same `名称 + slug` pattern across:

- 今日展示
- 下一轮展示
- 指定日期预览
- 未来 7 天轮换预览

## Options

### 1. Keep slug-only lists

No work, but still the least operator-friendly presentation.

### 2. Reuse `PreviewList`

Recommended. Smallest change with the clearest UX gain.

### 3. Upgrade schedule into richer cards

Higher visual polish, but unnecessary complexity for an admin utility page.

## Design

### Dashboard shell

In `apps/web/components/admin/dashboard-shell.tsx`:

- replace the custom slug-only `<ul>` schedule rendering
- render `PreviewList items={day.schools}` when schools exist
- render `PreviewList items={day.majors}` when majors exist

### Behavior

- empty states remain unchanged
- highlighted schedule day behavior remains unchanged
- schedule navigation links remain unchanged

### Testing

Update admin Web tests to assert that the seven-day preview includes:

- school/major names
- school/major slugs

and no longer relies on slug-only output.
