# Admin Review API Design

## Goal

Extend the existing admin API so the review queue becomes usable for content operations. The API should return real pending review items from the database first, then support explicit approve and reject actions with minimal audit metadata.

## Current Context

- The API app already exists in `apps/api/app/main.py`.
- Admin routes already exist in `apps/api/app/routers/admin.py`.
- Admin authentication is currently enforced via `x-admin-token`.
- Review candidates and queue payload mapping already exist in `apps/api/app/services/ingestion.py`.
- The persistence model already includes `ReviewQueue` in `apps/api/app/models/ingestion.py`.
- The current `GET /api/admin/review-queue` endpoint returns a hard-coded empty list.
- Publishing logic already exists, but it should remain separate from review actions in this iteration.

## Scope

This design covers two capabilities, in order:

1. Return real review queue rows through the admin API.
2. Support approve and reject actions on review queue rows.

This design does not cover:

- Publishing approved content
- Generating new content versions from review decisions
- Public-facing API or web integration
- A separate audit log table

## Recommended Approach

Use the existing `ReviewQueue` table as the single source of truth for review work items. Keep the API small and explicit:

- `GET /api/admin/review-queue` reads real pending items from the database
- `POST /api/admin/review-queue/{queue_id}/approve` marks a pending item as approved
- `POST /api/admin/review-queue/{queue_id}/reject` marks a pending item as rejected

Store minimal audit metadata directly on `ReviewQueue`:

- `reviewed_by`
- `reviewed_at`
- `review_note`

This keeps review and publishing decoupled. The API becomes immediately useful without forcing early business coupling that the current codebase has not defined yet.

## Alternatives Considered

### Option A: Status-only actions

Only update `review_status` and skip audit metadata.

Pros:

- Smallest implementation
- Fastest path to basic write actions

Cons:

- Loses reviewer attribution
- Makes later admin tooling harder
- Likely requires a breaking API update soon after

### Option B: Minimal audit on `ReviewQueue` (recommended)

Update status and save lightweight reviewer metadata on the queue row.

Pros:

- Preserves operational context
- Matches the current simple data model style
- Avoids introducing a new table too early

Cons:

- Review history is limited to the latest decision

### Option C: Full business coupling

Approve or reject actions also mutate downstream content version records.

Pros:

- Closer to a final production workflow

Cons:

- Couples review and publishing too early
- Requires business rules the repo does not define yet
- Raises implementation and testing complexity unnecessarily

## Data Model

`ReviewQueue` should remain the review work item model.

Existing fields to keep:

- `id`
- `entity_type`
- `entity_id`
- `candidate_version`
- `diff_summary`
- `priority`
- `review_status`
- `created_at`

New fields to add:

- `reviewed_by: Optional[str]`
- `reviewed_at: Optional[datetime]`
- `review_note: Optional[str]`

## State Model

Allowed queue states in this iteration:

- `pending_review`
- `approved`
- `rejected`

Rules:

- New or unread work items remain `pending_review`
- Only `pending_review` items can transition to `approved`
- Only `pending_review` items can transition to `rejected`
- A non-pending item cannot be reviewed again through these endpoints

## API Design

### GET `/api/admin/review-queue`

Purpose:

- Return real review queue rows for admin use

Authentication:

- Requires valid `x-admin-token`

Behavior:

- Query `ReviewQueue` rows from the database
- By default return only rows where `review_status == "pending_review"`
- Order results by `created_at` ascending so processing order is deterministic

Response shape:

```json
{
  "items": [
    {
      "id": 1,
      "entity_type": "school",
      "entity_id": 42,
      "candidate_version": 3,
      "diff_summary": ["summary", "strengths"],
      "priority": "normal",
      "review_status": "pending_review",
      "created_at": "2026-04-13T08:00:00Z"
    }
  ]
}
```

### POST `/api/admin/review-queue/{queue_id}/approve`

Purpose:

- Approve a pending queue item

Authentication:

- Requires valid `x-admin-token`

Request body:

```json
{
  "reviewed_by": "editor@example.com"
}
```

Behavior:

- Look up the queue row by `queue_id`
- Return `404` if missing
- Return `409` if `review_status` is not `pending_review`
- Set:
  - `review_status = "approved"`
  - `reviewed_by = <request.reviewed_by>`
  - `reviewed_at = now()`
- Return the updated row

### POST `/api/admin/review-queue/{queue_id}/reject`

Purpose:

- Reject a pending queue item

Authentication:

- Requires valid `x-admin-token`

Request body:

```json
{
  "reviewed_by": "editor@example.com",
  "review_note": "source data is stale"
}
```

Behavior:

- Look up the queue row by `queue_id`
- Return `404` if missing
- Return `409` if `review_status` is not `pending_review`
- Set:
  - `review_status = "rejected"`
  - `reviewed_by = <request.reviewed_by>`
  - `reviewed_at = now()`
  - `review_note = <request.review_note or null>`
- Return the updated row

## Error Handling

The API should keep the existing authentication error behavior:

- `401` with `{"detail": "admin authentication required"}` for missing or invalid admin token

New review workflow errors:

- `404` when a queue item does not exist
- `409` when attempting to approve or reject an item that is not `pending_review`
- `422` from FastAPI request validation when required request fields are missing

## Implementation Boundaries

Keep implementation simple and local to the existing API package:

- Extend `ReviewQueue` rather than creating new tables
- Add database-backed route behavior in `apps/api/app/routers/admin.py`
- Extract a small helper or service only if it improves clarity for state transitions
- Do not integrate approve or reject with publishing in this iteration

## Testing Strategy

### Admin queue read tests

Add API tests that verify:

- Valid admin token returns real `pending_review` rows
- Returned rows are ordered by `created_at` ascending
- Non-pending rows are excluded by default
- Missing token still returns `401`

### Admin queue action tests

Add API tests that verify:

- Approve updates a pending row to `approved`
- Reject updates a pending row to `rejected`
- Both actions persist `reviewed_by`
- Both actions persist `reviewed_at`
- Reject persists `review_note`
- Unknown `queue_id` returns `404`
- Re-reviewing an already approved or rejected row returns `409`
- Missing token still returns `401`

### Test Style

- Prefer API-level tests in `apps/api/tests/test_admin_api.py`
- Reuse the existing in-memory SQLite pattern already used in other tests
- Only add lower-level unit tests if route logic becomes hard to reason about

## File Impact

Expected implementation work will likely touch:

- `apps/api/app/models/ingestion.py`
- `apps/api/app/routers/admin.py`
- `apps/api/app/db.py` or nearby session wiring if route-level database access needs a small helper
- `apps/api/tests/test_admin_api.py`

## Success Criteria

The work is complete when:

- `GET /api/admin/review-queue` returns real pending items from the database
- Approve and reject endpoints exist and enforce valid state transitions
- Minimal audit metadata is stored on reviewed items
- Admin authentication remains enforced
- Automated tests cover both read and write paths
- Publishing behavior remains unchanged
