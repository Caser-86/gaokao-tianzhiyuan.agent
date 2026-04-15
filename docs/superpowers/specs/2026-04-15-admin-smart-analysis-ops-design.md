# Admin Smart Analysis Operations Design

## Goal

Add an operator-facing management layer for smart analysis so the product team can:

1. switch smart analysis fully off, gated, or fully on at runtime
2. grant or revoke the `smart_analysis` entitlement for a specific `user_id`
3. make those decisions persist in SQLite instead of relying on request metadata or `.env`

This slice should turn the current developer-oriented access control into an operational workflow that can be used from the existing admin backend and web admin page.

## Current Context

- The backend already has smart-analysis policy logic in `apps/api/app/services/chat.py`.
- The current policy source is:
  - `settings.smart_analysis_mode`
  - `metadata.entitlements`
- The chat skill already distinguishes policy fallback from provider fallback through `debug.notes`.
- The backend already uses SQLite through SQLModel in `apps/api/app/db.py`, and tables are auto-created at startup.
- The admin backend already exposes authenticated operator APIs in `apps/api/app/routers/admin.py`.
- The admin web page already uses a server-rendered page plus server actions in:
  - `apps/web/app/(admin)/admin/page.tsx`
  - `apps/web/app/(admin)/admin/actions.ts`
  - `apps/web/components/admin/dashboard-shell.tsx`

## Problem

The current smart-analysis access control is technically correct but operationally incomplete:

- global mode is stored in configuration, not runtime data
- user entitlements are only carried in request metadata
- operators cannot inspect or change smart-analysis access from the admin page
- testing the real monetization path from the公众号 / chat entry point still requires manual request shaping

This means the product cannot yet run smart analysis as a real switchable entitlement.

## Scope

This design covers:

1. persistent runtime storage for the global smart-analysis mode
2. persistent per-user storage for the `smart_analysis` entitlement
3. admin API endpoints for reading and updating those values
4. admin page controls for operators to manage them
5. chat-time policy evaluation that reads from SQLite first and still supports request metadata as a temporary override path

This design does not cover:

- payment or purchase flows
- package purchase history
- batch entitlement import
- multiple entitlement tiers
- a public self-service purchase page
- WeChat identity binding beyond the existing `user_id` / `openid`

## Recommended Approach

Use a SQLite-backed operations layer with two focused persistence models.

### Model 1: Runtime setting

Store the global mode in a generic runtime-setting table keyed by name.

Recommended first key:

- `smart_analysis_mode`

Allowed values:

- `off`
- `gated`
- `on`

Reasoning:

- avoids editing `.env` after startup
- allows admin changes without redeploy or restart
- leaves room for future runtime-controlled features

### Model 2: User entitlement

Store per-user entitlement records in a dedicated table keyed by:

- `user_id`
- `entitlement`

Recommended first entitlement:

- `smart_analysis`

Each row should carry:

- `user_id`
- `entitlement`
- `is_enabled`
- `updated_at`

Reasoning:

- simple enough for the current slice
- maps directly to how chat requests identify users today
- can later become the source of truth behind packages or payments

## Alternatives Considered

### Option A: Keep global mode in `.env`, store only user entitlements in SQLite

Pros:

- smallest backend change
- reuses existing config validation

Cons:

- operators still cannot truly manage the global switch from admin
- changing global mode would still depend on deploy or restart
- inconsistent operator experience

### Option B: Store both global mode and user entitlements in SQLite (recommended)

Pros:

- fully operator-controlled
- persistent across restarts
- clean runtime behavior
- aligns with the existing admin/database architecture

Cons:

- requires a new service layer and admin endpoints

### Option C: Build package purchases now

Pros:

- closer to end-state monetization

Cons:

- too large for this slice
- mixes payments, accounts, and entitlement operations

## Architecture

### New persistence layer

Add new SQLModel tables under `apps/api/app/models/`:

- `RuntimeSetting`
- `UserEntitlement`

These tables should be auto-created by the existing `create_all_models()` startup path.

### New service layer

Add a focused service module, for example:

- `apps/api/app/services/access_control.py`

Responsibilities:

- read the effective global smart-analysis mode
- update the global mode
- look up a user's `smart_analysis` entitlement
- grant or revoke the entitlement
- expose a single helper for chat-time decision making

This keeps database concerns out of `chat.py`.

### Updated chat decision flow

`ConversationService` should stop treating `settings.smart_analysis_mode` as the only source of truth.

New precedence:

1. read persisted runtime mode from SQLite
2. read persisted `user_id` entitlement from SQLite
3. merge request metadata entitlements as a compatibility layer
4. return the same policy reasons already introduced:
   - `smart_analysis_disabled_globally`
   - `smart_analysis_entitlement_required`

Recommended compatibility rule:

- database-backed entitlement and metadata entitlement should both count as allowed during this transition

Reasoning:

- existing callers using `metadata.entitlements` keep working
- admin-managed users become the preferred real path

### Admin API integration

Extend `apps/api/app/routers/admin.py` with a dedicated smart-analysis section rather than overloading platform routes.

Reasoning:

- this is an operator workflow, not a public platform capability
- existing admin authentication already lives here
- keeps all admin write actions behind the same token-gated surface

## Data Model

### RuntimeSetting

Recommended shape:

```python
class RuntimeSetting(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str = Field(nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)
```

Rules:

- only one row per key
- `smart_analysis_mode` value must be validated to `off`, `gated`, or `on`

### UserEntitlement

Recommended shape:

```python
class UserEntitlement(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(nullable=False, index=True)
    entitlement: str = Field(nullable=False, index=True)
    is_enabled: bool = Field(default=True, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)
```

Recommended uniqueness rule:

- unique on `(user_id, entitlement)`

Reasoning:

- grants can be updated in place instead of duplicated

## API Design

Add admin endpoints such as:

- `GET /api/admin/smart-analysis/settings`
- `PUT /api/admin/smart-analysis/settings`
- `GET /api/admin/smart-analysis/users/{user_id}`
- `PUT /api/admin/smart-analysis/users/{user_id}`

### Settings response

```json
{
  "mode": "gated"
}
```

### User entitlement response

```json
{
  "user_id": "wx-openid-123",
  "entitlements": [
    {
      "name": "smart_analysis",
      "enabled": true
    }
  ]
}
```

### Update payloads

Global mode update:

```json
{
  "mode": "off"
}
```

User entitlement update:

```json
{
  "smart_analysis_enabled": true
}
```

### Error handling

- invalid mode returns `422`
- missing or blank `user_id` returns `422`
- unknown user on read returns a normal empty entitlement response, not `404`

Reasoning:

- the operator may be checking a user before granting access

## Admin UI

Add one new admin section near other operational controls.

### Block 1: Global smart-analysis mode

Show:

- current mode
- a compact selector or radio group for `off / gated / on`
- a save action

This is the top-level operational switch and should appear before user-level controls.

### Block 2: User entitlement management

Show:

- one `user_id` input
- a load button
- current entitlement status
- grant button
- revoke button

This should be intentionally minimal and operator-friendly:

- no table of all users in this slice
- no pagination
- no bulk operations

Reasoning:

- most immediate use case is "a user paid / a user should be enabled now"

## Chat-Time Behavior

The externally visible chat contract should stay stable.

Behavior:

- `off`: always return rule-based fallback with `smart_analysis_disabled_globally`
- `gated`:
  - if user has DB entitlement, allow provider-backed smart analysis
  - else if request metadata contains `smart_analysis`, allow provider-backed smart analysis
  - otherwise return rule-based fallback with `smart_analysis_entitlement_required`
- `on`: allow provider-backed smart analysis for everyone

This preserves the current debug contract and avoids breaking frontend or公众号 callers.

## Testing Strategy

### Backend

Add tests for:

- runtime setting defaults and updates
- user entitlement create/update/read behavior
- chat service resolution using DB-backed entitlement
- admin API read/write endpoints

Focus on:

- `off` overrides user entitlement
- `gated` + DB grant allows smart analysis
- `gated` + no DB grant + no metadata entitlement blocks smart analysis
- `gated` + metadata entitlement still works during transition
- `on` ignores entitlement absence

### Frontend

Add admin page tests for:

- current mode renders
- mode save form is present
- user entitlement search form is present
- loaded user entitlement state renders grant/revoke controls

## Rollout Notes

Recommended initial rollout:

1. default DB-backed global mode to the existing config value when no row exists
2. keep `.env` validation in place as a bootstrap default
3. once the admin page writes a DB value, runtime behavior should use the DB row

This gives safe startup behavior without breaking current local environments.

## Success Criteria

This slice is successful when:

1. an operator can switch global smart-analysis mode from the admin page
2. an operator can grant or revoke `smart_analysis` for a specific `user_id`
3. the grant persists after backend restart
4. gated chat requests use DB-backed entitlement without requiring request metadata
5. existing metadata-based callers still work during transition
