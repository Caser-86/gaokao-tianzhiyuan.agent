# Featured Content Date Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only admin tool that previews the featured schools and majors for one selected date.

**Architecture:** Extend the existing admin featured-content payload so it accepts an optional `preview_date` query parameter and returns an optional `preview.selected_date` result plus a local validation message when the date is invalid. Then wire that payload into the existing server-rendered admin page with a date form and a selected-date preview block.

**Tech Stack:** FastAPI, Python, Next.js App Router, TypeScript, Vitest, Testing Library

---

### Task 1: Add API selected-date preview support

**Files:**
- Modify: `apps/api/tests/test_admin_api.py`
- Modify: `apps/api/app/services/featured_content.py`
- Modify: `apps/api/app/routers/admin.py`

- [ ] **Step 1: Write the failing API tests**

```python
def test_featured_content_endpoint_returns_selected_date_preview(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client

    response = client.get(
        "/api/admin/featured-content?preview_date=2026-04-15",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json()["preview"]["selected_date"] == {
        "date": "2026-04-15",
        "weekday": "周三",
        "schools": [
            {
                "slug": "west-china-medical-center",
                "name": "华西医学中心",
            }
        ],
        "majors": [
            {
                "slug": "computer-science",
                "name": "计算机科学与技术",
            }
        ],
    }
    assert response.json()["preview"]["selected_date_error"] is None


def test_featured_content_endpoint_returns_local_error_for_invalid_preview_date(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client

    response = client.get(
        "/api/admin/featured-content?preview_date=2026-99-99",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json()["preview"]["selected_date"] is None
    assert response.json()["preview"]["selected_date_error"] == "预览日期格式无效"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_admin_api.py::test_featured_content_endpoint_returns_selected_date_preview tests/test_admin_api.py::test_featured_content_endpoint_returns_local_error_for_invalid_preview_date -v`

Expected: FAIL because `selected_date` and `selected_date_error` are missing

- [ ] **Step 3: Write minimal service implementation**

```python
def build_featured_content_preview(
    *,
    preview_date: date | None = None,
) -> dict[str, Any]:
    payload = list_featured_content()
    today = date.today()
    today_entry = _preview_entry_for_date(payload, today)
    next_preview = { ... }
    schedule = [ ... ]
    selected_date_entry = (
        _preview_entry_for_date(payload, preview_date)
        if preview_date is not None
        else None
    )
    return {
        "today": {
            "schools": today_entry["schools"],
            "majors": today_entry["majors"],
        },
        "next": next_preview,
        "schedule": schedule,
        "selected_date": selected_date_entry,
        "selected_date_error": None,
    }
```

- [ ] **Step 4: Write minimal router parsing and response model**

```python
class FeaturedContentPreviewResponse(SQLModel):
    today: FeaturedTodayPreviewResponse
    next: FeaturedTodayPreviewResponse
    schedule: list[FeaturedPreviewDayResponse]
    selected_date: FeaturedPreviewDayResponse | None = None
    selected_date_error: str | None = None


@router.get("/featured-content", response_model=FeaturedContentResponse)
def get_featured_content(
    preview_date: str | None = Query(default=None),
    _authorized: None = Depends(require_admin),
) -> FeaturedContentResponse:
    selected_preview_date: date | None = None
    selected_date_error: str | None = None
    if preview_date:
        try:
            selected_preview_date = date.fromisoformat(preview_date)
        except ValueError:
            selected_date_error = "预览日期格式无效"

    preview = build_featured_content_preview(preview_date=selected_preview_date)
    preview["selected_date_error"] = selected_date_error
    ...
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_admin_api.py::test_featured_content_endpoint_returns_selected_date_preview tests/test_admin_api.py::test_featured_content_endpoint_returns_local_error_for_invalid_preview_date -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add apps/api/tests/test_admin_api.py apps/api/app/services/featured_content.py apps/api/app/routers/admin.py
git commit -m "feat(api): add featured content date preview"
```

### Task 2: Map selected-date preview in the web admin client

**Files:**
- Modify: `apps/web/tests/admin-review-api.test.ts`
- Modify: `apps/web/lib/admin-featured-content-api.ts`

- [ ] **Step 1: Write the failing client mapping test**

```ts
expect(payload.preview.selectedDate).toEqual({
  date: '2026-04-15',
  weekday: '周三',
  schools: [
    {
      slug: 'west-china-medical-center',
      name: '华西医学中心',
    },
  ],
  majors: [
    {
      slug: 'computer-science',
      name: '计算机科学与技术',
    },
  ],
});
expect(payload.preview.selectedDateError).toBeNull();
```

And invalid date case:

```ts
expect(payload.preview.selectedDate).toBeNull();
expect(payload.preview.selectedDateError).toBe('预览日期格式无效');
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node .\\node_modules\\vitest\\vitest.mjs run tests/admin-review-api.test.ts`

Expected: FAIL because `selectedDate` mapping is missing

- [ ] **Step 3: Write minimal implementation**

```ts
export type AdminFeaturedContent = {
  // ...
  preview: {
    today: { ... };
    next: { ... };
    schedule: AdminFeaturedPreviewDay[];
    selectedDate: AdminFeaturedPreviewDay | null;
    selectedDateError: string | null;
  };
};

selectedDate: payload.preview?.selected_date
  ? {
      date: payload.preview.selected_date.date,
      weekday: payload.preview.selected_date.weekday,
      schools: mapPreviewItems(payload.preview.selected_date.schools),
      majors: mapPreviewItems(payload.preview.selected_date.majors),
    }
  : null,
selectedDateError: payload.preview?.selected_date_error ?? null,
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node .\\node_modules\\vitest\\vitest.mjs run tests/admin-review-api.test.ts`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/tests/admin-review-api.test.ts apps/web/lib/admin-featured-content-api.ts
git commit -m "feat(web): map featured content date preview"
```

### Task 3: Render selected-date preview in the admin page

**Files:**
- Modify: `apps/web/tests/admin-page.test.tsx`
- Modify: `apps/web/tests/admin-dashboard.test.tsx`
- Modify: `apps/web/app/(admin)/admin/page.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`

- [ ] **Step 1: Write the failing UI tests**

```ts
render(await AdminPage({
  searchParams: Promise.resolve({ preview_date: '2026-04-15' }),
}));

expect(screen.getByRole('heading', { name: '指定日期预览' })).toBeInTheDocument();
expect(screen.getByDisplayValue('2026-04-15')).toBeInTheDocument();
expect(screen.getByRole('button', { name: '查看该日轮换' })).toBeInTheDocument();
expect(screen.getByRole('heading', { name: '该日展示学校' })).toBeInTheDocument();
expect(screen.getByRole('heading', { name: '该日展示专业' })).toBeInTheDocument();
expect(screen.getByText('west-china-medical-center')).toBeInTheDocument();
expect(screen.getByText('computer-science')).toBeInTheDocument();
```

And helper/error states:

```ts
expect(screen.getByText('选择一个日期查看当天轮换结果')).toBeInTheDocument();
expect(screen.getByText('预览日期格式无效')).toBeInTheDocument();
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node .\\node_modules\\vitest\\vitest.mjs run tests/admin-page.test.tsx tests/admin-dashboard.test.tsx`

Expected: FAIL because the date-preview form and selected-date block are missing

- [ ] **Step 3: Write minimal page and shell implementation**

In `apps/web/app/(admin)/admin/page.tsx`:

```ts
type AdminPageProps = {
  searchParams?: Promise<{
    preview_date?: string;
  }>;
};

export default async function AdminPage({ searchParams }: AdminPageProps = {}) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const previewDate = resolvedSearchParams.preview_date ?? '';
  // pass previewDate into listFeaturedContent(previewDate)
  // pass selectedDatePreview and selectedDateError into DashboardShell
}
```

In `apps/web/lib/admin-featured-content-api.ts`:

```ts
export async function listFeaturedContent(previewDate?: string): Promise<AdminFeaturedContent> {
  const query = previewDate
    ? `?preview_date=${encodeURIComponent(previewDate)}`
    : '';
  const response = await fetch(`${getApiUrl()}/api/admin/featured-content${query}`, {
    headers: buildHeaders(),
    cache: 'no-store',
  });
  // existing mapping
}
```

In `apps/web/components/admin/dashboard-shell.tsx`:

```tsx
<section aria-labelledby="selected-date-preview-heading">
  <h2 id="selected-date-preview-heading">指定日期预览</h2>
  <form action="/admin" method="GET">
    <input type="date" name="preview_date" defaultValue={selectedPreviewDateValue} />
    <button type="submit">查看该日轮换</button>
  </form>

  {!selectedPreviewDateValue && !selectedDatePreview && !selectedDateError ? (
    <p>选择一个日期查看当天轮换结果</p>
  ) : null}
  {selectedDateError ? <p>{selectedDateError}</p> : null}
  {selectedDatePreview ? (
    <>
      <h3>该日展示学校</h3>
      ...
      <h3>该日展示专业</h3>
      ...
    </>
  ) : null}
</section>
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node .\\node_modules\\vitest\\vitest.mjs run tests/admin-page.test.tsx tests/admin-dashboard.test.tsx`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/tests/admin-page.test.tsx apps/web/tests/admin-dashboard.test.tsx "apps/web/app/(admin)/admin/page.tsx" apps/web/components/admin/dashboard-shell.tsx apps/web/lib/admin-featured-content-api.ts
git commit -m "feat(web): show featured content date preview"
```

### Task 4: Full verification

**Files:**
- Modify: none

- [ ] **Step 1: Run API verification**

Run: `python -m pytest tests/test_admin_api.py -v`

Expected: PASS

- [ ] **Step 2: Run full web verification**

Run: `node .\\node_modules\\vitest\\vitest.mjs run`

Expected: PASS

- [ ] **Step 3: Run production build verification**

Run: `node .\\node_modules\\next\\dist\\bin\\next build`

Expected: PASS with the existing Windows SWC warning still acceptable because wasm fallback succeeds

- [ ] **Step 4: Commit if verification-driven fixes were needed**

```bash
git add .
git commit -m "fix: align featured content date preview verification"
```
