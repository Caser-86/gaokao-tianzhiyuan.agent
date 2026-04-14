# Featured Content Admin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add admin-managed featured schools and majors so the homepage only shows curated entities, and let admins maintain a manual image URL for featured school cards.

**Architecture:** Introduce a dedicated `data/featured-content.json` configuration file and a small API service for reading and updating it. Extend the admin API and admin web shell to edit one row at a time, then update the public list endpoints and homepage rendering so featured-content configuration controls which entities appear and which school cards show a photo.

**Tech Stack:** FastAPI, Python, SQLModel, Next.js 15, React 19, TypeScript, Vitest, Testing Library, Pytest

---

### Task 1: Add featured-content storage and admin API coverage

**Files:**
- Create: `data/featured-content.json`
- Create: `apps/api/app/services/featured_content.py`
- Modify: `apps/api/app/routers/admin.py`
- Modify: `apps/api/tests/test_admin_api.py`

- [ ] **Step 1: Write the failing test**

Extend `apps/api/tests/test_admin_api.py` so it covers reading featured-content config and updating one school or major entry at a time.

```python
def test_featured_content_endpoint_returns_school_and_major_configuration(admin_client) -> None:
    client, _engine = admin_client

    response = client.get(
        "/api/admin/featured-content",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schools"][0]["slug"] == "southeast-university"
    assert payload["schools"][0]["is_featured"] is True
    assert "hero_image_url" in payload["schools"][0]
    assert payload["majors"][0]["slug"] == "clinical-medicine"
```

```python
def test_update_featured_school_persists_is_featured_and_image_url(admin_client) -> None:
    client, _engine = admin_client

    response = client.post(
        "/api/admin/featured-content/schools/southeast-university",
        headers={"x-admin-token": settings.admin_token},
        json={
            "is_featured": False,
            "hero_image_url": "https://cdn.example.com/southeast.jpg",
        },
    )

    assert response.status_code == 200
    assert response.json()["is_featured"] is False
    assert response.json()["hero_image_url"] == "https://cdn.example.com/southeast.jpg"
```

```python
def test_update_featured_major_rejects_unknown_slug(admin_client) -> None:
    client, _engine = admin_client

    response = client.post(
        "/api/admin/featured-content/majors/missing-major",
        headers={"x-admin-token": settings.admin_token},
        json={"is_featured": True},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "featured content entity not found"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_admin_api.py -v`

Expected: FAIL because the admin router does not yet expose featured-content endpoints.

- [ ] **Step 3: Write minimal implementation**

Create `data/featured-content.json` and a dedicated service for loading, validating, and updating featured-content entries.

```json
{
  "schools": [
    {
      "slug": "southeast-university",
      "is_featured": true,
      "hero_image_url": ""
    },
    {
      "slug": "west-china-medical-center",
      "is_featured": true,
      "hero_image_url": ""
    }
  ],
  "majors": [
    {
      "slug": "clinical-medicine",
      "is_featured": true
    },
    {
      "slug": "computer-science",
      "is_featured": true
    }
  ]
}
```

```python
FEATURED_CONTENT_PATH = Path(__file__).resolve().parents[4] / "data" / "featured-content.json"

def load_featured_content() -> dict[str, Any]:
    return json.loads(FEATURED_CONTENT_PATH.read_text(encoding="utf-8"))

def update_featured_school(slug: str, *, is_featured: bool, hero_image_url: str | None) -> dict[str, Any]:
    payload = load_featured_content()
    entry = next((item for item in payload["schools"] if item["slug"] == slug), None)
    if entry is None:
        raise KeyError(slug)
    entry["is_featured"] = is_featured
    entry["hero_image_url"] = (hero_image_url or "").strip()
    FEATURED_CONTENT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return entry
```

Add new admin router models and handlers in `apps/api/app/routers/admin.py`.

```python
class FeaturedSchoolConfigResponse(SQLModel):
    slug: str
    is_featured: bool
    hero_image_url: str | None = None


class FeaturedMajorConfigResponse(SQLModel):
    slug: str
    is_featured: bool


@router.get("/featured-content")
def get_featured_content(
    _authorized: None = Depends(require_admin),
) -> FeaturedContentResponse:
    payload = read_featured_content_response()
    return FeaturedContentResponse(**payload)
```

```python
@router.post("/featured-content/schools/{slug}", response_model=FeaturedSchoolConfigResponse)
def update_featured_school_config(
    slug: str,
    payload: FeaturedSchoolConfigRequest,
    _authorized: None = Depends(require_admin),
) -> FeaturedSchoolConfigResponse:
    try:
        return FeaturedSchoolConfigResponse(
            **update_featured_school(
                slug,
                is_featured=payload.is_featured,
                hero_image_url=payload.hero_image_url,
            )
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="featured content entity not found") from exc
```

Apply the same one-row update pattern to majors.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_admin_api.py -v`

Expected: PASS with featured-content reads and updates working behind existing admin auth.

- [ ] **Step 5: Commit**

```bash
git add data/featured-content.json apps/api/app/services/featured_content.py apps/api/app/routers/admin.py apps/api/tests/test_admin_api.py
git commit -m "feat(api): add featured content admin endpoints"
```

### Task 2: Filter public list responses by featured-content configuration

**Files:**
- Modify: `apps/api/app/services/catalog.py`
- Modify: `apps/api/tests/test_public_catalog_api.py`

- [ ] **Step 1: Write the failing test**

Extend `apps/api/tests/test_public_catalog_api.py` so list endpoints only return featured entities and school cards expose `hero_image_url`.

```python
def test_list_schools_only_returns_featured_items() -> None:
    response = client.get("/api/public/schools")

    assert response.status_code == 200
    payload = response.json()
    assert all(item["slug"] != "architecture-demo-school" for item in payload["items"])
    assert payload["items"][0]["hero_image_url"] == ""
```

```python
def test_list_majors_only_returns_featured_items() -> None:
    response = client.get("/api/public/majors")

    payload = response.json()
    assert {item["slug"] for item in payload["items"]} == {
        "clinical-medicine",
        "computer-science",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_public_catalog_api.py -v`

Expected: FAIL because public list endpoints still return the full catalog and schools do not expose `hero_image_url`.

- [ ] **Step 3: Write minimal implementation**

Update `apps/api/app/services/catalog.py` to join `catalog.json` with `featured-content.json`.

```python
from .featured_content import load_featured_content


def list_schools(*, region: str | None = None, keyword: str | None = None) -> dict[str, Any]:
    featured = {
        item["slug"]: item
        for item in load_featured_content()["schools"]
        if item.get("is_featured")
    }
    schools = load_catalog()["schools"]
    filtered = []

    for school in schools:
        config = featured.get(school["slug"])
        if config is None:
            continue
        ...
        filtered.append(
            {
                "slug": school["slug"],
                "name": school["name"],
                "region": school["region"],
                "city": school["city"],
                "tags": school["tags"],
                "summary": school["summary"],
                "hero_image_url": config.get("hero_image_url") or None,
                "has_ranking_references": bool(school.get("ranking_references")),
            }
        )
```

```python
def list_majors() -> dict[str, Any]:
    featured_slugs = {
        item["slug"]
        for item in load_featured_content()["majors"]
        if item.get("is_featured")
    }
    items = [
        ...
        for major in load_catalog()["majors"]
        if major["slug"] in featured_slugs
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_public_catalog_api.py -v`

Expected: PASS with public school and major lists now driven by featured-content config.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/services/catalog.py apps/api/tests/test_public_catalog_api.py
git commit -m "feat(api): filter public catalog by featured content"
```

### Task 3: Add admin-side featured-content editing UI and actions

**Files:**
- Create: `apps/web/lib/admin-featured-content-api.ts`
- Modify: `apps/web/app/(admin)/admin/actions.ts`
- Modify: `apps/web/app/(admin)/admin/page.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`
- Modify: `apps/web/tests/admin-review-api.test.ts`
- Modify: `apps/web/tests/admin-page.test.tsx`

- [ ] **Step 1: Write the failing test**

Extend the admin tests so the page renders featured school and major rows and the admin client posts row updates.

```tsx
const { listReviewQueueMock, listFeaturedContentMock } = vi.hoisted(() => ({
  listReviewQueueMock: vi.fn(),
  listFeaturedContentMock: vi.fn(),
}));

vi.mock('../lib/admin-featured-content-api', () => ({
  listFeaturedContent: listFeaturedContentMock,
  updateFeaturedSchool: vi.fn(),
  updateFeaturedMajor: vi.fn(),
}));
```

```tsx
test('renders featured school and major configuration rows', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [
      {
        slug: 'southeast-university',
        name: '东南大学',
        isFeatured: true,
        heroImageUrl: 'https://cdn.example.com/southeast.jpg',
      },
    ],
    majors: [
      {
        slug: 'clinical-medicine',
        name: '临床医学',
        isFeatured: true,
      },
    ],
  });

  render(await AdminPage());

  expect(screen.getByRole('heading', { name: '学校展示配置' })).toBeInTheDocument();
  expect(screen.getByDisplayValue('https://cdn.example.com/southeast.jpg')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '专业展示配置' })).toBeInTheDocument();
  expect(screen.getByText('临床医学')).toBeInTheDocument();
});
```

```ts
test('updateFeaturedSchool posts feature state and image url', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      slug: 'southeast-university',
      is_featured: true,
      hero_image_url: 'https://cdn.example.com/southeast.jpg',
    }),
  });

  await updateFeaturedSchool('southeast-university', true, 'https://cdn.example.com/southeast.jpg');

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/admin/featured-content/schools/southeast-university',
    expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        is_featured: true,
        hero_image_url: 'https://cdn.example.com/southeast.jpg',
      }),
    }),
  );
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-review-api.test.ts tests/admin-page.test.tsx`

Expected: FAIL because admin featured-content APIs, actions, and UI rows do not yet exist.

- [ ] **Step 3: Write minimal implementation**

Create a dedicated admin client for featured-content config.

```ts
export type AdminFeaturedSchool = {
  slug: string;
  name: string;
  isFeatured: boolean;
  heroImageUrl: string;
};

export async function listFeaturedContent(): Promise<{
  schools: AdminFeaturedSchool[];
  majors: AdminFeaturedMajor[];
}> {
  const response = await fetch(`${getApiUrl()}/api/admin/featured-content`, {
    headers: buildHeaders(),
    cache: 'no-store',
  });
  const payload = await parseResponse<{
    schools: Array<{ slug: string; name: string; is_featured: boolean; hero_image_url?: string | null }>;
    majors: Array<{ slug: string; name: string; is_featured: boolean }>;
  }>(response);
  return {
    schools: payload.schools.map((item) => ({
      slug: item.slug,
      name: item.name,
      isFeatured: item.is_featured,
      heroImageUrl: item.hero_image_url ?? '',
    })),
    majors: payload.majors.map((item) => ({
      slug: item.slug,
      name: item.name,
      isFeatured: item.is_featured,
    })),
  };
}
```

Extend admin server actions:

```ts
export async function updateFeaturedSchoolAction(formData: FormData): Promise<void> {
  const slug = String(formData.get('slug') ?? '');
  const heroImageUrl = String(formData.get('heroImageUrl') ?? '');
  const isFeatured = formData.get('isFeatured') === 'on';
  await updateFeaturedSchool(slug, isFeatured, heroImageUrl);
  revalidatePath('/admin');
  revalidatePath('/');
}
```

Render the new configuration sections in `dashboard-shell.tsx` and load them in `AdminPage`.

```tsx
<section aria-labelledby="featured-schools-heading">
  <h2 id="featured-schools-heading">{'学校展示配置'}</h2>
  {featuredSchools.map((school) => (
    <form key={school.slug} action={updateFeaturedSchoolAction}>
      <input type="hidden" name="slug" value={school.slug} />
      <label>
        <input type="checkbox" name="isFeatured" defaultChecked={school.isFeatured} />
        {school.name}
      </label>
      <input type="text" name="heroImageUrl" defaultValue={school.heroImageUrl} aria-label={`学校图片 ${school.slug}`} />
      <button type="submit">{'保存'}</button>
    </form>
  ))}
</section>
```

Keep the existing review queue rendering in place.

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-review-api.test.ts tests/admin-page.test.tsx`

Expected: PASS with admin featured-content reads and row actions wired through the existing admin page.

- [ ] **Step 5: Commit**

```bash
git add apps/web/lib/admin-featured-content-api.ts apps/web/app/(admin)/admin/actions.ts apps/web/app/(admin)/admin/page.tsx apps/web/components/admin/dashboard-shell.tsx apps/web/tests/admin-review-api.test.ts apps/web/tests/admin-page.test.tsx
git commit -m "feat(web): add featured content admin controls"
```

### Task 4: Render featured school images and curated lists on the homepage

**Files:**
- Modify: `apps/web/lib/public-content-api.ts`
- Modify: `apps/web/app/page.tsx`
- Modify: `apps/web/tests/public-content-api.test.ts`
- Modify: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Write the failing test**

Extend homepage tests so featured school cards render an image when `heroImageUrl` is present and continue working without it.

```tsx
listSchoolsMock.mockResolvedValue({
  items: [
    {
      slug: 'southeast-university',
      name: '东南大学',
      region: '江苏',
      city: '南京',
      tags: ['985'],
      summary: '工科见长。',
      heroImageUrl: 'https://cdn.example.com/southeast.jpg',
      hasRankingReferences: true,
    },
  ],
  total: 1,
});
```

```tsx
expect(screen.getByRole('img', { name: '东南大学' })).toHaveAttribute(
  'src',
  'https://cdn.example.com/southeast.jpg',
);
```

Add a companion assertion that schools without `heroImageUrl` still render their text card without an image.

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-content-api.test.ts tests/public-pages.test.tsx`

Expected: FAIL because school summaries do not yet map `hero_image_url`, and the homepage does not render a school image.

- [ ] **Step 3: Write minimal implementation**

Extend school summaries in `apps/web/lib/public-content-api.ts`.

```ts
export type SchoolSummary = {
  slug: string;
  name: string;
  region: string;
  city: string;
  tags: string[];
  summary: string;
  heroImageUrl?: string;
  hasRankingReferences?: boolean;
};
```

```ts
heroImageUrl: item.hero_image_url ?? '',
```

Render the image in `apps/web/app/page.tsx` only when present.

```tsx
{school.heroImageUrl ? (
  <img
    src={school.heroImageUrl}
    alt={school.name}
    style={{ width: '100%', aspectRatio: '16 / 9', objectFit: 'cover' }}
  />
) : null}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-content-api.test.ts tests/public-pages.test.tsx`

Expected: PASS with curated school cards showing a photo when configured and falling back gracefully when not.

- [ ] **Step 5: Commit**

```bash
git add apps/web/lib/public-content-api.ts apps/web/app/page.tsx apps/web/tests/public-content-api.test.ts apps/web/tests/public-pages.test.tsx
git commit -m "feat(web): render featured school images"
```

### Task 5: Run final verification

**Files:**
- Test: `apps/api/tests/test_admin_api.py`
- Test: `apps/api/tests/test_public_catalog_api.py`
- Test: `apps/web/tests/admin-review-api.test.ts`
- Test: `apps/web/tests/admin-page.test.tsx`
- Test: `apps/web/tests/public-content-api.test.ts`
- Test: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Run focused API verification**

Run: `python -m pytest tests/test_admin_api.py tests/test_public_catalog_api.py -v`

Expected: PASS

- [ ] **Step 2: Run focused admin and homepage Web verification**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-review-api.test.ts tests/admin-page.test.tsx tests/public-content-api.test.ts tests/public-pages.test.tsx`

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
