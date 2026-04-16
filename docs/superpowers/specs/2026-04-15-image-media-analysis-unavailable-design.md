# Image Media Analysis Unavailable Path Design

## Goal

Remove the misleading "pending integration" state for official-account image analysis when the project explicitly selects `openai_compatible` but the provider is unavailable or already failed. The system should distinguish between:

- no media-analysis provider intentionally configured
- a declared media-analysis provider that is misconfigured or failing

## Scope

This subtask only changes the image media-analysis unavailable path:

- keep `provider="" | pending | noop | none` on the existing pending path
- change `provider="openai_compatible"` with incomplete config into an explicit failed result
- when image analysis returns `failed`, reply with a clear image-analysis-unavailable guidance text instead of the generic pending-integration reply
- keep successful image routing unchanged

Out of scope:

- changing the successful image-analysis flow
- changing the unsupported `video` / `shortvideo` behavior again
- adding new database columns or admin endpoints

## Current State

- `provider=""` correctly represents "no media-analysis integration enabled yet" and returns `pending`.
- `provider="openai_compatible"` with missing `BASE_URL / API_KEY / MODEL` also collapses into the same `pending` provider path.
- image provider failures such as HTTP errors already persist `status="failed"` and `context.failure_reason`, but the user still receives the generic pending-integration reply.

## Options

### Option 1: Leave all non-success image paths on pending

- Pros: no behavior change
- Cons: operators cannot distinguish "not configured" from "broken", and user copy is inaccurate for real failures

### Option 2: Recommended - split intentional pending from explicit unavailable/failure

- Pros: small change, operationally clear, preserves the current success path
- Cons: adds one more user-facing fallback message

### Option 3: Force every unavailable path back to the generic picture fallback

- Pros: fewer message variants
- Cons: loses the distinction between disabled capability and temporary provider failure

## Recommendation

Choose Option 2.

This keeps the intentionally disabled path stable, while making declared-but-broken media analysis explicit for both admins and users.

## Design

### Provider construction

- Keep `PendingMediaAnalysisProvider` for `provider="" | pending | noop | none`.
- Add an unavailable provider result for `provider="openai_compatible"` when any required config is blank:
  - `status = "failed"`
  - `provider = "openai_compatible"`
  - `failure_reason = "当前 openai_compatible 媒体分析配置不完整，请检查 BASE_URL / API_KEY / MODEL"`

### Image router behavior

- In `_handle_wechat_official_account_image_message()`:
  - `success + routed_reply` stays unchanged
  - `success + rendered_reply/summary` stays unchanged
  - `failed` returns a new image-analysis-unavailable guidance reply
  - `pending` still returns the existing pending-integration reply

### User-facing reply

- Add a new constant for image provider failure/unavailability:
  - "已收到你上传的图片，但当前图片解析暂时不可用。请继续补充文字描述、分数、省份或专业方向，我先继续帮你分析。"
- This is used only when image analysis explicitly fails.

### Admin outcome

- Existing failure events and `context.failure_reason` persistence continue to work unchanged.
- `/admin` failure filters become more meaningful because declared-but-misconfigured image providers will now surface as failed events instead of pending records.

## Testing

- `apps/api/tests/test_chat_services.py`
  - verify `provider="openai_compatible"` with incomplete config returns a failed result with the config-missing reason
- `apps/api/tests/test_chat_api.py`
  - keep the current pending-image test for the blank provider path
  - change the failed-image test to expect the new unavailable reply instead of the pending-integration reply

## Success Criteria

- blank/intentional pending provider path still behaves as pending
- declared-but-incomplete `openai_compatible` image analysis is explicit `failed`
- failed image-analysis results no longer send the misleading pending-integration reply
