# Admin Related Content Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add admin APIs and admin page editing controls for school `related_majors` and major `related_schools`.

**Architecture:** Extend the existing catalog-backed admin editing pattern used for summaries, sections, and ranking references. API owns validation and persistence; Web admin adds one API client plus two simple multiline-slug forms.

**Tech Stack:** FastAPI, catalog JSON persistence, Next.js App Router, Vitest, Testing Library, pytest

---

### Task 1: Add admin related-content API

**Files:**
- Modify: `apps/api/app/services/catalog.py`
- Modify: `apps/api/app/routers/admin.py`
- Create: `apps/api/tests/test_admin_related_content_api.py`

- [ ] **Step 1: Write the failing API test**

```python
def test_related_content_endpoint_returns_school_and_major_entries(related_content_catalog_file):
    with TestClient(app) as client:
        response = client.get(
            "/api/admin/related-content",
            headers={"x-admin-token": settings.admin_token},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schools"][0]["related_majors"] == ["clinical-medicine"]
    assert payload["majors"][0]["related_schools"] == ["southeast-university"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_admin_related_content_api.py -v`

Expected: FAIL because the route does not exist yet

- [ ] **Step 3: Write minimal API implementation**

```python
def list_admin_related_content() -> dict[str, Any]:
    catalog = load_catalog()
    return {
        "schools": [
            {
                "slug": school["slug"],
                "name": school["name"],
                "related_majors": school.get("related_majors", []),
            }
            for school in catalog["schools"]
        ],
        "majors": [
            {
                "slug": major["slug"],
                "name": major["name"],
                "related_schools": major.get("related_schools", []),
            }
            for major in catalog["majors"]
        ],
    }
```

- [ ] **Step 4: Add update and validation behavior**

```python
def update_related_content(entity_key: str, slug: str, related_field: str, related_slugs: list[str]) -> dict[str, Any]:
    catalog = load_catalog()
    entries = catalog[entity_key]
    entity = next((item for item in entries if item["slug"] == slug), None)
    if entity is None:
        raise KeyError(slug)

    related_pool = {
        item["slug"]
        for item in catalog["majors" if related_field == "related_majors" else "schools"]
    }
    if any(related_slug not in related_pool for related_slug in related_slugs):
        raise ValueError("related content slug is invalid")

    entity[related_field] = related_slugs
    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    load_catalog.cache_clear()
    return {
        "slug": entity["slug"],
        "name": entity["name"],
        related_field: entity.get(related_field, []),
    }
```

- [ ] **Step 5: Run API test to verify it passes**

Run: `python -m pytest tests/test_admin_related_content_api.py -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add apps/api/app/services/catalog.py apps/api/app/routers/admin.py apps/api/tests/test_admin_related_content_api.py
git commit -m "feat(api): add admin related content endpoints"
```

### Task 2: Add web related-content client and actions

**Files:**
- Create: `apps/web/lib/admin-related-content-api.ts`
- Modify: `apps/web/app/(admin)/admin/actions.ts`
- Create: `apps/web/tests/admin-related-content-api.test.ts`

- [ ] **Step 1: Write the failing web client test**

```ts
import { describe, expect, test, vi } from 'vitest';

describe('listRelatedContent', () => {
  test('maps school and major related slug lists', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        schools: [{ slug: 'southeast-university', name: '东南大学', related_majors: ['clinical-medicine'] }],
        majors: [{ slug: 'clinical-medicine', name: '临床医学', related_schools: ['southeast-university'] }],
      }),
    }));
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-related-content-api.test.ts`

Expected: FAIL because the client module does not exist yet

- [ ] **Step 3: Write minimal web client and actions**

```ts
export async function listRelatedContent(): Promise<AdminRelatedContentList> {
  const payload = await requestAdminJson<AdminRelatedContentPayload>('/api/admin/related-content');
  return {
    schools: payload.schools.map((entity) => ({
      slug: entity.slug,
      name: entity.name,
      relatedMajors: entity.related_majors,
    })),
    majors: payload.majors.map((entity) => ({
      slug: entity.slug,
      name: entity.name,
      relatedSchools: entity.related_schools,
    })),
  };
}
```

- [ ] **Step 4: Add server actions**

```ts
export async function updateSchoolRelatedContentAction(formData: FormData): Promise<void> {
  const slug = parseRequiredSlug(formData.get('slug'));
  const relatedMajors = parseSlugLines(formData.get('relatedMajors'));
  await updateSchoolRelatedContent(slug, relatedMajors);
  revalidatePath('/admin');
  revalidatePath('/');
  revalidatePath(`/schools/${slug}`);
}
```

- [ ] **Step 5: Run web client test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-related-content-api.test.ts`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add apps/web/lib/admin-related-content-api.ts apps/web/app/(admin)/admin/actions.ts apps/web/tests/admin-related-content-api.test.ts
git commit -m "feat(web): add admin related content client"
```

### Task 3: Add admin related-content forms

**Files:**
- Modify: `apps/web/app/(admin)/admin/page.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`
- Create: `apps/web/tests/admin-related-content.test.tsx`
- Modify: `apps/web/tests/admin-page.test.tsx`

- [ ] **Step 1: Write the failing admin UI test**

```tsx
test('renders school and major related content editors', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[]}
      featuredMajors={[]}
      schoolRotation={defaultRotation}
      majorRotation={defaultRotation}
      featuredSchoolPreview={[]}
      featuredMajorPreview={[]}
      nextFeaturedSchoolPreview={[]}
      nextFeaturedMajorPreview={[]}
      featuredSchedule={[]}
      selectedPreviewDateValue=""
      selectedDatePreview={null}
      relatedSchools={[{ slug: 'southeast-university', name: '东南大学', relatedMajors: ['clinical-medicine'] }]}
      relatedMajors={[{ slug: 'clinical-medicine', name: '临床医学', relatedSchools: ['southeast-university'] }]}
      approveAction={async () => {}}
      rejectAction={async () => {}}
      updateFeaturedSchoolAction={async () => {}}
      updateFeaturedMajorAction={async () => {}}
      updateSchoolRotationAction={async () => {}}
      updateMajorRotationAction={async () => {}}
    />
  );

  expect(screen.getByText('学校相关推荐')).toBeInTheDocument();
  expect(screen.getByText('专业相关推荐')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-related-content.test.tsx`

Expected: FAIL because the related-content UI does not exist yet

- [ ] **Step 3: Write minimal admin page integration**

```tsx
const relatedContent = await listRelatedContent();
relatedSchools = relatedContent.schools;
relatedMajors = relatedContent.majors;
```

- [ ] **Step 4: Add dashboard forms**

```tsx
function RelatedContentForm({ entity, mode, action }: Props) {
  return (
    <form action={action}>
      <input type="hidden" name="slug" value={entity.slug} />
      <textarea
        name={mode === 'school' ? 'relatedMajors' : 'relatedSchools'}
        defaultValue={(mode === 'school' ? entity.relatedMajors : entity.relatedSchools).join('\n')}
      />
      <button type="submit">保存相关推荐</button>
    </form>
  );
}
```

- [ ] **Step 5: Run focused admin tests to verify they pass**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-related-content.test.tsx tests/admin-page.test.tsx`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add apps/web/app/(admin)/admin/page.tsx apps/web/components/admin/dashboard-shell.tsx apps/web/tests/admin-related-content.test.tsx apps/web/tests/admin-page.test.tsx
git commit -m "feat(web): edit related content in admin"
```

### Task 4: Full verification

**Files:**
- Modify: `apps/web/tests/admin-content-summary.test.tsx`
- Modify: `apps/web/tests/admin-ranking-reference.test.tsx`
- Modify: `apps/web/tests/admin-content-sections.test.tsx`
- Modify: any other admin test files that need the new list/action mocks

- [ ] **Step 1: Run full API suite**

Run: `python -m pytest`

Expected: PASS

- [ ] **Step 2: Run full web suite**

Run: `node ./node_modules/vitest/vitest.mjs run`

Expected: PASS

- [ ] **Step 3: Run production build**

Run: `node ./node_modules/next/dist/bin/next build`

Expected: Build succeeds

- [ ] **Step 4: Commit verification-related test updates**

```bash
git add apps/web/tests
git commit -m "test(web): cover admin related content flow"
```
