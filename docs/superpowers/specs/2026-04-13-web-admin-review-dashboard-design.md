# Web Admin Review Dashboard Design

## Goal

Extend the existing Next.js admin page so content operators can view pending review items and perform approve or reject actions against the admin review API.

## Current Context

- The API now exposes:
  - `GET /api/admin/review-queue`
  - `POST /api/admin/review-queue/{queue_id}/approve`
  - `POST /api/admin/review-queue/{queue_id}/reject`
- The API requires `x-admin-token` authentication.
- The web app already has a minimal admin shell at `apps/web/app/(admin)/admin/page.tsx`.
- The admin shell component already renders a title and a few summary cards in `apps/web/components/admin/dashboard-shell.tsx`.
- The web app also contains newer public pages and layout files that are not part of this admin workflow and should not be disrupted.

## Scope

This design covers:

1. Fetching pending review queue items on the admin page
2. Rendering those items in the admin dashboard
3. Supporting approve and reject actions from the dashboard
4. Refreshing the page after successful review actions

This design does not cover:

- Client-side live updates
- Filtering, pagination, or search
- Batch review actions
- Rich notifications or toast systems
- Publishing approved content
- Public site integration

## Recommended Approach

Use a server-rendered admin page with a small server-only API client module and form-based review actions. The admin page should fetch the queue on the server, render the current items, and submit approve or reject operations through server actions. After each successful action, the page should revalidate and show the latest queue state.

This approach is the smallest complete workflow:

- no browser-exposed admin token
- no client-side state management
- no extra API proxy layer unless required later
- minimal moving parts while still validating the full review loop

## Alternatives Considered

### Option A: Read-only dashboard

Show pending items in `/admin` but leave review actions for later.

Pros:

- Smallest frontend change
- Lowest interaction complexity

Cons:

- Leaves the workflow half-finished
- Does not validate whether the API action shapes are ergonomic for the UI

### Option B: Server-rendered dashboard with form actions (recommended)

Render the queue on the server and use simple forms for approve and reject actions.

Pros:

- Keeps the admin token server-side
- Avoids client-side state overhead
- Matches the current minimal admin shell
- Produces an end-to-end usable review workflow quickly

Cons:

- UX is basic compared with richer client interactions

### Option C: Client-rendered admin dashboard

Fetch queue items from the browser and manage updates in client state.

Pros:

- More interactive UX
- Easier later extension to optimistic updates

Cons:

- Requires careful handling of admin credentials
- Adds complexity before the workflow has stabilized
- Risks overbuilding this early admin surface

## Architecture

### Page entry

`apps/web/app/(admin)/admin/page.tsx` should remain the route entry for the admin dashboard.

Responsibilities:

- fetch the pending review queue on the server
- define review form actions
- pass fetched items and any error state into the dashboard component

### Dashboard component

`apps/web/components/admin/dashboard-shell.tsx` should expand from a static shell into a presentational admin dashboard component.

Responsibilities:

- render the title and existing summary cards
- render the review queue list
- render empty and error states
- render approve and reject forms for each queue item

This component should stay mostly presentational. Data access and path revalidation should remain in the page entry or adjacent server utilities.

### API client utility

Create a small server-only module such as `apps/web/lib/admin-review-api.ts`.

Responsibilities:

- call `GET /api/admin/review-queue`
- call approve and reject endpoints
- attach `x-admin-token`
- centralize API base URL and error handling

This keeps fetch details out of the page and component code.

## Data Flow

1. The admin page calls `listReviewQueue()` on the server.
2. The API client sends the request to the admin API with the configured admin token.
3. The page receives either queue items or an error result.
4. `DashboardShell` renders:
   - a populated list
   - an empty state when there are no pending items
   - or an error block when loading fails
5. An operator submits an approve or reject form.
6. The server action calls the corresponding API client function.
7. On success, the page revalidates `/admin` and reloads the fresh queue.
8. On failure, the page returns a simple error message for display.

## Admin Authentication Handling

The admin token must remain server-side only.

The web app should read it from environment configuration and never send it to the browser except as an outbound request header from the server to the API. The dashboard page and actions should run on the server so no secret is exposed to client JavaScript.

## UI Behavior

## Summary section

Keep the existing heading and high-level cards:

- `待审核内容`
- `最近发布`
- `抓取状态`

The cards can remain static placeholders for now if they are not yet backed by data. The main new value in this iteration is the review queue list below them.

## Review queue section

Each pending item should show:

- `entity_type`
- `entity_id`
- `candidate_version`
- `diff_summary`
- `priority`
- `created_at`

The presentation can stay simple, for example a stacked card or bordered row list.

## Empty state

When there are no pending items, render a message such as:

- `当前没有待审核内容`

## Error state

When queue loading fails, render a visible error block with a short message such as:

- `审核队列加载失败，请稍后重试`

## Review actions

Each pending item should render:

- a `通过` action
- a `驳回` action

Reject should allow an optional note field. Keep this lightweight:

- either a small inline text input
- or a simple textarea if that is easier to implement cleanly

No modal is needed in this iteration.

## Testing Strategy

### Component tests

Update or extend web tests so they verify:

- the dashboard heading still renders
- queue items render when provided
- the empty state renders when there are no items
- review action controls are visible for pending items

These tests should not depend on real network requests.

### API client tests

If the API client utility contains non-trivial request or response handling, add focused tests for:

- request path construction
- header usage
- success parsing
- failure propagation

### Interaction scope

Do not overinvest in complex server action integration tests yet. The API behavior is already covered in the API test suite, so the web layer should focus on rendering and basic action wiring.

## File Impact

Expected implementation work will likely touch:

- `apps/web/app/(admin)/admin/page.tsx`
- `apps/web/components/admin/dashboard-shell.tsx`
- `apps/web/tests/admin-dashboard.test.tsx`
- `apps/web/lib/admin-review-api.ts`

Potentially, if environment wiring is needed:

- `apps/web/package.json`
- `apps/web/tsconfig.json`

## Success Criteria

The work is complete when:

- `/admin` loads pending review items from the API on the server
- the dashboard renders queue rows and a clear empty state
- operators can approve or reject pending items from the dashboard
- the page refreshes to reflect the latest queue after successful actions
- the admin token remains server-side
- web tests cover the rendered dashboard states
