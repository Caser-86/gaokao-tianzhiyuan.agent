# Trusted Platform Entitlement Subject Design

> Status: Implemented and verified
> Date: 2026-08-25

## Problem

`POST /api/platform/entitlements/evaluate` currently accepts an optional body `user_id` and uses it to read persisted entitlements. A caller can therefore choose another subject when the endpoint is used in a production-like environment. The product-bundle preview itself is public, but persisted user entitlements must be evaluated only for the server-resolved subject.

## Scope

- Reuse the Phase 4.2 Bearer/cookie identity resolver for the platform entitlement evaluation endpoint.
- Keep `product_slugs` caller-controlled because it describes the public bundle preview.
- In production-like environments, reject a body `user_id` without a valid server session and reject a claim that differs from the verified token subject.
- In development/test, retain the explicit body `user_id` fallback for existing local fixtures.
- Remove the Web URL/query identity flow and send credentials with the entitlement request.

Out of scope:

- Admin entitlement management and admin authentication.
- Product purchase, billing, account registration, or token revocation.
- Changing the public product catalog or entitlement response shape.

## Acceptance criteria

- A production-like request cannot read persisted entitlements by naming another `user_id`.
- A valid server session reads only the token subject's persisted entitlements.
- Web does not serialize `user_id`/`openid` into the platform request or quick-chat URL.
- Existing product preview behavior and local test fixtures remain runnable.
- No new runtime dependency or real secret is added.
