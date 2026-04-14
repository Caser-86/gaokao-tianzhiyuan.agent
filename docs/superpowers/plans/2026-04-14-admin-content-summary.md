# Admin Content Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add admin APIs and admin UI to edit school and major summaries without hand-editing `data/catalog.json`.

**Architecture:** Reuse the existing catalog-file-backed admin pattern. Add summary-specific read/write helpers in the API, then connect a small admin data client, server actions, and two summary editor sections in the existing admin dashboard.

**Tech Stack:** FastAPI, SQLModel, Next.js App Router, Vitest, Testing Library

---

### Task 1: Add Summary Admin API

**Files:**
- Modify: `apps/api/app/services/catalog.py`
- Modify: `apps/api/app/routers/admin.py`
- Create: `apps/api/tests/test_admin_content_summary_api.py`

- [ ] **Step 1: Write the failing API tests**

```python
def test_content_summary_endpoint_returns_school_and_major_entries(summary_catalog_file):
    with TestClient(app) as client:
        response = client.get(
            "/api/admin/content-summaries",
            headers={"x-admin-token": settings.admin_token},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schools"][0]["summary"] == "测试学校摘要"
    assert payload["majors"][0]["summary"] == "测试专业摘要"


def test_update_school_summary(summary_catalog_file):
    with TestClient(app) as client:
        response = client.post(
            "/api/admin/content-summaries/schools/southeast-university",
            headers={"x-admin-token": settings.admin_token},
            json={"summary": "更新后的学校摘要"},
        )

    assert response.status_code == 200
    assert response.json()["summary"] == "更新后的学校摘要"


def test_update_major_summary_rejects_blank_summary(summary_catalog_file):
    with TestClient(app) as client:
        response = client.post(
            "/api/admin/content-summaries/majors/clinical-medicine",
            headers={"x-admin-token": settings.admin_token},
            json={"summary": "   "},
        )

    assert response.status_code == 422
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_admin_content_summary_api.py -v`
Expected: FAIL because the routes and catalog helpers do not exist yet

- [ ] **Step 3: Write minimal API implementation**

```python
def list_admin_content_summaries() -> dict[str, Any]:
    catalog = load_catalog()
    return {
        "schools": [
            {"slug": school["slug"], "name": school["name"], "summary": school["summary"]}
            for school in catalog["schools"]
        ],
        "majors": [
            {"slug": major["slug"], "name": major["name"], "summary": major["summary"]}
            for major in catalog["majors"]
        ],
    }


def update_content_summary(entity_key: str, slug: str, summary: str) -> dict[str, Any]:
    normalized = summary.strip()
    if not normalized:
        raise ValueError("summary is required")
    ...
```

```python
class ContentSummaryEntityResponse(SQLModel):
    slug: str
    name: str
    summary: str


class ContentSummaryListResponse(SQLModel):
    schools: list[ContentSummaryEntityResponse]
    majors: list[ContentSummaryEntityResponse]


class ContentSummaryUpdateRequest(SQLModel):
    summary: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_admin_content_summary_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/services/catalog.py apps/api/app/routers/admin.py apps/api/tests/test_admin_content_summary_api.py
git commit -m "feat(api): add admin content summary endpoints"
```

### Task 2: Add Web Summary Admin Client and UI

**Files:**
- Create: `apps/web/lib/admin-content-summary-api.ts`
- Modify: `apps/web/app/(admin)/admin/actions.ts`
- Modify: `apps/web/app/(admin)/admin/page.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`
- Create: `apps/web/tests/admin-content-summary.test.tsx`
- Modify: `apps/web/tests/admin-page.test.tsx`

- [ ] **Step 1: Write the failing Web test**

```tsx
test('renders school and major summary editors in admin', async () => {
  listContentSummariesMock.mockResolvedValue({
    schools: [{ slug: 'southeast-university', name: '东南大学', summary: '学校摘要' }],
    majors: [{ slug: 'clinical-medicine', name: '临床医学', summary: '专业摘要' }],
  });

  render(await AdminPage({}));

  expect(screen.getByRole('heading', { name: '学校摘要编辑' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '专业摘要编辑' })).toBeInTheDocument();
  expect(screen.getByDisplayValue('学校摘要')).toBeInTheDocument();
  expect(screen.getByDisplayValue('专业摘要')).toBeInTheDocument();
  expect(screen.getAllByRole('button', { name: '保存摘要' })).toHaveLength(2);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-content-summary.test.tsx`
Expected: FAIL because summary admin UI and API client do not exist yet

- [ ] **Step 3: Write minimal Web implementation**

```ts
export type AdminContentSummaryEntity = {
  slug: string;
  name: string;
  summary: string;
};

export async function listContentSummaries(): Promise<{
  schools: AdminContentSummaryEntity[];
  majors: AdminContentSummaryEntity[];
}> {
  ...
}
```

```ts
export async function updateSchoolSummaryAction(formData: FormData): Promise<void> {
  const slug = parseRequiredSlug(formData.get('slug'));
  const summary = String(formData.get('summary') ?? '');
  await updateSchoolSummary(slug, summary);
  revalidatePath('/admin');
  revalidatePath('/');
  revalidatePath(`/schools/${slug}`);
}
```

```tsx
<section aria-labelledby="school-summary-heading">
  <h2 id="school-summary-heading">学校摘要编辑</h2>
  {summarySchools.map((school) => (
    <form key={school.slug} action={updateSchoolSummaryAction}>
      <input type="hidden" name="slug" value={school.slug} />
      <h3>{school.name}</h3>
      <p>{school.slug}</p>
      <textarea name="summary" defaultValue={school.summary} />
      <button type="submit">保存摘要</button>
    </form>
  ))}
</section>
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-content-summary.test.tsx tests/admin-page.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/lib/admin-content-summary-api.ts apps/web/app/(admin)/admin/actions.ts apps/web/app/(admin)/admin/page.tsx apps/web/components/admin/dashboard-shell.tsx apps/web/tests/admin-content-summary.test.tsx apps/web/tests/admin-page.test.tsx
git commit -m "feat(web): edit content summaries in admin"
```

### Task 3: Full Verification

**Files:**
- Verify only

- [ ] **Step 1: Run API test suite**

Run: `python -m pytest`
Expected: PASS

- [ ] **Step 2: Run Web test suite**

Run: `node .\node_modules\vitest\vitest.mjs run`
Expected: PASS

- [ ] **Step 3: Run production build**

Run: `node .\node_modules\next\dist\bin\next build`
Expected: PASS with the known Windows SWC policy warning only

- [ ] **Step 4: Commit follow-up fixes if needed**

```bash
git add -A
git commit -m "fix: stabilize admin content summary editing"
```
