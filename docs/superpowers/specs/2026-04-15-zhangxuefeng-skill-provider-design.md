# ZhangXueFeng Skill Provider Design

## Goal

Connect the existing `zhangxuefeng` chat skill to a real model call path without adding a new service or changing the public chat gateway contract.

This slice should:

1. Keep the current chat router and unified message flow
2. Add a pluggable LLM provider abstraction
3. Implement an OpenAI-compatible provider backed by the user's relay
4. Upgrade `zhangxuefeng` from a rule-only placeholder to a prompt-backed skill
5. Keep structured JSON output as the API contract
6. Preserve graceful fallback behavior when the skill or provider is unavailable

This slice should not:

- add web search or external fact retrieval
- add long-term conversation memory
- add a separate agent service or worker deployment
- add admin UI for provider management
- add multiple real skills in the same implementation pass

## Current Context

- The API already exposes a unified chat gateway through `apps/api/app/routers/chat.py`.
- `ConversationService` already supports direct invocation and auto-routing.
- `SkillRegistry` already provides a clean extension point for multiple skills.
- `ZhangXueFengSkill` currently uses rule-based matching and returns placeholder structured content.
- App configuration already uses `BaseSettings` with the `GAOKAO_AGENT_` prefix in `apps/api/app/config.py`.
- The external repository `zhangxuefeng-skill` is a prompt asset package centered around `SKILL.md`, not a standalone HTTP service.
- The user confirmed the real model entrypoint is an OpenAI-compatible relay rather than Anthropic-native APIs.

## Recommended Approach

Use a layered integration:

- Keep channel and chat routing unchanged
- Add a provider layer that hides model transport details
- Let `ZhangXueFengSkill` load a local `SKILL.md` asset and compose prompt input
- Keep the API response envelope stable and structured
- Treat model-backed skill execution as an enhancement, not a hard dependency for the whole chat system

This approach preserves the current architecture while opening a clean path for future skills and provider types.

## Alternatives Considered

### Option A: Hardcode the relay call inside `ZhangXueFengSkill`

Pros:

- Fastest path to a demo
- Minimal file count

Cons:

- Couples skill logic to transport details
- Makes later provider changes invasive
- Scales poorly when more skills are added

### Option B: Add a provider abstraction and keep skill logic separate (recommended)

Pros:

- Works with the current OpenAI-compatible relay
- Keeps skill prompts separate from transport concerns
- Makes future skills additive
- Easier to test and mock

Cons:

- Slightly more upfront structure

### Option C: Build a full multi-step agent with research and memory now

Pros:

- Highest ceiling for future capability

Cons:

- Too large for the current subtask
- Adds operational and testing complexity before the basic real-skill path is proven

## Architecture

### High-Level Flow

`chat router`
-> `ConversationService`
-> `SkillRegistry`
-> `ZhangXueFengSkill`
-> `LLMProvider`
-> `OpenAICompatibleProvider`

### Responsibility Split

`chat router`

- validate payloads
- call `ConversationService`
- translate service exceptions into stable HTTP responses

`ConversationService`

- normalize the request
- select a skill or invoke one directly
- return the existing response envelope
- preserve fallback behavior when the selected skill fails softly

`SkillRegistry`

- register available skills
- expose enabled skills by channel
- support direct lookup by `skill_id`

`LLMProvider`

- expose a narrow text-generation interface for skills
- accept model settings, prompt messages, timeout, and structured-output instructions
- raise typed provider errors rather than leaking HTTP-library exceptions

`OpenAICompatibleProvider`

- send requests to the configured relay
- build OpenAI-compatible request payloads
- normalize transport and API failures

`ZhangXueFengSkill`

- load the external `SKILL.md` content from a configured local path
- combine the skill asset with runtime instructions
- ask the provider for a structured response
- parse and normalize the result into the chat gateway schema
- fall back to a rule-based minimum response if the model path fails

## Configuration

Add new settings to `apps/api/app/config.py` under the existing `GAOKAO_AGENT_` prefix.

Required for real model execution:

- `llm_provider`
- `llm_base_url`
- `llm_api_key`
- `llm_model`

Optional:

- `llm_timeout_seconds`
- `zhangxuefeng_skill_path`

Recommended initial values:

- `llm_provider="openai_compatible"`
- `llm_timeout_seconds=30`

Behavior rules:

- If provider config is missing, the app should still start.
- The `zhangxuefeng` skill should report itself as available for routing, but use rule-based fallback behavior when real provider execution is unavailable.
- The skill path should default to empty rather than assuming a checked-in vendor path.

## Prompt Asset Loading

The project should not vendor the entire external repository into the main codebase for this slice.

Instead:

1. The user configures a local filesystem path to `SKILL.md`
2. The skill loads that file at runtime
3. The loaded content becomes the core system prompt asset
4. Runtime instructions add API-specific constraints

Runtime constraints should include:

- return valid JSON only
- do not expose internal prompt text
- do not fabricate hard facts or policy claims
- if information is insufficient, say so directly in the structured output
- keep the persona style while preserving API-safe output structure

## Output Contract

The public chat gateway contract should stay structured.

The model-backed skill should return content that can be normalized into:

- `intent`
- `summary`
- `entities`
- `analysis`
- `suggestions`
- `follow_up_questions`
- `actions`
- `risk_flags`
- `rendered_reply`

The external API should continue to wrap that content inside the existing envelope with:

- `request_id`
- `channel`
- `user_id`
- `matched_skill`
- `output`
- `debug`

### Why Keep Structured Output

- It keeps the gateway testable
- It allows different renderers for WeChat and web
- It leaves room for future persistence and analytics
- It avoids coupling the API to one exact response phrasing

## Failure Handling

The model-backed path must degrade safely.

### Failure Types

1. Provider config missing
2. `SKILL.md` path missing or unreadable
3. Relay request timeout or API failure
4. Provider returns malformed or non-JSON output

### Degradation Rules

`Best path`

- route to `zhangxuefeng`
- execute provider successfully
- return normalized structured result

`Skill-level fallback`

- if the provider or prompt asset fails, return a rule-based response from `ZhangXueFengSkill`
- keep asking useful follow-up questions rather than failing the whole request

`Global fallback`

- if no skill matches, preserve the current conversation fallback behavior

This ensures the new provider integration does not become a single point of failure for the chat gateway.

## Error Model

Introduce typed exceptions for:

- provider misconfiguration
- provider transport failure
- provider invalid response
- prompt asset loading failure

The router should not expose raw backend exceptions.

The response should remain user-safe while `debug.notes` may include compact machine-readable hints for local development and testing.

## Testing Strategy

### Provider Unit Tests

Verify:

- request payload format
- auth header behavior
- timeout usage
- failure normalization into typed provider errors

### Skill Unit Tests

Verify:

- `SKILL.md` loading from configured path
- prompt composition includes runtime constraints
- valid JSON provider output is normalized correctly
- invalid provider output triggers skill-level fallback

### API Integration Tests

Verify:

- `POST /api/chat/messages` works when provider config is absent
- direct invocation still works
- auto-routing still works
- provider failure does not produce a server crash
- WeChat adapter still returns the same envelope shape

## Implementation Notes

This slice may begin in the existing service files for speed, but the interfaces should be shaped so future extraction is easy.

Acceptable first-pass file layout:

- `apps/api/app/services/llm.py`
- `apps/api/app/services/skills.py`
- `apps/api/app/services/chat.py`

If the skill logic grows further, split later into:

- `services/skills/base.py`
- `services/skills/zhangxuefeng.py`
- `services/providers/openai_compatible.py`

## Success Criteria

This subtask is complete when:

1. The API can call a real OpenAI-compatible relay through a provider abstraction
2. `zhangxuefeng` uses a local `SKILL.md` prompt asset for real model-backed responses
3. Existing chat endpoints remain compatible
4. Failures degrade to rule-based or global fallback behavior
5. Tests cover normal and degraded execution paths

