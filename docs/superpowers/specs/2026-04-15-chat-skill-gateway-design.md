# Chat Skill Gateway Design

## Goal

Add a first-pass chat gateway to the API so future channels such as the WeChat official account can call structured skills through a stable internal interface. The first iteration should support:

1. A unified chat message API
2. A WeChat channel adapter API
3. A pluggable skill registry
4. A first placeholder `zhangxuefeng` skill
5. Structured JSON output only

The first iteration should explicitly avoid stateful conversation memory and should not depend on a real external LLM or orchestration provider.

## Current Context

- The API app already exists in `apps/api/app/main.py`.
- Existing public APIs are read-oriented catalog endpoints in `apps/api/app/routers/public.py`.
- Existing admin APIs follow a FastAPI router plus service-layer pattern in `apps/api/app/routers/admin.py`.
- Configuration is currently centralized in `apps/api/app/config.py`.
- The repo currently contains public content pages, admin content operations, and homepage quick prompts, but no chat router, no skill registry, and no channel-specific conversation adapter.
- The public homepage currently exposes quick prompts as UI affordances, but those prompts do not invoke any internal skill execution path yet.

## Scope

This design covers the first implementation slice only:

1. Add new chat-oriented API routes
2. Define shared request and response models for chat requests
3. Introduce a `SkillRegistry` and `SkillHandler` abstraction
4. Implement a no-memory `ConversationService`
5. Add a placeholder `zhangxuefeng` skill with rule-based matching and structured JSON output
6. Add a WeChat adapter endpoint that normalizes channel-specific payloads into the unified chat flow

This design does not cover:

- Real WeChat signature validation or XML callback handling
- Stateful multi-turn memory
- Persistent conversation storage
- External LLM integration
- Dynamic prompt management
- Admin UI for toggling skills
- Non-WeChat production channel adapters
- Final user-facing text generation

## Recommended Approach

Use a layered chat gateway with explicit boundaries:

- `router` layer receives HTTP requests and validates payloads
- `ConversationService` normalizes requests, resolves a skill, invokes it, and wraps the response
- `SkillRegistry` owns available skill definitions and lookup rules
- `SkillHandler` implementations encapsulate skill-specific matching and output generation
- channel adapter endpoints only translate incoming channel payloads into the unified chat request format

This keeps channel integration separate from skill execution and allows future skills to be added without changing the WeChat-specific code path.

## Alternatives Considered

### Option A: One endpoint per skill

Expose separate public endpoints such as:

- `POST /api/chat/skills/zhangxuefeng/invoke`
- `POST /api/chat/skills/school-lookup/invoke`

Pros:

- Fastest initial implementation
- Simple to reason about per endpoint

Cons:

- Couples callers to internal skill topology
- Makes multi-channel integration repetitive
- Fragments logging, routing, and validation behavior
- Scales poorly as more skills are added

### Option B: Unified chat gateway plus skill registry (recommended)

Expose a stable chat interface and let internal routing select a skill or invoke one directly when requested.

Pros:

- Keeps channels decoupled from skill internals
- Makes new skills additive rather than invasive
- Centralizes validation, logging, fallback behavior, and output shape
- Matches the current service-oriented API architecture better

Cons:

- Slightly more design work up front
- Requires a few new abstractions before the first skill ships

### Option C: Stateful conversation gateway in v1

Start with session history, context memory, and multi-turn orchestration.

Pros:

- More natural chat experience
- Closer to a long-term assistant architecture

Cons:

- Larger implementation surface
- Requires persistence and lifecycle rules that the repo does not define yet
- Raises operational complexity before the basic skill gateway is proven

## Architecture

### New Router Surface

Add a dedicated chat router, for example:

- `apps/api/app/routers/chat.py`

Register it in `apps/api/app/main.py` alongside the existing admin, platform, and public routers.

### Service Boundaries

Add a small chat service package, for example:

- `apps/api/app/services/chat.py` for `ConversationService`
- `apps/api/app/services/skills.py` for the registry and handler protocol

If the module grows quickly, the design should allow splitting it into:

- `services/chat/conversation.py`
- `services/chat/registry.py`
- `services/chat/skills/zhangxuefeng.py`

The first implementation can start with one or two files as long as the public interfaces stay clean.

### Responsibility Split

`Chat router`

- validate request payloads
- call `ConversationService`
- return consistent HTTP responses

`WeChat adapter route`

- accept WeChat-shaped payloads
- normalize them into the common request model
- delegate to `ConversationService`

`ConversationService`

- create request IDs
- validate channel and skill targeting rules
- choose a skill when `skill_id` is absent
- invoke the selected skill
- generate fallback output when no skill matches
- return the standard chat envelope

`SkillRegistry`

- register skills
- list enabled skills
- resolve one skill by ID
- enumerate enabled skills for matching

`SkillHandler`

- expose metadata
- decide whether it matches a request
- generate structured JSON output

## API Design

### POST `/api/chat/messages`

Purpose:

- Unified chat entrypoint for all channels

Request body:

```json
{
  "channel": "wechat",
  "user_id": "wx-openid-123",
  "session_id": null,
  "message": "帮我看看江苏适合冲哪些985",
  "skill_id": null,
  "metadata": {
    "source": "official_account",
    "message_type": "text"
  }
}
```

Behavior:

- require `channel`, `user_id`, and `message`
- accept optional `session_id`, but do not persist or reuse it yet
- if `skill_id` is present, invoke that skill directly
- if `skill_id` is absent, run automatic skill matching
- if no skill exceeds the routing threshold, return a structured fallback response

Response shape:

```json
{
  "request_id": "chat_01",
  "channel": "wechat",
  "user_id": "wx-openid-123",
  "matched_skill": {
    "skill_id": "zhangxuefeng",
    "version": "v1",
    "confidence": 0.92,
    "reason": "matched keyword: 冲 / 985 / 江苏"
  },
  "output": {
    "type": "structured_json",
    "content": {
      "intent": "school_recommendation",
      "summary": "用户在咨询江苏地区 985 冲刺建议",
      "entities": {
        "province": "江苏",
        "school_tags": ["985"],
        "score": null
      },
      "suggestions": [],
      "follow_up_questions": [],
      "actions": []
    }
  },
  "debug": {
    "used_fallback": false,
    "notes": []
  }
}
```

### POST `/api/chat/channels/wechat`

Purpose:

- channel adapter endpoint for the official account integration path

Behavior:

- accept a WeChat-oriented JSON payload for internal integration
- map it into the common request model used by `POST /api/chat/messages`
- delegate to the same `ConversationService`
- return the same standard chat envelope

The first iteration should treat this as a JSON adapter only. Real signature verification, XML parsing, and raw WeChat protocol handling should remain out of scope.

### GET `/api/chat/skills`

Purpose:

- list registered and enabled skills

Response shape:

```json
{
  "items": [
    {
      "skill_id": "zhangxuefeng",
      "name": "张雪峰",
      "enabled": true,
      "supports_channels": ["wechat", "web"],
      "description": "高考志愿、学校专业咨询的首期占位 skill"
    }
  ]
}
```

### POST `/api/chat/skills/{skill_id}/invoke`

Purpose:

- invoke one specific skill directly for debugging, testing, and future admin tooling

Behavior:

- require a valid `skill_id`
- bypass auto-matching
- still wrap the skill output in the standard chat envelope

### GET `/api/chat/health`

Purpose:

- provide a lightweight health endpoint for channel integration checks

Behavior:

- return a static success payload if the router is available

## Request and Response Models

### Common Chat Request

Fields:

- `channel: str`
- `user_id: str`
- `session_id: str | None`
- `message: str`
- `skill_id: str | None`
- `metadata: dict[str, Any]`

Rules:

- `channel` must be one of the supported channel identifiers
- `message` must be non-empty after trimming
- `session_id` is accepted for forward compatibility, but not used for memory in v1
- `metadata` is optional and should default to an empty object

### Common Chat Response

Fields:

- `request_id: str`
- `channel: str`
- `user_id: str`
- `matched_skill`
- `output`
- `debug`

`matched_skill` fields:

- `skill_id: str`
- `version: str`
- `confidence: float`
- `reason: str`

`output` fields:

- `type: "structured_json"`
- `content: dict[str, Any]`

`debug` fields:

- `used_fallback: bool`
- `notes: list[str]`

## Skill Registry Design

### Skill Metadata

Each skill should expose metadata that includes:

- `skill_id`
- `name`
- `version`
- `description`
- `enabled`
- `supports_channels`

### Skill Handler Interface

Each skill should implement the same conceptual contract:

- `describe() -> SkillMetadata`
- `match(request) -> SkillMatchResult`
- `invoke(request) -> SkillOutput`

`match()` should return:

- whether the skill should handle the request
- confidence score
- a short explanation for debugging

`invoke()` should return structured JSON content only. It should not attempt to format the final user message for a specific channel.

### Registry Behavior

The registry should:

- register the built-in `zhangxuefeng` skill during startup or module initialization
- expose a list operation for the skills endpoint
- expose a get-by-ID operation for direct invocation
- expose enabled skills filtered by channel for auto-matching

The first implementation can use an in-memory registry because skills are static in v1.

## Conversation Routing

### Direct Invocation

If `skill_id` is present:

- resolve the skill by ID
- return `404` if the skill does not exist
- return `409` if the skill exists but is disabled or unsupported for the request channel
- invoke the skill directly

### Automatic Matching

If `skill_id` is absent:

- enumerate enabled skills for the request channel
- call `match()` on each skill
- select the highest-confidence skill above a fixed threshold
- if no skill exceeds the threshold, return a fallback response

### Fallback Behavior

Fallback should be a successful structured response, not a server exception.

Suggested fallback output:

```json
{
  "intent": "fallback",
  "summary": "当前没有命中明确技能",
  "entities": {},
  "suggestions": [],
  "follow_up_questions": [
    "你想查学校、专业，还是志愿填报建议？"
  ],
  "actions": []
}
```

This keeps channels responsive even when routing is uncertain.

## `zhangxuefeng` Skill v1

### Purpose

Provide the first skill placeholder for gaokao-oriented recommendation and comparison queries. The goal is not to reproduce a full expert assistant yet. The goal is to prove the skill gateway contract with a realistic domain-specific skill name and output format.

### Matching Strategy

Use simple rule-based matching in the first iteration, such as:

- keywords related to schools, majors, and volunteer strategy
- mentions of `985`, `211`, `双一流`, `冲`, `稳`, `保`
- region and score-related cues when present

The matching logic should stay explicit and testable.

### Supported Intents

The first version should support these structured intents:

- `school_recommendation`
- `major_recommendation`
- `volunteer_strategy`
- `comparison`
- `fallback`

### Output Schema

The skill should emit `output.content` with these common fields:

- `intent`
- `summary`
- `entities`
- `suggestions`
- `follow_up_questions`
- `actions`

Suggested `suggestions` item shape:

```json
{
  "type": "school",
  "title": "东南大学",
  "slug": "southeast-university",
  "reason": "属于 985，工科实力强，适合作为冲刺项",
  "confidence": 0.81
}
```

Suggested `actions` item shape:

```json
{
  "type": "open_school",
  "label": "查看学校详情",
  "target": "/schools/southeast-university"
}
```

The first version can return empty `suggestions` and `actions` for some intents as long as the envelope stays valid and the skill result is structurally consistent.

## Channel Adapter Design

### WeChat Adapter Payload

The first iteration should accept a normalized JSON payload, for example:

```json
{
  "openid": "wx-openid-123",
  "message": "帮我看看江苏适合冲哪些985",
  "message_type": "text",
  "metadata": {
    "source": "official_account"
  }
}
```

It should be transformed internally into:

```json
{
  "channel": "wechat",
  "user_id": "wx-openid-123",
  "session_id": null,
  "message": "帮我看看江苏适合冲哪些985",
  "skill_id": null,
  "metadata": {
    "source": "official_account",
    "message_type": "text"
  }
}
```

This allows the core chat flow to stay channel-agnostic.

## Error Handling

### Request Errors

Return `4xx` errors for:

- missing required fields
- empty `message`
- invalid `channel`
- malformed adapter payloads

### Skill Resolution Errors

Return:

- `404` when a direct `skill_id` does not exist
- `409` when a requested skill is disabled or unsupported for the channel

### Skill Execution Errors

If skill execution fails unexpectedly:

- do not leak stack traces in the normal response body
- return a structured fallback response envelope where possible
- append a short diagnostic note in `debug.notes`

This keeps upstream channel integrations stable during early rollout.

## Configuration

The first implementation may not need many new settings, but the design should leave room for:

- enabling or disabling the chat router
- enabling or disabling named skills
- choosing a routing threshold

If settings are added, they should live in `apps/api/app/config.py` with safe development defaults.

## Testing Strategy

### API Tests

Add tests that cover:

- `POST /api/chat/messages` with auto-matching to `zhangxuefeng`
- `POST /api/chat/messages` with explicit `skill_id`
- `POST /api/chat/messages` fallback when no skill matches
- `GET /api/chat/skills` listing registered skills
- `POST /api/chat/skills/{skill_id}/invoke` direct invocation
- `POST /api/chat/channels/wechat` request normalization
- invalid channel validation
- unknown or disabled skill handling

### Service Tests

Add unit tests for:

- registry lookup behavior
- confidence-based skill selection
- fallback generation
- `zhangxuefeng` keyword matching and intent routing

### Non-Goals for Testing

The first implementation should not add:

- end-to-end WeChat protocol tests
- real network tests to external LLMs
- persistence tests for conversation history

## Risks and Constraints

- A rule-based `zhangxuefeng` placeholder will not feel like a full assistant yet
- The first routing threshold may need tuning once real traffic arrives
- Returning structured JSON only pushes final rendering complexity to channel consumers, but that is intentional in v1
- The in-memory registry is simple and correct for v1, but not enough for runtime admin toggles later

## Acceptance Criteria

- The API exposes a dedicated chat router with unified message entry, WeChat adapter entry, skill listing, direct skill invocation, and chat health endpoints
- A `ConversationService` exists and handles no-state request execution
- Skills are registered through a reusable registry abstraction
- The repo includes a placeholder `zhangxuefeng` skill that can match and return structured JSON
- Automatic routing and direct invocation both work through tests
- Unknown skills, invalid channels, and unmatched requests return stable behavior
- API tests pass without requiring any external LLM or channel provider
