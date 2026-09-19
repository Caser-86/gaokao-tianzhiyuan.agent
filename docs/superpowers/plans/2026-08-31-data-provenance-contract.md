# Data Provenance Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose a small, testable provenance contract so public catalog responses and detail pages clearly identify demo data, freshness, scope, and non-authoritative limitations.

**Architecture:** Store one top-level `data_provenance` object in the canonical root `data/catalog.json`. The API reads that metadata with a safe built-in fallback and adds the same object to public search, list, and detail responses without changing SQLModel tables or migrations. The Web API client maps the snake_case contract to TypeScript and renders a shared notice on school and major detail pages.

**Tech Stack:** Python 3.11+, FastAPI/SQLModel, standard-library JSON/date validation, pytest, Next.js 15, React 19, Vitest, Testing Library, existing CSS.

**Spec:** `data/README.md`, `PROJECT_REVIEW.md`, and `docs/operations/production-readiness-matrix.md`

## Global Constraints

- Preserve all existing catalog content, relations, fallback behavior, and the untracked `apps/data/` directory.
- Do not add a database migration or runtime dependency; this is a read-only public metadata contract.
- Demo metadata must not claim official status, current admissions cutoffs, ranking authority, or recommendation accuracy.
- Keep source URLs optional for demo metadata and require human review for future non-demo records.
- Add tests before implementation for validator, API serialization, client mapping, and page rendering behavior.
- Do not place API keys, personal data, or production credentials in fixtures, screenshots, logs, or documentation.

---

### Task 1: Define and Validate the Canonical Provenance Object

**Files:**
- Modify: `data/catalog.json`
- Modify: `scripts/verify-data-assets.py`
- Test: `scripts/tests/test_verify_data_assets.py`
- Update: `data/README.md`

**Contract:** `catalog.json.data_provenance` is an object with:

```json
{
  "status": "demo",
  "source_name": "项目手工编写演示数据",
  "source_url": null,
  "updated_at": "2026-08-30",
  "applicable_year": null,
  "region": "多地区示例",
  "official": false,
  "disclaimer": "仅用于功能演示，不构成招生、排名或志愿决策依据。"
}
```

The validator accepts `source_url: null` and `applicable_year: null` only when `status == "demo"`. It requires a non-empty HTTP(S) `source_url` and an integer `applicable_year` for future non-demo records, and always requires a valid ISO date in `updated_at`, a non-empty `source_name`, `region`, and `disclaimer`, plus a boolean `official`. `status` is limited to `demo`, `secondary`, or `official`; `official` must remain `false` for `demo`.

- [ ] **Step 1: Write failing validator tests**

Add tests for: missing `data_provenance` is rejected; the repository fixture with demo metadata is accepted; a non-demo record without source URL/year is rejected.

- [ ] **Step 2: Run focused tests and verify failure**

```powershell
python scripts/tests/test_verify_data_assets.py
```

Expected result before implementation: the new missing/invalid metadata tests fail because the validator does not inspect `data_provenance`.

- [ ] **Step 3: Add the demo metadata object**

Insert the exact contract above under the top-level `data_provenance` key in `data/catalog.json`. Do not edit school, major, ranking, or featured records.

- [ ] **Step 4: Implement minimal validator functions**

Add `_validate_data_provenance(provenance, errors)` and call it from `validate_data`. Use `datetime.date.fromisoformat` for the date check and `urllib.parse.urlparse` for non-demo HTTP(S) URL validation. Keep error messages field-specific.

- [ ] **Step 5: Run data tests and validator**

```powershell
python scripts/tests/test_verify_data_assets.py
python scripts/verify-data-assets.py
```

Expected result: all data tests pass; the validator reports valid root data and may retain its existing warning that `apps/data/` is not validated.

- [ ] **Step 6: Document the contract**

Update `data/README.md` so the required fields and demo/non-demo distinction exactly match the validator.

### Task 2: Return Provenance From Public API Endpoints

**Files:**
- Create: `apps/api/app/services/data_provenance.py`
- Modify: `apps/api/app/services/catalog.py`
- Test: `apps/api/tests/test_public_catalog_api.py`
- Test: `apps/api/tests/test_data_provenance.py`

**Interfaces:**
- `get_data_provenance() -> dict[str, object]` returns a fresh copy of the normalized metadata.
- `load_catalog()` includes `data_provenance` for internal callers.
- `GET /api/public/search-entry`, `GET /api/public/schools`, `GET /api/public/majors`, `GET /api/public/schools/{slug}`, and `GET /api/public/majors/{slug}` include `data_provenance`.
- Existing fields and response status codes remain unchanged.

- [ ] **Step 1: Write failing service and API tests**

Assert the provenance helper returns `status == "demo"`, `official is False`, and a fresh object; assert public school list and school detail responses expose the same `data_provenance` fields.

- [ ] **Step 2: Run focused tests and verify failure**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_data_provenance.py tests/test_public_catalog_api.py -q
```

Expected result before implementation: the new helper import or response assertions fail because the API does not expose the contract.

- [ ] **Step 3: Implement metadata loading**

Create `data_provenance.py` with the exact fallback contract and a loader that reads the top-level object from the repository `data/catalog.json` when available. Normalize only the known fields and return a copy; never log the file contents or environment variables.

- [ ] **Step 4: Add metadata to public serializers**

Use `get_data_provenance()` in `catalog.py` to add metadata to the five public response families. For detail responses, merge the object at the response top level rather than inside a school/major entity. Keep ranking reference URLs and existing entity fields unchanged.

- [ ] **Step 5: Run focused API tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_data_provenance.py tests/test_public_catalog_api.py -q
```

### Task 3: Display the Boundary on Web Detail Pages

**Files:**
- Create: `apps/web/components/public/data-provenance-notice.tsx`
- Modify: `apps/web/lib/public-content-api.ts`
- Modify: `apps/web/app/schools/[slug]/page.tsx`
- Modify: `apps/web/app/majors/[slug]/page.tsx`
- Modify: `apps/web/app/globals.css`
- Test: `apps/web/tests/public-content-api.test.ts`
- Test: `apps/web/tests/public-pages.test.tsx`

**Interfaces:**
- TypeScript `DataProvenance` maps `status`, `source_name`, `source_url`, `updated_at`, `applicable_year`, `region`, `official`, and `disclaimer` to camelCase fields.
- `SchoolDetail` and `MajorDetail` receive `dataProvenance` from the API client.
- `DataProvenanceNotice` accepts `provenance?: DataProvenance` and renders nothing only for legacy test/mocked payloads that omit the field; real API payloads always render the notice.

- [ ] **Step 1: Write failing client and page tests**

Add API-client mapping assertions for `data_provenance`, and add school/major page assertions for the visible `演示数据` label, update date, region, and disclaimer.

- [ ] **Step 2: Run focused Web tests and verify failure**

```powershell
Set-Location ..\web
npm test -- --run tests/public-content-api.test.ts tests/public-pages.test.tsx
```

Expected result before implementation: the new mapping/page assertions fail because the client types and pages do not handle provenance.

- [ ] **Step 3: Implement the client mapping**

Add the `DataProvenance` type and map `data_provenance` in `getSchoolBySlug` and `getMajorBySlug`. Keep existing mocks backward-compatible by making the renderer prop optional.

- [ ] **Step 4: Implement the shared notice**

Render a semantic `aside` with a heading/label, disclaimer, update date, applicable region, and a source link only when `sourceUrl` is non-empty. Use existing visual tokens and no new icon or UI dependency.

- [ ] **Step 5: Render on both detail pages and style it**

Place the notice below each detail page masthead and add responsive CSS using the existing palette. Do not alter catalog cards or admin pages in this task.

- [ ] **Step 6: Run focused Web tests**

```powershell
npm test -- --run tests/public-content-api.test.ts tests/public-pages.test.tsx
```

### Task 4: Update Evidence and Verify Delivery

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_REVIEW.md`
- Modify: `docs/interview/interview-qa.md`
- Modify: `docs/interview/three-minute-demo.md`
- Modify: `docs/operations/production-readiness-matrix.md`
- Create: `docs/verification/2026-08-31-data-provenance-contract.md`

- [ ] **Step 1: Update current-facing explanation**

State that public catalog responses now carry demo status, update date, region, and disclaimer; keep the explicit boundary that this is not a live official admissions feed.

- [ ] **Step 2: Record verification evidence**

Record the exact commands, results, changed API contract, Web behavior, and the persistent `apps/data/` warning. Do not record local credentials or claim production deployment.

- [ ] **Step 3: Run full verification**

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify-project.ps1
```

Also run `git diff --check`, changed-file Ruff, and a secret scan over staged files.

- [ ] **Step 4: Review and deliver**

Stage only the listed files, confirm `apps/data/` remains unstaged, commit with `feat: expose catalog data provenance`, push `codex/interview-ready`, and verify local/remote HEAD equality.

## Explicit Non-Goals

- No SQLModel schema change, Alembic migration, live data ingestion, source crawling, or external source verification.
- No account authentication, token revocation, rate limiting, DNS rebinding defense, or model/provider behavior change.
- No deletion or modification of `apps/data/`.
