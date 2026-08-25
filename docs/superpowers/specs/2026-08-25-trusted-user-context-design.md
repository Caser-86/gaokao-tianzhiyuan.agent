# Trusted User Context Design

> Status: Implemented and verified
> Date: 2026-08-25

## Problem

Chat and session endpoints currently accept `user_id` from the request body or query string. The Web page also forwards a URL-provided identifier. A caller who knows another identifier can therefore impersonate that subject when reading sessions or evaluating user-scoped behavior.

The verified official-account callback is a separate path: it verifies the WeChat signature before routing the verified `FromUserName`/openid into the chat service. Generic Web and adapter calls do not have that trust property.

## Scope

This phase adds a small server-issued identity boundary without a new authentication framework:

- Issue an opaque guest identity in a signed HMAC session token using Python standard-library primitives.
- Store the token in an HTTP-only API cookie and accept the same token as a Bearer token for non-browser clients.
- In production-like environments, reject a claimed `user_id`/`openid` without a valid token; reject a body/query identifier that differs from the verified token subject.
- In development/test, retain the current explicit identifier fallback for local compatibility, while Web traffic stops serializing its URL hint as an identity claim.
- Keep verified official-account routing as an internal trusted-subject path.

Out of scope:

- Account registration, password login, JWT libraries, OAuth, or a user table.
- Admin authentication changes.
- Platform entitlement query authorization (Phase 4.3).
- WeChat replay/nonce/idempotency controls (Phase 4.4).

## Token and cookie contract

```text
POST /api/auth/session
    -> Set-Cookie: gaokao_session=<v1 payload.signature>; HttpOnly; SameSite=Lax

Web chat/session requests
    -> credentials: include
    -> server resolves subject from cookie
```

The signed payload contains only an opaque subject and expiry. The server secret is configured by `GAOKAO_AGENT_SESSION_SECRET`; a development placeholder is rejected outside development/test. Tokens are not database sessions, so revocation and multi-device account management remain future work.

## Acceptance criteria

- Production rejects a request that claims `user_id` without a server-issued session.
- Production rejects a valid session token when the request claims a different `user_id`.
- A request without a claimed identity can receive a server-generated guest session; the response subject is not chosen by the caller.
- Web chat and session history requests include credentials and no longer use a URL/body `user_id` as the API identity.
- Existing local development/test flows remain runnable, explicitly documented as compatibility fallback.
- No runtime dependency or real secret is added.
