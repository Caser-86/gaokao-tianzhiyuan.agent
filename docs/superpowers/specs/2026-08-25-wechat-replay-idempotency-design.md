# WeChat Replay and Idempotency Design

> Status: Implemented and verified
> Date: 2026-08-25

## Problem

The official-account callback verifies the WeChat signature, but it currently accepts old timestamps and processes a retried `MsgId`/nonce again. A retry can therefore repeat chat routing, media analysis, or event side effects.

## Scope

- Apply a configurable timestamp freshness window to official-account GET verification and POST callbacks, for both plaintext and AES modes.
- Reject bodies larger than a small configured limit before XML parsing/decryption.
- Persist a lightweight receipt table and atomically claim `MsgId` and request nonce keys before any event/chat/media handling.
- Return `success` for a verified duplicate so WeChat stops retrying without re-running business logic.
- Keep the current plaintext/AES signature and response contracts for first-time messages.

Out of scope:

- Rate limiting, WAF, or distributed queue processing.
- External URL/media SSRF controls (Phase 4.5).
- Changing WeChat AES cryptography or official-account identity verification.

## Dedupe contract

- A non-empty `MsgId` creates `msgid:<MsgId>`; a non-empty request nonce creates `nonce:<nonce>`.
- A callback is duplicate if either key has already been claimed within the retention window.
- Both keys are inserted in one transaction for a first-time callback, so a retry with the same `MsgId` or nonce is rejected even if the other value changes.
- Receipts are retained for at least the timestamp freshness window and old receipts are pruned during claims.

## Acceptance criteria

- Old timestamps are rejected before business handling.
- Oversized request bodies are rejected before XML parsing/decryption.
- The same `MsgId` or nonce does not invoke business handling twice.
- Existing plaintext/AES first-delivery tests remain green.
- No new runtime dependency or real secret is added.
