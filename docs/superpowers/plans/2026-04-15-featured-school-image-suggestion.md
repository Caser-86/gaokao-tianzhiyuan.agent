# Featured School Image Suggestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a low-risk admin-only image suggestion flow that fetches one candidate school image from the school's official website, shows it in the admin featured-school row, and lets operators confirm before saving it to `hero_image_url`.

**Architecture:** Extend the existing featured-content admin API with a read-only suggestion endpoint that derives a candidate image from the catalog's school website URL. Keep persistence unchanged: the suggestion result stays ephemeral until the operator clicks a separate "use this image" action that reuses the existing featured-school update path. Surface the result inline in the existing `/admin` school configuration UI using the current server-rendered form/action pattern.

**Tech Stack:** FastAPI, existing catalog/featured-content services, Python stdlib HTTP + HTML parsing, Next.js App Router server actions, Vitest, pytest

---

### Task 1: Add admin API support for school image suggestions

**Files:**
- Modify: `apps/api/app/services/catalog.py`
- Modify: `apps/api/app/routers/admin.py`
- Test: `apps/api/tests/test_admin_api.py`

- [ ] **Step 1: Write the failing API tests**

Add these tests to `apps/api/tests/test_admin_api.py` near the featured-content tests:

```python
def test_suggest_featured_school_image_returns_candidate(admin_client, featured_content_file, monkeypatch) -> None:
    client, _engine = admin_client

    monkeypatch.setattr(
        featured_content_service,
        "fetch_school_image_candidate",
        lambda slug: {
            "slug": slug,
            "name": "东南大学",
            "status": "found",
            "source_url": "https://www.seu.edu.cn/",
            "suggested_image_url": "https://www.seu.edu.cn/assets/hero.jpg",
            "message": None,
        },
    )

    response = client.post(
        "/api/admin/featured-content/schools/southeast-university/suggest-image",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json() == {
        "slug": "southeast-university",
        "name": "东南大学",
        "status": "found",
        "source_url": "https://www.seu.edu.cn/",
        "suggested_image_url": "https://www.seu.edu.cn/assets/hero.jpg",
        "message": None,
    }


def test_suggest_featured_school_image_returns_missing_when_school_has_no_website(
    admin_client,
    featured_content_file,
    monkeypatch,
) -> None:
    client, _engine = admin_client

    monkeypatch.setattr(
        featured_content_service,
        "fetch_school_image_candidate",
        lambda slug: {
            "slug": slug,
            "name": "东南大学",
            "status": "missing",
            "source_url": None,
            "suggested_image_url": None,
            "message": "学校未配置可抓取的官网地址",
        },
    )

    response = client.post(
        "/api/admin/featured-content/schools/southeast-university/suggest-image",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "missing"
    assert response.json()["message"] == "学校未配置可抓取的官网地址"


def test_suggest_featured_school_image_returns_404_for_unknown_slug(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client

    response = client.post(
        "/api/admin/featured-content/schools/missing-school/suggest-image",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "featured content entity not found"}
```

- [ ] **Step 2: Run the API tests to verify failure**

Run:

```powershell
python -m pytest tests/test_admin_api.py -v
```

Expected: FAIL because `/api/admin/featured-content/schools/{slug}/suggest-image` and `fetch_school_image_candidate()` do not exist yet.

- [ ] **Step 3: Add the minimal service implementation**

In `apps/api/app/services/catalog.py`, add a helper for school website lookup:

```python
def get_school_website(slug: str) -> str | None:
    school = get_school_detail(slug)
    if school is None:
        raise KeyError(slug)

    website = school.get("website") or school.get("source_url") or school.get("official_website")
    if not isinstance(website, str):
        return None

    normalized = website.strip()
    return normalized or None
```

In `apps/api/app/services/featured_content.py`, add a focused candidate fetcher:

```python
from html.parser import HTMLParser
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from .catalog import get_school_detail, get_school_website


class _ImageCandidateParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.og_image: str | None = None
        self.first_image: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "meta":
            property_name = (values.get("property") or values.get("name") or "").lower()
            content = values.get("content") or ""
            if property_name == "og:image" and content and self.og_image is None:
                self.og_image = content
        if tag == "img":
            src = values.get("src") or ""
            if src and self.first_image is None:
                self.first_image = src


def fetch_school_image_candidate(slug: str) -> dict[str, Any]:
    school = get_school_detail(slug)
    if school is None:
        raise KeyError(slug)

    website = get_school_website(slug)
    if not website:
        return {
            "slug": school["slug"],
            "name": school["name"],
            "status": "missing",
            "source_url": None,
            "suggested_image_url": None,
            "message": "学校未配置可抓取的官网地址",
        }

    request = Request(
        website,
        headers={"User-Agent": "gaokao-agent/1.0 (+featured-school-image-suggestion)"},
    )

    try:
        with urlopen(request, timeout=8) as response:
            html = response.read().decode("utf-8", errors="ignore")
    except Exception:
        return {
            "slug": school["slug"],
            "name": school["name"],
            "status": "failed",
            "source_url": website,
            "suggested_image_url": None,
            "message": "抓取失败，请稍后重试",
        }

    parser = _ImageCandidateParser()
    parser.feed(html)
    candidate = parser.og_image or parser.first_image

    if not candidate:
        return {
            "slug": school["slug"],
            "name": school["name"],
            "status": "missing",
            "source_url": website,
            "suggested_image_url": None,
            "message": "官网页面未找到可用图片",
        }

    return {
        "slug": school["slug"],
        "name": school["name"],
        "status": "found",
        "source_url": website,
        "suggested_image_url": urljoin(website, candidate),
        "message": None,
    }
```

In `apps/api/app/routers/admin.py`, add a response model and route:

```python
class FeaturedSchoolImageSuggestionResponse(SQLModel):
    slug: str
    name: str
    status: str
    source_url: str | None = None
    suggested_image_url: str | None = None
    message: str | None = None


@router.post(
    "/featured-content/schools/{slug}/suggest-image",
    response_model=FeaturedSchoolImageSuggestionResponse,
)
def suggest_featured_school_image(
    slug: str,
    _authorized: None = Depends(require_admin),
) -> FeaturedSchoolImageSuggestionResponse:
    try:
        suggestion = fetch_school_image_candidate(slug)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="featured content entity not found",
        ) from exc

    return FeaturedSchoolImageSuggestionResponse(**suggestion)
```

- [ ] **Step 4: Run API tests to verify pass**

Run:

```powershell
python -m pytest tests/test_admin_api.py -v
```

Expected: PASS with the three new suggestion tests and no regressions in existing admin API tests.

- [ ] **Step 5: Commit the API changes**

```powershell
git add apps/api/app/services/catalog.py apps/api/app/services/featured_content.py apps/api/app/routers/admin.py apps/api/tests/test_admin_api.py
git commit -m "feat(api): add featured school image suggestion endpoint"
```

### Task 2: Add web API client and server actions for image suggestions

**Files:**
- Modify: `apps/web/lib/admin-featured-content-api.ts`
- Modify: `apps/web/app/(admin)/admin/actions.ts`
- Test: `apps/web/tests/admin-review-api.test.ts`

- [ ] **Step 1: Write the failing web client and action tests**

Add a client test to `apps/web/tests/admin-review-api.test.ts`:

```ts
test('suggestFeaturedSchoolImage posts to the school suggestion endpoint', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(
      JSON.stringify({
        slug: 'southeast-university',
        name: '东南大学',
        status: 'found',
        source_url: 'https://www.seu.edu.cn/',
        suggested_image_url: 'https://www.seu.edu.cn/assets/hero.jpg',
        message: null,
      }),
      { status: 200 },
    ),
  );
  vi.stubGlobal('fetch', fetchMock);

  const payload = await suggestFeaturedSchoolImage('southeast-university');

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/admin/featured-content/schools/southeast-university/suggest-image',
    expect.objectContaining({
      method: 'POST',
      headers: expect.objectContaining({
        'x-admin-token': 'test-admin-token',
      }),
    }),
  );
  expect(payload.status).toBe('found');
  expect(payload.suggestedImageUrl).toBe('https://www.seu.edu.cn/assets/hero.jpg');
});
```

Add an action test:

```ts
test('suggestSchoolImageAction returns the suggested candidate payload', async () => {
  suggestFeaturedSchoolImageMock.mockResolvedValue({
    slug: 'southeast-university',
    name: '东南大学',
    status: 'found',
    sourceUrl: 'https://www.seu.edu.cn/',
    suggestedImageUrl: 'https://www.seu.edu.cn/assets/hero.jpg',
    message: null,
  });

  const formData = new FormData();
  formData.set('slug', 'southeast-university');

  await expect(suggestSchoolImageAction(formData)).resolves.toEqual({
    slug: 'southeast-university',
    name: '东南大学',
    status: 'found',
    sourceUrl: 'https://www.seu.edu.cn/',
    suggestedImageUrl: 'https://www.seu.edu.cn/assets/hero.jpg',
    message: null,
  });
});
```

- [ ] **Step 2: Run the web client/action tests to verify failure**

Run:

```powershell
node .\node_modules\vitest\vitest.mjs run tests/admin-review-api.test.ts
```

Expected: FAIL because `suggestFeaturedSchoolImage` and `suggestSchoolImageAction` do not exist yet.

- [ ] **Step 3: Add the minimal web client and action implementation**

In `apps/web/lib/admin-featured-content-api.ts`, add the type and client:

```ts
export type AdminFeaturedSchoolImageSuggestion = {
  slug: string;
  name: string;
  status: 'found' | 'missing' | 'failed';
  sourceUrl: string | null;
  suggestedImageUrl: string | null;
  message: string | null;
};

export async function suggestFeaturedSchoolImage(
  slug: string,
): Promise<AdminFeaturedSchoolImageSuggestion> {
  const response = await fetch(
    `${getApiUrl()}/api/admin/featured-content/schools/${slug}/suggest-image`,
    {
      method: 'POST',
      headers: buildHeaders(),
      cache: 'no-store',
    },
  );
  const payload = await parseResponse<{
    slug: string;
    name: string;
    status: 'found' | 'missing' | 'failed';
    source_url?: string | null;
    suggested_image_url?: string | null;
    message?: string | null;
  }>(response);

  return {
    slug: payload.slug,
    name: payload.name,
    status: payload.status,
    sourceUrl: payload.source_url ?? null,
    suggestedImageUrl: payload.suggested_image_url ?? null,
    message: payload.message ?? null,
  };
}
```

In `apps/web/app/(admin)/admin/actions.ts`, add:

```ts
export async function suggestSchoolImageAction(formData: FormData) {
  const slug = String(formData.get('slug') ?? '').trim();
  if (!slug) {
    throw new Error('school slug is required');
  }

  return suggestFeaturedSchoolImage(slug);
}
```

If `actions.ts` already centralizes imports, add the corresponding import only:

```ts
import {
  suggestFeaturedSchoolImage,
  updateFeaturedSchool,
  ...
} from '../../../lib/admin-featured-content-api';
```

- [ ] **Step 4: Run the web client/action tests to verify pass**

Run:

```powershell
node .\node_modules\vitest\vitest.mjs run tests/admin-review-api.test.ts
```

Expected: PASS with the new suggestion client/action coverage.

- [ ] **Step 5: Commit the web client/action changes**

```powershell
git add apps/web/lib/admin-featured-content-api.ts apps/web/app/(admin)/admin/actions.ts apps/web/tests/admin-review-api.test.ts
git commit -m "feat(web): add featured school image suggestion client"
```

### Task 3: Render inline suggestion UI in the admin school configuration rows

**Files:**
- Modify: `apps/web/app/(admin)/admin/page.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`
- Test: `apps/web/tests/admin-dashboard.test.tsx`
- Test: `apps/web/tests/admin-page.test.tsx`

- [ ] **Step 1: Write the failing admin UI tests**

In `apps/web/tests/admin-dashboard.test.tsx`, add a render test around the school row:

```tsx
test('renders school image suggestion controls and success state', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[
        {
          slug: 'southeast-university',
          name: '东南大学',
          isFeatured: true,
          heroImageUrl: '',
        },
      ]}
      featuredMajors={[]}
      schoolRotation={{ enabled: false, frequencyDays: 1, windowSize: 1, orderedSlugs: [] }}
      majorRotation={{ enabled: false, frequencyDays: 1, windowSize: 1, orderedSlugs: [] }}
      featuredSchoolPreview={[]}
      featuredMajorPreview={[]}
      nextFeaturedSchoolPreview={[]}
      nextFeaturedMajorPreview={[]}
      featuredSchedule={[]}
      selectedPreviewDateValue=""
      selectedDatePreview={null}
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
      suggestSchoolImageAction={async () => ({
        slug: 'southeast-university',
        name: '东南大学',
        status: 'found',
        sourceUrl: 'https://www.seu.edu.cn/',
        suggestedImageUrl: 'https://www.seu.edu.cn/assets/hero.jpg',
        message: null,
      })}
      schoolImageSuggestions={{
        'southeast-university': {
          slug: 'southeast-university',
          name: '东南大学',
          status: 'found',
          sourceUrl: 'https://www.seu.edu.cn/',
          suggestedImageUrl: 'https://www.seu.edu.cn/assets/hero.jpg',
          message: null,
        },
      }}
    />,
  );

  expect(screen.getByRole('button', { name: '尝试抓取图片' })).toBeInTheDocument();
  expect(screen.getByAltText('东南大学候选图片')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: '查看来源页' })).toHaveAttribute(
    'href',
    'https://www.seu.edu.cn/',
  );
  expect(screen.getByRole('button', { name: '使用该图片' })).toBeInTheDocument();
});
```

In `apps/web/tests/admin-page.test.tsx`, add page wiring coverage:

```tsx
test('passes school image suggestions into the admin shell', async () => {
  listFeaturedContentMock.mockResolvedValue({
    schools: [
      { slug: 'southeast-university', name: '东南大学', isFeatured: true, heroImageUrl: '' },
    ],
    majors: [],
    rotation: {
      schools: { enabled: false, frequencyDays: 1, windowSize: 1, orderedSlugs: [] },
      majors: { enabled: false, frequencyDays: 1, windowSize: 1, orderedSlugs: [] },
    },
    preview: {
      today: { schools: [], majors: [] },
      next: { schools: [], majors: [] },
      schedule: [],
      selectedDate: null,
      selectedDateError: null,
    },
  });

  const page = await AdminPage({
    searchParams: Promise.resolve({
      suggested_school_image_slug: 'southeast-university',
    }),
  });

  render(page);

  expect(screen.getByAltText('东南大学候选图片')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the admin UI tests to verify failure**

Run:

```powershell
node .\node_modules\vitest\vitest.mjs run tests/admin-dashboard.test.tsx tests/admin-page.test.tsx
```

Expected: FAIL because the page and dashboard do not yet know about image suggestions.

- [ ] **Step 3: Add the minimal admin UI implementation**

In `apps/web/app/(admin)/admin/page.tsx`, add:

```ts
import { suggestSchoolImageAction, ... } from './actions';
import type { AdminFeaturedSchoolImageSuggestion } from '../../../lib/admin-featured-content-api';
```

Add query parsing and one-school fetch:

```ts
type AdminPageProps = {
  searchParams?: Promise<{
    ...
    suggested_school_image_slug?: string;
  }>;
};

let schoolImageSuggestions: Record<string, AdminFeaturedSchoolImageSuggestion> = {};
const suggestedSchoolImageSlug =
  resolvedSearchParams?.suggested_school_image_slug?.trim() || undefined;

if (suggestedSchoolImageSlug) {
  try {
    const suggestion = await suggestFeaturedSchoolImage(suggestedSchoolImageSlug);
    schoolImageSuggestions = {
      [suggestion.slug]: suggestion,
    };
  } catch (_error) {
    schoolImageSuggestions = {
      [suggestedSchoolImageSlug]: {
        slug: suggestedSchoolImageSlug,
        name:
          featuredContent.schools.find((school) => school.slug === suggestedSchoolImageSlug)?.name ??
          suggestedSchoolImageSlug,
        status: 'failed',
        sourceUrl: null,
        suggestedImageUrl: null,
        message: '抓取失败，请稍后重试',
      },
    };
  }
}
```

Pass the new props into `DashboardShell`:

```tsx
<DashboardShell
  ...
  suggestSchoolImageAction={suggestSchoolImageAction}
  schoolImageSuggestions={schoolImageSuggestions}
/>
```

In `apps/web/components/admin/dashboard-shell.tsx`, extend props:

```ts
import type { AdminFeaturedSchoolImageSuggestion } from '../../lib/admin-featured-content-api';

type DashboardShellProps = {
  ...
  schoolImageSuggestions?: Record<string, AdminFeaturedSchoolImageSuggestion>;
  suggestSchoolImageAction?: (formData: FormData) => Promise<AdminFeaturedSchoolImageSuggestion>;
};
```

In the featured-school row, add two small forms:

```tsx
<form action={suggestSchoolImageAction ?? noopAction}>
  <input type="hidden" name="slug" value={school.slug} />
  <button type="submit" formAction={buildAdminHref({ ...existingFilters, suggestedSchoolImageSlug: school.slug })}>
    尝试抓取图片
  </button>
</form>

{suggestion?.status === 'found' ? (
  <div>
    <img src={suggestion.suggestedImageUrl ?? ''} alt={`${school.name}候选图片`} />
    <a href={suggestion.sourceUrl ?? '#'} target="_blank" rel="noreferrer">查看来源页</a>
    <form action={updateFeaturedSchoolAction}>
      <input type="hidden" name="slug" value={school.slug} />
      <input type="hidden" name="isFeatured" value={school.isFeatured ? '1' : '0'} />
      <input type="hidden" name="heroImageUrl" value={suggestion.suggestedImageUrl ?? ''} />
      <button type="submit">使用该图片</button>
    </form>
  </div>
) : null}

{suggestion?.status !== 'found' && suggestion?.message ? <p>{suggestion.message}</p> : null}
```

Keep the state strictly server-driven: query parameter in, suggestion payload out.

- [ ] **Step 4: Run the admin UI tests and full web verification**

Run:

```powershell
node .\node_modules\vitest\vitest.mjs run tests/admin-dashboard.test.tsx tests/admin-page.test.tsx
node .\node_modules\vitest\vitest.mjs run
node .\node_modules\next\dist\bin\next build
```

Expected:
- targeted admin tests PASS
- full web suite PASS
- `next build` succeeds (existing native SWC policy warning may still print while wasm fallback succeeds)

- [ ] **Step 5: Commit the admin UI changes**

```powershell
git add apps/web/app/(admin)/admin/page.tsx apps/web/components/admin/dashboard-shell.tsx apps/web/tests/admin-dashboard.test.tsx apps/web/tests/admin-page.test.tsx
git commit -m "feat(web): suggest featured school images in admin"
```
