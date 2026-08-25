# Trusted Entitlement Boundary Design

> Status: Implemented and verified
> Date: 2026-08-25

## Problem

The chat request accepts arbitrary `metadata`. The current service merges client-provided `entitlements` with database entitlements and lets client-provided `smart_analysis_mode` participate in the policy decision. A caller can therefore claim `smart_analysis` or request `on` even when the server-side policy says `off` or `gated`.

## Scope

This phase makes the smart-analysis decision server-authoritative without introducing a new authentication framework or changing the public chat response shape.

In scope:

- Runtime mode comes only from the persisted `RuntimeSetting` value, with the configured default as fallback.
- User entitlements come only from `UserEntitlement` rows for the server-resolved user identifier.
- Request metadata remains available for non-authoritative channel context, but `smart_analysis_mode` and `entitlements` cannot grant or expand access.
- Add regression tests for client entitlement injection and client mode escalation.

Out of scope:

- Establishing the trusted user identifier itself; the current `user_id`/WeChat `openid` boundary remains a Phase 4.2 concern.
- Replacing the existing entitlement tables or adding JWT/session authentication.
- Changing the public `matched_skill`, `output`, or `debug` response contracts.

## Decision flow

```text
request metadata ──┐
                   ├─ non-authoritative context only
                   └─ ignore policy keys: mode, entitlements

RuntimeSetting + UserEntitlement ──> resolve policy ──> ChatRequestContext
```

The service will overwrite the policy keys in the internal request context with server-derived values before calling a Skill. This keeps existing Skill behavior and channel metadata while making the authorization inputs explicit.

## Acceptance criteria

- With server mode `gated` and no database entitlement, client metadata cannot enable smart analysis.
- With server mode `off`, client metadata cannot escalate the mode to `on` or grant an entitlement.
- With server mode `gated` and a database entitlement, the request remains allowed even if client metadata omits or contradicts entitlement claims.
- Existing API and Web response contracts remain unchanged.
- No runtime dependency or secret is added.
