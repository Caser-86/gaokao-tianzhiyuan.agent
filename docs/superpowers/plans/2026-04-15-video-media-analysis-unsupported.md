# Video Media Analysis Unsupported Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert official-account `video` / `shortvideo` media-analysis attempts from a misleading pending state into an explicit unsupported failure path.

**Architecture:** Keep the current media-analysis architecture and avoid real video integration. The provider will emit an explicit failed result for unsupported media types, and the chat router will keep returning the normal video guidance reply while persisting the failure for admin triage.

**Tech Stack:** FastAPI, SQLModel, Python, pytest

---

### Task 1: Lock the unsupported-path behavior with failing tests

**Files:**
- Modify: `apps/api/tests/test_chat_api.py`

- [ ] **Step 1: Write the failing test**

```python
assert response.status_code == 200
assert (
    f"<Content><![CDATA[{chat_router_module.WECHAT_OFFICIAL_ACCOUNT_VIDEO_FALLBACK_REPLY}]]></Content>"
    in response.text
)

with Session(get_engine()) as session:
    events = session.exec(select(MediaAnalysisEvent)).all()

assert len(events) == 1
saved = events[0]
assert saved.media_type == "video"
assert saved.status == "failed"
assert saved.context["failure_reason"] == (
    "当前 openai_compatible 媒体分析仅支持 image，暂不支持 video/shortvideo"
)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_chat_api.py -k "video_messages_return_media_pending_reply_for_entitled_gated_user" -q`
Expected: FAIL because the router still returns the pending reply and the stored event is not a failed unsupported record.

- [ ] **Step 3: Add a shortvideo assertion if needed**

```python
assert saved.media_type in {"video", "shortvideo"}
```

- [ ] **Step 4: Run test again to confirm the same behavior gap**

Run: `python -m pytest apps/api/tests/test_chat_api.py -k "video_messages_return_media_pending_reply_for_entitled_gated_user" -q`
Expected: still FAIL for the intended unsupported-path behavior.

- [ ] **Step 5: Commit**

```bash
git add apps/api/tests/test_chat_api.py
git commit -m "test: cover unsupported video media analysis path"
```

### Task 2: Implement explicit unsupported failure results

**Files:**
- Modify: `apps/api/app/services/media_analysis.py`
- Modify: `apps/api/app/routers/chat.py`

- [ ] **Step 1: Return failed results for unsupported media types**

```python
if request.media_type != "image":
    return MediaAnalysisResult(
        status="failed",
        provider="openai_compatible",
        failure_reason=(
            "当前 openai_compatible 媒体分析仅支持 image，暂不支持 video/shortvideo"
        ),
    )
```

- [ ] **Step 2: Keep the router on the normal video fallback reply when analysis fails**

```python
if result.status == "success" and result.rendered_reply:
    return result.rendered_reply
if result.status == "success" and result.summary:
    return result.summary
return WECHAT_OFFICIAL_ACCOUNT_VIDEO_FALLBACK_REPLY
```

- [ ] **Step 3: Run the focused test to verify it passes**

Run: `python -m pytest apps/api/tests/test_chat_api.py -k "video_messages_return_media_pending_reply_for_entitled_gated_user" -q`
Expected: PASS

- [ ] **Step 4: Run the surrounding media-analysis tests**

Run: `python -m pytest apps/api/tests/test_chat_api.py -k "image_message_can_use_media_analysis_provider_reply_when_enabled or image_message_records_media_analysis_event or image_message_records_failed_media_reason_event or video_messages_return_media_pending_reply_for_entitled_gated_user" -q`
Expected: PASS, confirming image behavior remains intact.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/services/media_analysis.py apps/api/app/routers/chat.py
git commit -m "feat: mark unsupported video media analysis as failed"
```

### Task 3: Update handover docs and run full verification

**Files:**
- Modify: `docs/operations/local-handover-runbook.md`

- [ ] **Step 1: Update the handover note**

```md
- Official-account `video` / `shortvideo` analysis attempts under `openai_compatible` now persist as explicit failed records with a readable unsupported-media reason, while user replies stay on the normal video guidance text.
```

- [ ] **Step 2: Run focused API verification**

Run: `python -m pytest apps/api/tests/test_chat_api.py -k "video_messages_return_media_pending_reply_for_entitled_gated_user or image_message_records_failed_media_reason_event" -q`
Expected: PASS

- [ ] **Step 3: Run full project verification**

Run: `powershell -ExecutionPolicy Bypass -File scripts/verify-project.ps1`
Expected: PASS with only the existing known non-blocking warnings.

- [ ] **Step 4: Commit**

```bash
git add docs/operations/local-handover-runbook.md
git commit -m "docs: note unsupported video media analysis behavior"
```
