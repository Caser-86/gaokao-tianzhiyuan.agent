# Featured Content Next Rotation Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only admin preview for the next featured-school and featured-major rotation result.

**Architecture:** Extend the existing admin featured-content payload so `preview` includes a `next` block computed from the same API-side rotation helpers as today and seven-day schedule. Then map that nested shape in the web admin client and render two lightweight next-preview sections in the existing admin dashboard.

**Tech Stack:** FastAPI, Python, Next.js App Router, TypeScript, Vitest, Testing Library

---

### Task 1: Add API next-preview payload

**Files:**
- Modify: `apps/api/tests/test_admin_api.py`
- Modify: `apps/api/app/services/featured_content.py`
- Modify: `apps/api/app/routers/admin.py`

- [ ] **Step 1: Write the failing API test**

```python
def test_featured_content_endpoint_returns_next_preview(client: TestClient) -> None:
    response = client.get(
        "/api/admin/featured-content",
        headers={"x-admin-token": "dev-admin-token"},
    )

    assert response.status_code == 200
    preview = response.json()["preview"]
    assert preview["next"]["schools"] == [
        {
            "slug": "west-china-medical-center",
            "name": "华西医学中心",
        }
    ]
    assert preview["next"]["majors"] == [
        {
            "slug": "computer-science",
            "name": "计算机科学与技术",
        }
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_admin_api.py::test_featured_content_endpoint_returns_next_preview -v`

Expected: FAIL with `KeyError: 'next'`

- [ ] **Step 3: Write minimal implementation**

```python
def _next_preview_items(
    entries: list[dict[str, Any]],
    rule: dict[str, Any],
    *,
    today: date,
) -> list[dict[str, str]]:
    if not rule.get("enabled") or not rule.get("ordered_slugs"):
        return _preview_items(_current_rotation_window(entries, rule, today=today))

    next_date = today + timedelta(days=int(rule.get("frequency_days", 1) or 1))
    return _preview_items(_current_rotation_window(entries, rule, today=next_date))


def build_featured_content_preview() -> dict[str, Any]:
    payload = list_featured_content()
    today = date.today()
    today_entry = _preview_entry_for_date(payload, today)
    next_preview = {
        "schools": _next_preview_items(payload["schools"], payload["rotation"]["schools"], today=today),
        "majors": _next_preview_items(payload["majors"], payload["rotation"]["majors"], today=today),
    }
    schedule = [
        _preview_entry_for_date(payload, today + timedelta(days=offset))
        for offset in range(7)
    ]
    return {
        "today": {
            "schools": today_entry["schools"],
            "majors": today_entry["majors"],
        },
        "next": next_preview,
        "schedule": schedule,
    }
```

- [ ] **Step 4: Update router response model**

```python
class FeaturedTodayPreviewResponse(BaseModel):
    schools: list[FeaturedPreviewItemResponse]
    majors: list[FeaturedPreviewItemResponse]


class FeaturedContentPreviewResponse(BaseModel):
    today: FeaturedTodayPreviewResponse
    next: FeaturedTodayPreviewResponse
    schedule: list[FeaturedPreviewDayResponse]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_admin_api.py::test_featured_content_endpoint_returns_next_preview -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add apps/api/tests/test_admin_api.py apps/api/app/services/featured_content.py apps/api/app/routers/admin.py
git commit -m "feat(api): add featured content next preview"
```

### Task 2: Map next-preview in the web admin client

**Files:**
- Modify: `apps/web/tests/admin-review-api.test.ts`
- Modify: `apps/web/lib/admin-featured-content-api.ts`

- [ ] **Step 1: Write the failing web client test**

```ts
expect(payload.preview.next).toEqual({
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node .\\node_modules\\vitest\\vitest.mjs run tests/admin-review-api.test.ts`

Expected: FAIL because `payload.preview.next` is missing

- [ ] **Step 3: Write minimal implementation**

```ts
export type AdminFeaturedContent = {
  // ...
  preview: {
    today: {
      schools: AdminFeaturedPreviewItem[];
      majors: AdminFeaturedPreviewItem[];
    };
    next: {
      schools: AdminFeaturedPreviewItem[];
      majors: AdminFeaturedPreviewItem[];
    };
    schedule: AdminFeaturedPreviewDay[];
  };
};

preview: {
  today: {
    schools: mapPreviewItems(payload.preview?.today?.schools),
    majors: mapPreviewItems(payload.preview?.today?.majors),
  },
  next: {
    schools: mapPreviewItems(payload.preview?.next?.schools),
    majors: mapPreviewItems(payload.preview?.next?.majors),
  },
  schedule: payload.preview?.schedule?.map(/* existing mapping */) ?? [],
},
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node .\\node_modules\\vitest\\vitest.mjs run tests/admin-review-api.test.ts`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/tests/admin-review-api.test.ts apps/web/lib/admin-featured-content-api.ts
git commit -m "feat(web): map featured content next preview"
```

### Task 3: Render next-preview blocks in the admin page

**Files:**
- Modify: `apps/web/tests/admin-page.test.tsx`
- Modify: `apps/web/tests/admin-dashboard.test.tsx`
- Modify: `apps/web/app/(admin)/admin/page.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`

- [ ] **Step 1: Write the failing UI tests**

```ts
expect(screen.getByRole('heading', { name: '下一轮展示学校' })).toBeInTheDocument();
expect(screen.getByRole('heading', { name: '下一轮展示专业' })).toBeInTheDocument();
expect(screen.getByText('west-china-medical-center')).toBeInTheDocument();
expect(screen.getByText('computer-science')).toBeInTheDocument();
```

And for empty state:

```ts
expect(screen.getByText('当前没有下一轮展示学校')).toBeInTheDocument();
expect(screen.getByText('当前没有下一轮展示专业')).toBeInTheDocument();
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node .\\node_modules\\vitest\\vitest.mjs run tests/admin-page.test.tsx tests/admin-dashboard.test.tsx`

Expected: FAIL because the new sections are not rendered yet

- [ ] **Step 3: Write minimal implementation**

In `apps/web/app/(admin)/admin/page.tsx`:

```ts
let nextFeaturedSchoolPreview: AdminFeaturedPreviewItem[] = [];
let nextFeaturedMajorPreview: AdminFeaturedPreviewItem[] = [];

// after listFeaturedContent():
nextFeaturedSchoolPreview = featuredContent.preview.next.schools;
nextFeaturedMajorPreview = featuredContent.preview.next.majors;
```

Pass new props into `DashboardShell`:

```tsx
nextFeaturedSchoolPreview={nextFeaturedSchoolPreview}
nextFeaturedMajorPreview={nextFeaturedMajorPreview}
```

In `apps/web/components/admin/dashboard-shell.tsx`:

```tsx
<section aria-labelledby="next-featured-school-preview-heading">
  <h2 id="next-featured-school-preview-heading">下一轮展示学校</h2>
  {featuredContentError ? null : nextFeaturedSchoolPreview.length === 0 ? (
    <p>当前没有下一轮展示学校</p>
  ) : (
    <ul>
      {nextFeaturedSchoolPreview.map((school) => (
        <li key={school.slug}>
          <span>{school.name}</span>
          <span>{school.slug}</span>
        </li>
      ))}
    </ul>
  )}
</section>

<section aria-labelledby="next-featured-major-preview-heading">
  <h2 id="next-featured-major-preview-heading">下一轮展示专业</h2>
  {featuredContentError ? null : nextFeaturedMajorPreview.length === 0 ? (
    <p>当前没有下一轮展示专业</p>
  ) : (
    <ul>
      {nextFeaturedMajorPreview.map((major) => (
        <li key={major.slug}>
          <span>{major.name}</span>
          <span>{major.slug}</span>
        </li>
      ))}
    </ul>
  )}
</section>
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node .\\node_modules\\vitest\\vitest.mjs run tests/admin-page.test.tsx tests/admin-dashboard.test.tsx`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/tests/admin-page.test.tsx apps/web/tests/admin-dashboard.test.tsx "apps/web/app/(admin)/admin/page.tsx" apps/web/components/admin/dashboard-shell.tsx
git commit -m "feat(web): show featured content next preview"
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
git commit -m "fix: align featured content next preview verification"
```
