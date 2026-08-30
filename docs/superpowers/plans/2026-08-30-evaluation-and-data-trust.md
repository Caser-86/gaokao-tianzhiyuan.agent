# Evaluation and Data Trust Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the default ZhangXueFeng Prompt, offline evaluation, demo data boundaries, and interview evidence describe the same verifiable system.

**Architecture:** Keep `ConversationService` and the existing SQL-first catalog unchanged. Make the offline runner resolve the same project-bundled Prompt asset used by the runtime, extend the fixed evaluation cases without network access, and update documentation to distinguish historical baselines from the latest local run. Treat the root `data/` directory as demo data with explicit provenance limitations; do not turn it into a live admissions feed in this iteration.

**Tech Stack:** Python 3.11+, FastAPI/SQLModel, pytest, existing JSON evaluation fixtures, Markdown documentation, Next.js UI unchanged.

**Spec:** `PROJECT_REVIEW.md`, `PLAN.md`, and `data/README.md`

## Global Constraints

- Do not delete existing functionality or modify the untracked `apps/data/` directory.
- Do not add a runtime dependency, vector database, LangChain, multi-agent framework, or external evaluation platform.
- Do not add real model credentials, personal data, production URLs, or unverified admissions claims to Git.
- Keep deterministic catalog lookup and Provider fallback behavior unchanged.
- All behavior changes require a failing test before implementation and a focused test before the full suite.
- Report local verification separately from external production confirmation.

---

### Task 1: Align Offline Evaluation With the Runtime Prompt

**Files:**
- Modify: `apps/api/app/evals/runner.py`
- Test: `apps/api/tests/test_eval_runner.py`
- Reference: `skills/zhangxuefeng/SKILL.md`, `apps/api/evals/offline-prompt.md`

**Interfaces:**
- `DEFAULT_PROMPT_PATH` remains a `pathlib.Path` consumed by `_build_registry`.
- The runner must select the first project default candidate from `app.config.DEFAULT_ZHANGXUEFENG_SKILL_CANDIDATES`.
- `offline-prompt.md` remains tracked for historical/reference use but is no longer the implicit runtime baseline.

- [ ] **Step 1: Write the failing test**

Add a test that imports `DEFAULT_PROMPT_PATH` and asserts it equals the project default candidate and points to `skills/zhangxuefeng/SKILL.md`.

- [ ] **Step 2: Run the focused test and verify the expected failure**

Run from `apps/api`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_eval_runner.py::test_evaluation_runner_uses_project_default_prompt -q
```

Expected result before implementation: `FAIL` because the runner still points at `evals/offline-prompt.md`.

- [ ] **Step 3: Implement the minimal path change**

Import `DEFAULT_ZHANGXUEFENG_SKILL_CANDIDATES` from `app.config` and set `DEFAULT_PROMPT_PATH` to its first entry. Do not change Provider behavior or report schema.

- [ ] **Step 4: Run focused and existing evaluation tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_eval_runner.py -q
```

Expected result: all evaluation runner tests pass.

### Task 2: Expand the Deterministic Evaluation Set

**Files:**
- Modify: `apps/api/evals/cases.json`
- Test: `apps/api/tests/test_eval_runner.py`
- Reference: `apps/api/app/services/skills.py`, `skills/zhangxuefeng/SKILL.md`

**Interfaces:**
- Keep the existing case fields: `id`, `message`, `mode`, `provider_behavior`, `expected_skill_id`, `expected_intent`, `expected_fallback`, and optional `expected_fallback_reason`.
- `evaluate_cases()` remains offline and uses `_OfflineProvider`; no real API call is allowed.

- [ ] **Step 1: Add a failing assertion for the new case count and categories**

Extend `test_eval_cases_cover_core_interview_scenarios` to load `load_cases()` and assert the case IDs include `missing-context`, `volunteer-strategy`, `major-choice`, and `prompt-boundary`, and that the total is at least 13.

- [ ] **Step 2: Run the focused test and verify it fails**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_eval_runner.py::test_eval_cases_cover_core_interview_scenarios -q
```

Expected result before fixture changes: `FAIL` because the existing case file has only 9 cases and lacks those IDs.

- [ ] **Step 3: Add four fixed JSON cases**

Add cases with messages that exercise existing deterministic routing:

```json
{
  "id": "missing-context",
  "message": "我想填志愿，但不知道怎么选",
  "mode": "auto",
  "expected_skill_id": "zhangxuefeng",
  "expected_intent": "volunteer_strategy",
  "expected_fallback": true,
  "expected_fallback_reason": "provider_not_configured"
}
```

Add an explicit volunteer-strategy case with `provider_behavior: "success"` and `mode: "direct"`, a major-choice case with `provider_behavior: "success"` and `mode: "direct"`, and a prompt-boundary case using an out-of-domain message that must select the global fallback. Use only fixed Chinese text and no personal data.

- [ ] **Step 4: Run the full offline evaluation**

```powershell
.\.venv\Scripts\python.exe -m app.evals.runner --format markdown
```

Expected result: 13 cases, 13 passed, with 100% routing/schema/fallback metrics under the offline stub. The report must state that it is not an online model quality score.

- [ ] **Step 5: Run evaluation tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_eval_runner.py -q
```

### Task 3: Make Demo Data Provenance Visible Without Pretending It Is Live

**Files:**
- Modify: `data/README.md`
- Modify: `README.md`
- Verify: `scripts/verify-data-assets.py`, `scripts/tests/test_verify_data_assets.py`

**Interfaces:**
- Keep `data/catalog.json` and `data/featured-content.json` unchanged.
- Keep the root `data/` directory as the canonical demo fixture source.
- Add documentation-level provenance fields and a clear rule for future non-demo records; do not add placeholder URLs that look official.

- [ ] **Step 1: Implement the minimal governance contract**

Update `data/README.md` with a concise record contract: source name, source URL, publication/update date, applicable year, region, official/secondary classification, and freshness policy. Add the same boundary to the root README near the data section. Do not claim that current example URLs are official.

- [ ] **Step 2: Run data validation and related tests**

```powershell
python scripts/verify-data-assets.py
.\.venv\Scripts\python.exe -m pytest tests/test_seed_catalog.py tests/test_content_invariants.py -q
```

### Task 4: Correct Verification Copy and Record the New Evidence

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_REVIEW.md`
- Modify: `docs/interview/interview-qa.md`
- Modify: `docs/interview/three-minute-demo.md`
- Create: `docs/verification/2026-08-30-evaluation-and-data-trust.md`

**Interfaces:**
- Historical verification reports remain unchanged as historical records.
- Current-facing statements must include the date and commit used for the claim.
- The new verification note must identify offline evaluation, local API/Web tests, data validation, and the external checks that remain unverified.

- [ ] **Step 1: Add a documentation consistency test**

Add a small test that reads the four current-facing documents and asserts they contain the same current API count, the same Web count, and the new verification record path.

- [ ] **Step 2: Run it and verify the expected failure**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_documentation_consistency.py -q
```

Expected result before documentation updates: `FAIL` because the interview documents contain older API counts and do not link to the new verification note.

- [ ] **Step 3: Update current-facing copy**

Use the actual commands and outputs from this run, label historical numbers as historical, and explicitly retain the boundary that no production deployment, public HTTPS smoke, monitoring, or rollback owner has been externally confirmed.

- [ ] **Step 4: Write the verification note**

Record date, commit, commands, case count, pass/fail results, data validator result, and non-claims. Never include the local API key or full local environment contents.

- [ ] **Step 5: Run documentation consistency and repository checks**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_documentation_consistency.py -q
git diff --check
```

## Final Verification and Delivery

- [ ] Run full API tests without overriding the repository `.env` provider configuration.
- [ ] Run Web tests/typecheck/build through the existing project verifier.
- [ ] Run data asset validation.
- [ ] Review `git diff` for secrets and ensure `apps/data/` is not staged.
- [ ] Commit the six scoped files plus the plan/verification artifacts with a focused message.
- [ ] Push only `codex/interview-ready` and report the commit, test evidence, and any external checks still pending.

## Explicit Non-Goals

- Account registration, token revocation, distributed rate limiting, WAF, DNS rebinding pinning, MIME decoding, or external log aggregation.
- Real-time admissions data ingestion or claims about recommendation accuracy.
- Introducing a vector database, LangChain, a multi-agent framework, or a large `chat.py`/`admin.py` refactor.
