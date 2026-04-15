# Smart Analysis Access Control Design

## Goal

Add a two-layer access control mechanism for model-backed smart analysis in the chat gateway so the product can decide, at runtime, whether intelligent analysis is:

1. disabled for everyone
2. enabled only for entitled users
3. enabled for everyone

This slice should keep the existing chat gateway and skill contracts stable while making smart-analysis availability an explicit product decision instead of an incidental provider failure.

## Current Context

- The API already has a unified chat flow through `apps/api/app/routers/chat.py` and `apps/api/app/services/chat.py`.
- `ZhangXueFengSkill` already supports two execution paths:
  - provider-backed model invocation
  - rule-based fallback when the provider path is unavailable
- Runtime provider config already exists in `apps/api/app/config.py`.
- The platform service already exposes product and entitlement concepts in `apps/api/app/services/platform.py`.
- Current platform products expose entitlement bundles such as:
  - `school_basic_access`
  - `major_basic_access`
  - `school_deep_dive_access`
  - `region_compare_access`
- The chat request model already accepts `metadata`, so a lightweight entitlement list can be carried without introducing a full authentication system in this slice.
- Today, the chat flow only distinguishes technical fallback, not business-policy fallback. If smart analysis is intentionally disabled or entitlement-gated, the current system cannot explain that difference cleanly.

## Scope

This design covers:

1. a global smart-analysis mode switch
2. a platform-level entitlement name for smart analysis
3. chat-time eligibility evaluation using request metadata as the first entitlement source
4. distinct fallback reasons for:
   - globally disabled smart analysis
   - entitlement-required smart analysis
   - provider/config/runtime failures

This design does not cover:

- real user accounts or persistent user-entitlement lookup
- billing, payment, or purchase flows
- admin UI for editing the mode switch
- channel-specific pricing rules
- more than one smart-analysis entitlement tier

## Recommended Approach

Use two layers of control:

### Layer 1: Global mode

Add a runtime configuration value:

- `GAOKAO_AGENT_SMART_ANALYSIS_MODE`

Allowed values:

- `off`
- `gated`
- `on`

Semantics:

- `off`: no request is allowed to use provider-backed smart analysis
- `gated`: only requests with the required entitlement may use provider-backed smart analysis
- `on`: all requests may use provider-backed smart analysis

### Layer 2: User entitlement

Introduce a single capability name:

- `smart_analysis`

In this slice, the request may provide entitlements through:

- `metadata.entitlements`

This keeps the implementation lightweight now while aligning the vocabulary with the existing platform layer so a future user-account system can replace the entitlement source without changing the chat decision model.

## Alternatives Considered

### Option A: Global mode only

Pros:

- smallest implementation
- easiest to explain

Cons:

- cannot support paid access
- cannot selectively enable smart analysis for premium users

### Option B: Global mode plus entitlement gating (recommended)

Pros:

- supports all three product states: fully off, premium-only, fully on
- fits the current platform `products / entitlements` structure
- keeps business policy separate from provider failures
- can evolve later into real user-account entitlement lookup

Cons:

- adds a small amount of decision logic in chat services

### Option C: Build full account-aware entitlements now

Pros:

- closer to the eventual monetization architecture

Cons:

- too large for this slice
- would pull in identity, persistence, and billing concerns

## Architecture

### New Decision Boundary

Add a focused policy evaluator inside the chat service layer, for example as:

- a helper in `apps/api/app/services/chat.py`
- or a small companion module such as `apps/api/app/services/chat_access.py`

Responsibility:

- inspect the global mode
- inspect request entitlements
- decide whether provider-backed smart analysis is allowed for this request
- return a machine-readable reason when it is not allowed

### Responsibility Split

`config.py`

- defines the global smart-analysis mode

`platform.py`

- defines the canonical entitlement name through product bundles

`ConversationService`

- computes whether smart analysis is allowed for the current request
- passes the decision into skill execution context
- distinguishes business-policy fallback from technical fallback

`ZhangXueFengSkill`

- does not decide pricing or entitlement policy
- only decides:
  - use provider-backed smart analysis when allowed
  - otherwise use rule-based fallback

This keeps business policy outside the skill implementation.

## Data Flow

### Request Input

The first implementation should reuse the existing request shape:

```json
{
  "channel": "wechat",
  "user_id": "wx-user-1",
  "message": "河南560分想学金融，靠谱吗？",
  "metadata": {
    "entitlements": ["smart_analysis"]
  }
}
```

### Evaluation Flow

1. `ConversationService` receives the request
2. it reads `settings.smart_analysis_mode`
3. it extracts `metadata.entitlements`
4. it computes one of:
   - `allowed`
   - `disabled_globally`
   - `entitlement_required`
5. if allowed, the skill may use the provider path
6. if not allowed, the skill is forced to use rule-based fallback
7. the response preserves the existing chat envelope and includes the specific fallback reason in `debug.notes`

## Configuration

Add to `apps/api/app/config.py`:

- `smart_analysis_mode: str = "off"`

Validation rules:

- allowed values are only `off`, `gated`, and `on`
- invalid values should fail app startup with a clear configuration error

Recommended default:

- `off`

Reason:

- a new monetizable feature should not become globally available by accident

## Platform Entitlements

Extend the platform product catalog so at least one bundle grants:

- `smart_analysis`

Recommended first-pass mapping:

- add `smart_analysis` to `deep-dive-pack`

Why:

- that bundle already represents deeper, more premium analysis behavior
- this aligns smart analysis with the existing “deep” product tier rather than basic access

The `evaluate_entitlements()` endpoint should naturally include `smart_analysis` whenever the qualifying product slug is supplied.

## Chat Request Contract

The public request schema does not need a breaking change.

Continue to use:

- `metadata: dict[str, Any]`

But document that chat callers may send:

- `metadata.entitlements: list[str]`

This keeps the first implementation backward-compatible and easy to test from web, WeChat adapters, or internal tooling.

## Response Behavior

The user-facing response should remain natural and non-technical.

The response should not tell ordinary users:

- “your provider has insufficient balance”
- “your API key failed”
- “the relay is down”

Instead, the response should continue to return structured content plus a normal fallback reply.

### Debug Notes

Use `debug.notes` to distinguish exact causes.

Business-policy notes:

- `smart_analysis_disabled_globally`
- `smart_analysis_entitlement_required`

Technical notes:

- `provider_not_configured`
- `provider_insufficient_balance`
- `provider_request_failed`
- `provider_invalid_response`
- `skill_prompt_missing`

This preserves operational visibility without leaking infrastructure details to end users.

## Failure Model

The system should distinguish two classes of fallback:

### Policy fallback

Smart analysis was intentionally not allowed for this request because of product policy.

Examples:

- global mode is `off`
- global mode is `gated` and the request lacks `smart_analysis`

### Technical fallback

Smart analysis was allowed by policy, but provider-backed execution failed.

Examples:

- provider config missing
- relay request failed
- relay account has insufficient balance
- prompt asset missing
- provider output malformed

This distinction is central to the feature: product strategy and provider health should no longer look the same in the response metadata.

## Testing Strategy

### Config Tests

Verify:

- valid `smart_analysis_mode` values are accepted
- invalid values are rejected

### Platform Tests

Verify:

- premium products include `smart_analysis`
- entitlement evaluation returns `smart_analysis` when the qualifying product is present

### Chat Service Tests

Verify:

- mode `off` forces rule-based fallback even when entitlements are present
- mode `gated` allows provider-backed execution only when `smart_analysis` is present
- mode `gated` falls back with `smart_analysis_entitlement_required` when entitlements are missing
- mode `on` allows provider-backed execution without entitlements
- provider failures still surface technical debug notes distinct from policy notes

### API Tests

Verify:

- chat endpoints preserve the same envelope
- `debug.notes` distinguishes policy fallback from technical fallback
- WeChat adapter can pass through metadata entitlements if provided

## Success Criteria

This subtask is complete when:

1. the app supports `off`, `gated`, and `on` smart-analysis modes
2. `smart_analysis` exists as a platform entitlement
3. the chat layer can gate provider-backed smart analysis by entitlement
4. policy-driven fallback and technical fallback are distinguishable in `debug.notes`
5. the user-facing chat response remains non-technical

