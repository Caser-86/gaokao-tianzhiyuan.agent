# Media Analysis Retryability Design

## Goal

Make `/admin` distinguish between:

- media-analysis records that can be retried immediately
- records that are intentionally non-retriable under the current backend constraints

This removes the operational mismatch where some failed media-analysis records look retryable in the UI, but the retry endpoint rejects them.

## Scope

This subtask only covers retryability metadata and admin presentation:

- add explicit retryability metadata to admin media-analysis event responses
- keep the retry endpoint behavior unchanged
- show the retry button only for truly retryable records
- show a short block reason for non-retriable records

Out of scope:

- expanding retry support beyond image records with `pic_url`
- changing chat/media-analysis provider behavior
- adding new database columns

## Current State

- The retry endpoint only supports `media_type="image"` records with a non-empty `context.pic_url`.
- The admin UI infers retryability from `context.pic_url` alone.
- Failed `video` or `shortvideo` records can appear beside image records, but they should never be retried under the current backend contract.
- Operators do not get a clear reason in the list for why a failed record cannot be retried.

## Options

### Option 1: Keep frontend-only inference

- Pros: no API shape change
- Cons: duplicated rules, still drifts from backend behavior, hard to explain blocked retries

### Option 2: Recommended - backend declares retryability

- Pros: single source of truth, UI becomes simpler, future retry-expansion stays backward compatible
- Cons: adds two response fields to the admin API contract

### Option 3: Hide retry controls for all failed records

- Pros: zero mismatch
- Cons: loses manual retry for the image path that is already useful today

## Recommendation

Choose Option 2.

The backend already owns the retry rules, so it should also expose whether each record is retryable and why not.

## Design

### Retryability contract

Add two fields to `MediaAnalysisEventResponse`:

- `retryable: bool`
- `retry_block_reason: str | None`

Rules:

- `image` + non-empty `context.pic_url` => `retryable = true`, `retry_block_reason = null`
- all other records => `retryable = false`
- default block reason:
  - `非图片媒体记录暂不支持手动重试`
- image without `pic_url` block reason:
  - `图片记录缺少 pic_url，暂不支持手动重试`

### Backend reuse

- add a shared helper that evaluates retryability from a `MediaAnalysisEvent`
- reuse the same helper in:
  - admin list serialization
  - retry payload construction / validation

This keeps list metadata and retry endpoint validation aligned.

### Admin UI behavior

- render the retry button only when `event.retryable` is `true`
- when `event.retryable` is `false` and `event.retryBlockReason` exists, render:
  - `不可重试：...`

### Web API client

- map the two new response fields to camelCase:
  - `retryable`
  - `retryBlockReason`

## Testing

- `apps/api/tests/test_admin_api.py`
  - list endpoint should mark image-with-pic-url as retryable
  - list endpoint should mark unsupported video as non-retryable with a readable reason
- `apps/web/tests/admin-media-analysis-api.test.ts`
  - client should map `retryable` and `retry_block_reason`
- `apps/web/tests/admin-page.test.tsx`
  - retry button only appears for retryable records
  - non-retryable records show the block reason

## Success Criteria

- admin list responses expose retryability metadata
- retryable image records still show the retry button
- non-retryable failed records no longer expose a misleading retry button
- operators can see why a failed record is blocked from retrying
