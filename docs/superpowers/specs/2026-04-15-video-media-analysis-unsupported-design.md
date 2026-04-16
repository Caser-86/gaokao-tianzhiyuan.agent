# Video Media Analysis Unsupported Path Design

## Goal

Close the current `video` / `shortvideo` media-analysis gap without introducing a real video-understanding dependency. The system should clearly treat unsupported official-account video analysis as an explicit failure path instead of a misleading `pending` state.

## Scope

This subtask only changes the unsupported-path behavior for official-account `video` and `shortvideo` messages:

- return a clear user-facing fallback reply when media analysis is enabled but video analysis is unsupported
- persist a `failed` media-analysis event instead of `pending`
- persist a readable `context.failure_reason` so `/admin` operators can triage the record immediately
- keep existing image media-analysis behavior unchanged

Out of scope:

- real upstream video recognition
- downloading or transcoding WeChat video media
- auto-routing video extracted fields into the main chat flow
- adding new admin APIs or database columns

## Current State

- The provider layer accepts `image | video | shortvideo`, but the `openai_compatible` provider returns `pending` for non-image media.
- The official-account video handler records the result and returns the generic media-analysis pending reply for entitled users.
- In `/admin`, video records therefore look like "still pending" even though the system does not actually support that media type today.

## Options

### Option 1: Real video provider integration

- Pros: end-state capability
- Cons: much larger scope, relay/model support is uncertain, introduces media-fetching and provider-compatibility risk

### Option 2: Keep the current pending branch

- Pros: zero behavior change
- Cons: operations cannot distinguish "unsupported" from "still processing", and user messaging stays vague

### Option 3: Recommended - explicit unsupported failure path

- Pros: small, testable, operationally clear, keeps current architecture intact
- Cons: does not add true video intelligence yet

## Recommendation

Choose Option 3.

This is the smallest change that makes the system honest and observable. Users still get graceful guidance, while admins stop seeing false-pending records for media types we do not actually analyze.

## Design

### Provider behavior

- Update `OpenAICompatibleMediaAnalysisProvider.analyze()` so `video` and `shortvideo` return:
  - `status = "failed"`
  - `provider = "openai_compatible"`
  - `failure_reason = "当前 openai_compatible 媒体分析仅支持 image，暂不支持 video/shortvideo"`
- Keep the existing `image` path unchanged.
- Keep the generic `PendingMediaAnalysisProvider` unchanged, because that provider intentionally represents a not-yet-configured integration.

### Official-account router behavior

- In `_handle_wechat_official_account_video_message()`:
  - continue recording a media-analysis event when analysis is enabled
  - if the provider returns `success`, keep the current success reply flow
  - if the provider returns `failed`, return the normal video fallback guidance reply instead of the generic pending-integration reply
- This keeps user messaging natural while preserving precise failure details in the stored event context.

### Event persistence

- Reuse existing event fields only.
- Persist the readable failure message into `context.failure_reason`.
- Persist `status = failed` for unsupported video attempts.

### Admin outcome

- `/admin` immediately shows unsupported video attempts as failed records.
- Existing failure filters and failure-reason rendering work without extra admin changes.

## Testing

- `apps/api/tests/test_chat_api.py`
  - update the entitled-video test to expect the standard video fallback reply instead of the generic pending reply
  - verify the stored event has `status = failed`
  - verify `context.failure_reason` explains that only image analysis is currently supported
- keep image tests unchanged to prove the change is scoped

## Success Criteria

- entitled official-account `video` / `shortvideo` messages no longer create misleading `pending` records under the `openai_compatible` provider
- `/admin` can filter these attempts as failed and show a readable failure reason
- image media-analysis behavior remains green
