# Ranking Reference Seed Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand ranking-reference seed data so more school and major detail pages demonstrate the feature in realistic content scenarios.

**Architecture:** Keep the existing ranking-reference schema, API shape, and web rendering untouched while extending `data/catalog.json` with additional seeded references. Add focused API coverage for one more school and one more major so the expanded seed set is verified without turning web tests into content snapshots.

**Tech Stack:** JSON catalog data, FastAPI, Python, Pytest, Next.js 15, Vitest

---

### Task 1: Add failing API coverage for the expanded ranking-reference seed set

**Files:**
- Modify: `apps/api/tests/test_public_catalog_api.py`

- [ ] **Step 1: Write the failing test**

Add one school-detail test for `west-china-medical-center` and one major-detail test for `computer-science` that verify `ranking_references` are returned.

```python
def test_school_detail_returns_ranking_references_for_west_china() -> None:
    response = client.get("/api/public/schools/west-china-medical-center")

    assert response.status_code == 200
    assert response.json()["ranking_references"] == [
        {
            "source": "软科中国医学院校排名",
            "year": 2025,
            "label": "全国前 10",
            "scope": "医学院校",
            "note": "适合作为临床医学培养平台的横向参考。",
            "url": "https://example.com/rankings/west-china-medical-center",
        }
    ]


def test_major_detail_returns_ranking_references_for_computer_science() -> None:
    response = client.get("/api/public/majors/computer-science")

    assert response.status_code == 200
    assert response.json()["ranking_references"] == [
        {
            "source": "教育部学科评估",
            "year": 2023,
            "label": "计算机科学与技术 B+",
            "scope": "一级学科",
            "note": "适合作为院校计算机学科实力参考。",
            "url": "https://example.com/rankings/computer-science",
        }
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_public_catalog_api.py -v`

Expected: FAIL because the additional school and major seed data do not yet include `ranking_references`.

- [ ] **Step 3: Write minimal implementation**

No production code in this task. Stop after the new tests are red.

- [ ] **Step 4: Run test to verify it still fails for the expected reason**

Run: `python -m pytest tests/test_public_catalog_api.py -v`

Expected: FAIL with missing `ranking_references` for `west-china-medical-center` and `computer-science`.

- [ ] **Step 5: Commit**

```bash
git add apps/api/tests/test_public_catalog_api.py
git commit -m "test(api): cover expanded ranking reference seed data"
```

### Task 2: Seed ranking references for the additional school and major

**Files:**
- Modify: `data/catalog.json`

- [ ] **Step 1: Write the failing test**

Use the already-red API tests from Task 1 as the failing coverage for this task.

```python
assert response.json()["ranking_references"] == [
    {
        "source": "软科中国医学院校排名",
        "year": 2025,
        "label": "全国前 10",
        "scope": "医学院校",
        "note": "适合作为临床医学培养平台的横向参考。",
        "url": "https://example.com/rankings/west-china-medical-center",
    }
]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_public_catalog_api.py -v`

Expected: FAIL because the seed data is still missing from `data/catalog.json`.

- [ ] **Step 3: Write minimal implementation**

Add `ranking_references` to `west-china-medical-center` and `computer-science` in `data/catalog.json` using the existing schema.

```json
"ranking_references": [
  {
    "source": "软科中国医学院校排名",
    "year": 2025,
    "label": "全国前 10",
    "scope": "医学院校",
    "note": "适合作为临床医学培养平台的横向参考。",
    "url": "https://example.com/rankings/west-china-medical-center"
  }
]
```

```json
"ranking_references": [
  {
    "source": "教育部学科评估",
    "year": 2023,
    "label": "计算机科学与技术 B+",
    "scope": "一级学科",
    "note": "适合作为院校计算机学科实力参考。",
    "url": "https://example.com/rankings/computer-science"
  }
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_public_catalog_api.py -v`

Expected: PASS with all four detail examples returning seeded `ranking_references`.

- [ ] **Step 5: Commit**

```bash
git add data/catalog.json apps/api/tests/test_public_catalog_api.py
git commit -m "feat(data): expand ranking reference seed content"
```

### Task 3: Run final verification for the expanded seed data

**Files:**
- Test: `apps/api/tests/test_public_catalog_api.py`
- Test: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Run focused API verification**

Run: `python -m pytest tests/test_public_catalog_api.py -v`

Expected: PASS

- [ ] **Step 2: Run focused Web verification**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`

Expected: PASS with ranking-reference rendering behavior still green

- [ ] **Step 3: Run full Web test suite**

Run: `node ./node_modules/vitest/vitest.mjs run`

Expected: PASS with all `apps/web` tests green

- [ ] **Step 4: Run production build**

Run: `node ./node_modules/next/dist/bin/next build`

Expected: PASS with a successful Next.js production build. The known Windows SWC policy warning is acceptable if the build completes successfully via the wasm fallback.

- [ ] **Step 5: Review git status**

Run: `git status --short`

Expected: clean working tree after the intended commits, or only the plan file before its own commit

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/plans/2026-04-14-ranking-reference-seed-data.md
git commit -m "docs: add ranking reference seed data plan"
```
