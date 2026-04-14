# Ranking Reference Admin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add minimal admin read/write support for school and major ranking references so operators can maintain `ranking_references` without editing `data/catalog.json` manually.

**Architecture:** Extend the existing admin API with ranking-reference endpoints backed by `catalog.json`, then add a lightweight admin section and server actions in the existing `/admin` page. Keep the first version simple: edit existing rows and submit one extra blank row for appending.

**Tech Stack:** FastAPI, SQLModel response models, Next.js App Router, server actions, Vitest, pytest

---

### Task 1: Add Failing API Tests For Ranking Reference Admin Routes

**Files:**
- Modify: `apps/api/tests/test_admin_api.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_ranking_reference_endpoint_returns_school_and_major_entries(admin_client):
    client, _engine = admin_client

    response = client.get(
        "/api/admin/ranking-references",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    payload = response.json()
    assert any(item["slug"] == "southeast-university" for item in payload["schools"])
    assert any(item["slug"] == "clinical-medicine" for item in payload["majors"])


def test_update_school_ranking_references(admin_client):
    client, _engine = admin_client

    response = client.post(
        "/api/admin/ranking-references/schools/southeast-university",
        headers={"x-admin-token": settings.admin_token},
        json={
            "ranking_references": [
                {
                    "source": "软科中国大学排名",
                    "year": 2026,
                    "label": "全国第 12 名",
                    "scope": "综合类高校",
                    "note": "更新后的榜单备注",
                    "url": "https://example.com/new-ranking",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["slug"] == "southeast-university"
    assert payload["ranking_references"][0]["year"] == 2026


def test_update_major_ranking_references_rejects_invalid_year(admin_client):
    client, _engine = admin_client

    response = client.post(
        "/api/admin/ranking-references/majors/clinical-medicine",
        headers={"x-admin-token": settings.admin_token},
        json={
            "ranking_references": [
                {
                    "source": "教育部学科评估",
                    "year": 0,
                    "label": "A-",
                    "scope": "一级学科",
                    "note": "",
                    "url": "",
                }
            ]
        },
    )

    assert response.status_code == 422
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_admin_api.py -v`
Expected: FAIL because the admin ranking reference route does not exist yet

- [ ] **Step 3: Commit the failing test snapshot**

```bash
git add apps/api/tests/test_admin_api.py
git commit -m "test(api): cover ranking reference admin endpoints"
```

### Task 2: Implement API Ranking Reference Read/Write Support

**Files:**
- Modify: `apps/api/app/services/catalog.py`
- Modify: `apps/api/app/routers/admin.py`
- Modify: `apps/api/tests/test_admin_api.py`

- [ ] **Step 1: Add catalog service helpers**

```python
def list_admin_ranking_references() -> dict[str, Any]:
    catalog = load_catalog()
    return {
        "schools": [
            {
                "slug": school["slug"],
                "name": school["name"],
                "ranking_references": school.get("ranking_references", []),
            }
            for school in catalog["schools"]
        ],
        "majors": [
            {
                "slug": major["slug"],
                "name": major["name"],
                "ranking_references": major.get("ranking_references", []),
            }
            for major in catalog["majors"]
        ],
    }


def update_ranking_references(entity_key: str, slug: str, ranking_references: list[dict[str, Any]]) -> dict[str, Any]:
    catalog = load_catalog()
    entries = catalog[entity_key]
    entity = next((item for item in entries if item["slug"] == slug), None)
    if entity is None:
        raise KeyError(slug)

    entity["ranking_references"] = ranking_references
    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    load_catalog.cache_clear()
    return {
        "slug": entity["slug"],
        "name": entity["name"],
        "ranking_references": entity.get("ranking_references", []),
    }
```

- [ ] **Step 2: Add admin router models and endpoints**

```python
class RankingReferenceResponse(SQLModel):
    source: str
    year: int
    label: str
    scope: str = ""
    note: str = ""
    url: str = ""


class RankingReferenceEntityResponse(SQLModel):
    slug: str
    name: str
    ranking_references: list[RankingReferenceResponse]


class RankingReferenceListResponse(SQLModel):
    schools: list[RankingReferenceEntityResponse]
    majors: list[RankingReferenceEntityResponse]


class RankingReferenceRequest(SQLModel):
    source: str
    year: int
    label: str
    scope: str = ""
    note: str = ""
    url: str = ""


class RankingReferenceUpdateRequest(SQLModel):
    ranking_references: list[RankingReferenceRequest]


@router.get("/ranking-references", response_model=RankingReferenceListResponse)
def get_ranking_references(
    _authorized: None = Depends(require_admin),
) -> RankingReferenceListResponse:
    payload = list_admin_ranking_references()
    return RankingReferenceListResponse(
        schools=[RankingReferenceEntityResponse(**item) for item in payload["schools"]],
        majors=[RankingReferenceEntityResponse(**item) for item in payload["majors"]],
    )
```
Add matching `POST` endpoints for `/ranking-references/schools/{slug}` and `/ranking-references/majors/{slug}` that validate `source`, `label`, and `year >= 1`, then call `update_ranking_references(...)`.

- [ ] **Step 3: Run test to verify it passes**

Run: `python -m pytest tests/test_admin_api.py -v`
Expected: PASS for the new ranking reference admin tests and no regression in existing admin tests

- [ ] **Step 4: Commit**

```bash
git add apps/api/app/services/catalog.py apps/api/app/routers/admin.py apps/api/tests/test_admin_api.py
git commit -m "feat(api): add ranking reference admin endpoints"
```

### Task 3: Add Failing Web Tests For Ranking Reference Admin UI

**Files:**
- Modify: `apps/web/tests/admin-page.test.tsx`

- [ ] **Step 1: Write the failing tests**

```tsx
test('renders school and major ranking reference admin sections', async () => {
  listFeaturedContentMock.mockResolvedValue(mockFeaturedContent);
  listRankingReferencesMock.mockResolvedValue({
    schools: [
      {
        slug: 'southeast-university',
        name: '东南大学',
        rankingReferences: [
          {
            source: '软科中国大学排名',
            year: 2025,
            label: '全国第 15 名',
            scope: '综合类高校',
            note: '用于综合实力参考',
            url: 'https://example.com/rankings/southeast-university',
          },
        ],
      },
    ],
    majors: [],
  });

  render(await AdminPage({}));

  expect(screen.getByRole('heading', { name: '学校榜单引用' })).toBeInTheDocument();
  expect(screen.getByDisplayValue('软科中国大学排名')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '专业榜单引用' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-page.test.tsx`
Expected: FAIL because the ranking reference admin section and API client do not exist yet

- [ ] **Step 3: Commit the failing test snapshot**

```bash
git add apps/web/tests/admin-page.test.tsx
git commit -m "test(web): cover ranking reference admin UI"
```

### Task 4: Implement Web Ranking Reference Admin Client And Actions

**Files:**
- Create: `apps/web/lib/admin-ranking-reference-api.ts`
- Modify: `apps/web/app/(admin)/admin/actions.ts`
- Modify: `apps/web/app/(admin)/admin/page.tsx`

- [ ] **Step 1: Add the admin ranking reference API client**

```ts
export type AdminRankingReference = {
  source: string;
  year: number;
  label: string;
  scope: string;
  note: string;
  url: string;
};

export type AdminRankingReferenceEntity = {
  slug: string;
  name: string;
  rankingReferences: AdminRankingReference[];
};

export async function listRankingReferences(): Promise<{
  schools: AdminRankingReferenceEntity[];
  majors: AdminRankingReferenceEntity[];
}> {
  const response = await fetch(`${getApiUrl()}/api/admin/ranking-references`, {
    headers: buildHeaders(),
    cache: 'no-store',
  });
  const payload = await parseResponse<{
    schools: Array<{
      slug: string;
      name: string;
      ranking_references: AdminRankingReference[];
    }>;
    majors: Array<{
      slug: string;
      name: string;
      ranking_references: AdminRankingReference[];
    }>;
  }>(response);

  return {
    schools: payload.schools.map((item) => ({
      slug: item.slug,
      name: item.name,
      rankingReferences: item.ranking_references,
    })),
    majors: payload.majors.map((item) => ({
      slug: item.slug,
      name: item.name,
      rankingReferences: item.ranking_references,
    })),
  };
}
```

- [ ] **Step 2: Add server actions for school and major ranking references**

```ts
const parseRankingReferences = (formData: FormData): AdminRankingReference[] => {
  const rows = Number.parseInt(String(formData.get('rowCount') ?? '0'), 10);
  const items: AdminRankingReference[] = [];

  for (let index = 0; index < rows; index += 1) {
    const source = String(formData.get(`source_${index}`) ?? '').trim();
    const yearRaw = String(formData.get(`year_${index}`) ?? '').trim();
    const label = String(formData.get(`label_${index}`) ?? '').trim();
    const scope = String(formData.get(`scope_${index}`) ?? '').trim();
    const note = String(formData.get(`note_${index}`) ?? '').trim();
    const url = String(formData.get(`url_${index}`) ?? '').trim();

    if (!source && !yearRaw && !label && !scope && !note && !url) {
      continue;
    }

    items.push({
      source,
      year: Number.parseInt(yearRaw, 10),
      label,
      scope,
      note,
      url,
    });
  }

  return items;
};
```
Then add `updateSchoolRankingReferencesAction` and `updateMajorRankingReferencesAction` that call the new API client and `revalidatePath('/admin')`.

- [ ] **Step 3: Thread ranking reference data into the admin page**

```ts
let rankingReferenceSchools = [];
let rankingReferenceMajors = [];
let rankingReferenceError: string | undefined;

try {
  const rankingReferences = await listRankingReferences();
  rankingReferenceSchools = rankingReferences.schools;
  rankingReferenceMajors = rankingReferences.majors;
} catch {
  rankingReferenceError = '榜单引用加载失败，请稍后重试';
}
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/lib/admin-ranking-reference-api.ts apps/web/app/(admin)/admin/actions.ts apps/web/app/(admin)/admin/page.tsx
git commit -m "feat(web): add ranking reference admin data layer"
```

### Task 5: Render Ranking Reference Admin Forms In DashboardShell

**Files:**
- Modify: `apps/web/components/admin/dashboard-shell.tsx`
- Modify: `apps/web/tests/admin-page.test.tsx`

- [ ] **Step 1: Add the ranking reference UI**

```tsx
<section aria-labelledby="school-ranking-references-heading">
  <h2 id="school-ranking-references-heading">学校榜单引用</h2>
  {rankingReferenceSchools.map((school) => (
    <form key={school.slug} action={updateSchoolRankingReferencesAction}>
      <input type="hidden" name="slug" value={school.slug} />
      <input type="hidden" name="rowCount" value={school.rankingReferences.length + 1} />
      <h3>{school.name}</h3>
      {[...school.rankingReferences, emptyRankingReference].map((item, index) => (
        <div key={`${school.slug}-${index}`}>
          <input name={`source_${index}`} defaultValue={item.source} />
          <input name={`year_${index}`} defaultValue={item.year ? String(item.year) : ''} />
          <input name={`label_${index}`} defaultValue={item.label} />
          <input name={`scope_${index}`} defaultValue={item.scope} />
          <input name={`note_${index}`} defaultValue={item.note} />
          <input name={`url_${index}`} defaultValue={item.url} />
        </div>
      ))}
      <button type="submit">保存学校榜单</button>
    </form>
  ))}
</section>
```
Mirror the same pattern for major ranking references.

- [ ] **Step 2: Run test to verify it passes**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-page.test.tsx`
Expected: PASS with the new ranking reference admin UI rendered

- [ ] **Step 3: Commit**

```bash
git add apps/web/components/admin/dashboard-shell.tsx apps/web/tests/admin-page.test.tsx
git commit -m "feat(web): render ranking reference admin forms"
```

### Task 6: Final Verification

**Files:**
- Verify only

- [ ] **Step 1: Run API verification**

Run: `python -m pytest tests/test_admin_api.py -v`
Expected: PASS

- [ ] **Step 2: Run Web verification**

Run: `node .\node_modules\vitest\vitest.mjs run`
Expected: PASS

- [ ] **Step 3: Run production build verification**

Run: `node .\node_modules\next\dist\bin\next build`
Expected: PASS

- [ ] **Step 4: Commit final touch-ups if needed**

```bash
git status --short
```
Expected: clean or only intended follow-up changes
