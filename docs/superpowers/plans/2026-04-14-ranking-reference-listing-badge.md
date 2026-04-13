# Ranking Reference Listing Badge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a lightweight `含参考榜单` badge to school and major listing cards when their detail pages include ranking-reference content.

**Architecture:** Extend the public list responses with a derived `has_ranking_references` boolean and map it into the web summary types as `hasRankingReferences`. Keep the homepage card structure intact and only append a small metadata tag when the boolean is true.

**Tech Stack:** FastAPI, Python, Next.js 15, React 19, TypeScript, Vitest, Testing Library, Pytest

---

### Task 1: Add failing API coverage for ranking-reference listing flags

**Files:**
- Modify: `apps/api/tests/test_public_catalog_api.py`
- Modify: `apps/api/app/services/catalog.py`

- [ ] **Step 1: Write the failing test**

Extend the school-list and major-list API tests so they assert `has_ranking_references`.

```python
def test_list_schools_filters_by_region() -> None:
    response = client.get("/api/public/schools", params={"region": "江苏"})

    assert response.status_code == 200
    assert response.json()["items"][0]["has_ranking_references"] is True


def test_list_majors_returns_catalog_cards() -> None:
    response = client.get("/api/public/majors")

    payload = response.json()
    assert payload["items"][0]["has_ranking_references"] is True
    assert payload["items"][-1]["has_ranking_references"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_public_catalog_api.py -v`

Expected: FAIL because list serializers do not yet include `has_ranking_references`.

- [ ] **Step 3: Write minimal implementation**

Update the school and major list serializers in `apps/api/app/services/catalog.py`.

```python
filtered.append(
    {
        "slug": school["slug"],
        "name": school["name"],
        "region": school["region"],
        "city": school["city"],
        "tags": school["tags"],
        "summary": school["summary"],
        "has_ranking_references": bool(school.get("ranking_references")),
    }
)
```

```python
items = [
    {
        "slug": major["slug"],
        "name": major["name"],
        "discipline": major["discipline"],
        "recommended_regions": major["recommended_regions"],
        "summary": major["summary"],
        "has_ranking_references": bool(major.get("ranking_references")),
    }
    for major in majors
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_public_catalog_api.py -v`

Expected: PASS with list responses exposing the derived boolean flag.

- [ ] **Step 5: Commit**

```bash
git add apps/api/tests/test_public_catalog_api.py apps/api/app/services/catalog.py
git commit -m "feat(api): add ranking reference listing flags"
```

### Task 2: Render listing badges on homepage cards

**Files:**
- Modify: `apps/web/lib/public-content-api.ts`
- Modify: `apps/web/app/page.tsx`
- Modify: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Write the failing test**

Extend the homepage page test so it expects `含参考榜单` on seeded examples and omits it for items without ranking references.

```tsx
const RANKING_BADGE_TEXT = '\u542b\u53c2\u8003\u699c\u5355';

listSchoolsMock.mockResolvedValue({
  items: [
    {
      slug: 'southeast-university',
      name: '\u4e1c\u5357\u5927\u5b66',
      region: '\u6c5f\u82cf',
      city: '\u5357\u4eac',
      tags: ['985'],
      summary: '\u5de5\u79d1\u89c1\u957f\u3002',
      hasRankingReferences: true,
    },
    {
      slug: 'plain-school',
      name: '\u666e\u901a\u5b66\u6821',
      region: '\u5c71\u4e1c',
      city: '\u6d4e\u5357',
      tags: ['\u53cc\u975e'],
      summary: '\u65e0\u989d\u5916\u699c\u5355\u793a\u4f8b\u3002',
      hasRankingReferences: false,
    },
  ],
  total: 2,
});

expect(screen.getAllByText(RANKING_BADGE_TEXT)).toHaveLength(2);
expect(screen.getByText('\u4e1c\u5357\u5927\u5b66')).toBeInTheDocument();
expect(screen.getByText('\u4e34\u5e8a\u533b\u5b66')).toBeInTheDocument();
```

Use one school and one major seeded example with `true`, and one non-seeded example with `false` so the badge count is explicit.

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`

Expected: FAIL because the web summary types and homepage cards do not yet support `hasRankingReferences`.

- [ ] **Step 3: Write minimal implementation**

Update summary types and list mappers in `apps/web/lib/public-content-api.ts`, then render the badge in homepage metadata rows.

```tsx
export type SchoolSummary = {
  slug: string;
  name: string;
  region: string;
  city: string;
  tags: string[];
  summary: string;
  hasRankingReferences?: boolean;
};
```

```tsx
{school.hasRankingReferences ? <span>{'\u542b\u53c2\u8003\u699c\u5355'}</span> : null}
```

Apply the same pattern to major cards and to the list payload mapping from `has_ranking_references` to `hasRankingReferences`.

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`

Expected: PASS with seeded cards showing the badge and non-seeded cards omitting it.

- [ ] **Step 5: Commit**

```bash
git add apps/web/lib/public-content-api.ts apps/web/app/page.tsx apps/web/tests/public-pages.test.tsx
git commit -m "feat(web): show ranking reference listing badges"
```

### Task 3: Run final API and Web verification

**Files:**
- Test: `apps/api/tests/test_public_catalog_api.py`
- Test: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Run focused API verification**

Run: `python -m pytest tests/test_public_catalog_api.py -v`

Expected: PASS

- [ ] **Step 2: Run focused Web verification**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`

Expected: PASS

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
git add docs/superpowers/plans/2026-04-14-ranking-reference-listing-badge.md
git commit -m "docs: add ranking reference listing badge plan"
```
