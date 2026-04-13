# Ranking References Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add structured ranking references to school and major detail content and render them on the public detail pages.

**Architecture:** Extend the existing `data/catalog.json -> apps/api public catalog service -> apps/web public-content-api -> school/major detail pages` pipeline with a new `ranking_references` field. Keep ranking references as detail-only content, expose them through the existing public detail endpoints, and render them with a focused shared web component that is only shown when data is present.

**Tech Stack:** FastAPI, Python, JSON catalog data, Next.js 15, React 19, TypeScript, Vitest, Testing Library, Pytest

---

### Task 1: Add ranking references to the public catalog detail API

**Files:**
- Modify: `data/catalog.json`
- Modify: `apps/api/tests/test_public_catalog_api.py`
- Modify: `apps/api/app/services/catalog.py`

- [ ] **Step 1: Write the failing API tests**

Add `ranking_references` expectations to the existing school and major detail API tests in `apps/api/tests/test_public_catalog_api.py`.

```python
def test_school_detail_returns_modular_sections() -> None:
    response = client.get("/api/public/schools/southeast-university")

    assert response.status_code == 200
    assert response.json()["ranking_references"] == [
        {
            "source": "软科中国大学排名",
            "year": 2025,
            "label": "全国第 15 名",
            "scope": "综合类高校",
            "note": "用于综合实力参考，不等同于具体专业优势。",
            "url": "https://example.com/rankings/southeast-university",
        }
    ]


def test_major_detail_returns_career_and_risk_sections() -> None:
    response = client.get("/api/public/majors/clinical-medicine")

    assert response.status_code == 200
    assert response.json()["ranking_references"] == [
        {
            "source": "教育部学科评估",
            "year": 2023,
            "label": "临床医学 A-",
            "scope": "一级学科",
            "note": "适合作为医学学科实力参考。",
            "url": "https://example.com/rankings/clinical-medicine",
        }
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_public_catalog_api.py -v`

Expected: FAIL because the current catalog data and API detail responses do not include `ranking_references`.

- [ ] **Step 3: Write minimal implementation**

Add one school example and one major example to `data/catalog.json`, then make sure the detail service continues to return the full objects unchanged.

```json
"ranking_references": [
  {
    "source": "软科中国大学排名",
    "year": 2025,
    "label": "全国第 15 名",
    "scope": "综合类高校",
    "note": "用于综合实力参考，不等同于具体专业优势。",
    "url": "https://example.com/rankings/southeast-university"
  }
]
```

```python
def get_school_detail(slug: str) -> dict[str, Any] | None:
    schools = load_catalog()["schools"]
    return next((school for school in schools if school["slug"] == slug), None)


def get_major_detail(slug: str) -> dict[str, Any] | None:
    majors = load_catalog()["majors"]
    return next((major for major in majors if major["slug"] == slug), None)
```

If the service already returns the full object, the only code change here may be the JSON data plus test expectations.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_public_catalog_api.py -v`

Expected: PASS with school and major detail responses returning `ranking_references`.

- [ ] **Step 5: Commit**

```bash
git add data/catalog.json apps/api/tests/test_public_catalog_api.py apps/api/app/services/catalog.py
git commit -m "feat(api): add ranking references to public catalog detail"
```

### Task 2: Render ranking references on school and major detail pages

**Files:**
- Create: `apps/web/components/public/ranking-reference-list.tsx`
- Modify: `apps/web/lib/public-content-api.ts`
- Modify: `apps/web/app/schools/[slug]/page.tsx`
- Modify: `apps/web/app/majors/[slug]/page.tsx`
- Modify: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Write the failing Web tests**

Extend `apps/web/tests/public-pages.test.tsx` so both detail pages expect a `参考榜单` section when ranking references are present, and no section when the field is absent.

```tsx
const RANKING_SECTION_TITLE = '\u53c2\u8003\u699c\u5355';

test('school page renders ranking references when present', async () => {
  getSchoolBySlugMock.mockResolvedValue({
    slug: 'southeast-university',
    name: '\u4e1c\u5357\u5927\u5b66',
    region: '\u6c5f\u82cf',
    city: '\u5357\u4eac',
    tags: ['985'],
    summary: '\u5de5\u79d1\u89c1\u957f\u3002',
    sections: [],
    relatedMajors: ['architecture'],
    rankingReferences: [
      {
        source: '\u8f6f\u79d1\u4e2d\u56fd\u5927\u5b66\u6392\u540d',
        year: 2025,
        label: '\u5168\u56fd\u7b2c 15 \u540d',
        scope: '\u7efc\u5408\u7c7b\u9ad8\u6821',
        note: '\u7528\u4e8e\u7efc\u5408\u5b9e\u529b\u53c2\u8003\uff0c\u4e0d\u7b49\u540c\u4e8e\u5177\u4f53\u4e13\u4e1a\u4f18\u52bf\u3002',
        url: 'https://example.com/rankings/southeast-university',
      },
    ],
  });

  render(await SchoolPage({ params: Promise.resolve({ slug: 'southeast-university' }) }));

  expect(screen.getByRole('heading', { name: RANKING_SECTION_TITLE })).toBeInTheDocument();
  expect(screen.getByText('\u8f6f\u79d1\u4e2d\u56fd\u5927\u5b66\u6392\u540d')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: '\u67e5\u770b\u6765\u6e90' })).toHaveAttribute(
    'href',
    'https://example.com/rankings/southeast-university',
  );
});

test('major page omits ranking references when absent', async () => {
  getMajorBySlugMock.mockResolvedValue({
    slug: 'clinical-medicine',
    name: '\u4e34\u5e8a\u533b\u5b66',
    discipline: '\u533b\u5b66',
    recommendedRegions: ['\u6c5f\u82cf'],
    summary: '\u57f9\u517b\u5468\u671f\u957f\u3002',
    sections: [],
    relatedSchools: ['southeast-university'],
    rankingReferences: [],
  });

  render(await MajorPage({ params: Promise.resolve({ slug: 'clinical-medicine' }) }));

  expect(screen.queryByRole('heading', { name: RANKING_SECTION_TITLE })).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`

Expected: FAIL because the web types and detail pages do not yet support `rankingReferences`.

- [ ] **Step 3: Write minimal implementation**

Add a ranking-reference type in `apps/web/lib/public-content-api.ts`, map the API field through both detail fetchers, and render a small shared list component from both detail pages.

```tsx
export type RankingReference = {
  source: string;
  year: number;
  label: string;
  scope?: string;
  note?: string;
  url?: string;
};

export type SchoolDetail = SchoolSummary & {
  sections: PageSection[];
  relatedMajors: string[];
  rankingReferences: RankingReference[];
};
```

```tsx
type RankingReferenceListProps = {
  references: RankingReference[];
};

export default function RankingReferenceList({ references }: RankingReferenceListProps) {
  if (references.length === 0) {
    return null;
  }

  return (
    <section className="panel">
      <h2 className="panel-title">{'\u53c2\u8003\u699c\u5355'}</h2>
      <div className="section-grid">
        {references.map((reference) => (
          <article
            key={`${reference.source}-${reference.year}-${reference.label}`}
            className="section-card"
          >
            <p>{`${reference.source} ${reference.year}`}</p>
            <strong>{reference.label}</strong>
            {reference.scope ? <p>{reference.scope}</p> : null}
            {reference.note ? <p>{reference.note}</p> : null}
            {reference.url ? (
              <a href={reference.url} target="_blank" rel="noreferrer">
                {'\u67e5\u770b\u6765\u6e90'}
              </a>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}
```

Render `<RankingReferenceList references={school.rankingReferences} />` after `PageSectionRenderer` in the school page and the equivalent for the major page.

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`

Expected: PASS with both detail pages correctly rendering or omitting the ranking section.

- [ ] **Step 5: Commit**

```bash
git add apps/web/components/public/ranking-reference-list.tsx apps/web/lib/public-content-api.ts apps/web/app/schools/[slug]/page.tsx apps/web/app/majors/[slug]/page.tsx apps/web/tests/public-pages.test.tsx
git commit -m "feat(web): render ranking references on detail pages"
```

### Task 3: Run full API and Web verification

**Files:**
- Test: `apps/api/tests/test_public_catalog_api.py`
- Test: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Run focused API verification**

Run: `python -m pytest tests/test_public_catalog_api.py -v`

Expected: PASS with detail endpoints returning ranking references.

- [ ] **Step 2: Run focused Web verification**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`

Expected: PASS with school and major ranking-reference rendering covered.

- [ ] **Step 3: Run full Web test suite**

Run: `node ./node_modules/vitest/vitest.mjs run`

Expected: PASS with all `apps/web` tests green.

- [ ] **Step 4: Run production build**

Run: `node ./node_modules/next/dist/bin/next build`

Expected: PASS with a successful Next.js production build. The known Windows SWC policy warning is acceptable if the build completes successfully via the wasm fallback.

- [ ] **Step 5: Run git status review**

Run: `git status --short`

Expected: clean working tree after the intended commits, or only the plan file before its own commit.

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/plans/2026-04-14-ranking-references.md
git commit -m "docs: add ranking references plan"
```
