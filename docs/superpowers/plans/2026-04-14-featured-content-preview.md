# Featured Content Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a lightweight "today preview" to the admin featured-content payload and admin page so operators can see which schools and majors are currently selected by the rotation rules.

**Architecture:** Reuse the existing API-side featured-content rotation helpers that already drive the public school and major lists, then extend the admin featured-content response with a small `preview` object. The web admin data client will map that payload into camelCase types, and the admin page will render two text-first preview sections under the rotation controls.

**Tech Stack:** FastAPI, SQLModel response models, Next.js App Router, TypeScript, Vitest, Testing Library

---

### Task 1: Add API preview data to the admin featured-content payload

**Files:**
- Modify: `apps/api/tests/test_admin_api.py`
- Modify: `apps/api/app/services/featured_content.py`
- Modify: `apps/api/app/routers/admin.py`

- [ ] **Step 1: Write the failing API test**

Add this test near the existing `test_featured_content_endpoint_returns_school_and_major_configuration` coverage in `apps/api/tests/test_admin_api.py`:

```python
def test_featured_content_endpoint_returns_today_preview(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client

    response = client.get(
        "/api/admin/featured-content",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview"] == {
        "schools": [
            {
                "slug": "southeast-university",
                "name": "东南大学",
            }
        ],
        "majors": [
            {
                "slug": "clinical-medicine",
                "name": "临床医学",
            }
        ],
    }
```

- [ ] **Step 2: Run the API test to verify it fails**

Run:

```powershell
python -m pytest apps/api/tests/test_admin_api.py::test_featured_content_endpoint_returns_today_preview -v
```

Expected: `FAIL` because the current `GET /api/admin/featured-content` response has no `preview` field.

- [ ] **Step 3: Write the minimal API implementation**

Update `apps/api/app/services/featured_content.py` to expose a reusable preview helper based on the same current-rotation logic already used by public lists:

```python
def _preview_items(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "slug": item["slug"],
            "name": item["name"],
        }
        for item in entries
    ]


def build_featured_content_preview() -> dict[str, list[dict[str, str]]]:
    return {
        "schools": _preview_items(list_current_featured_schools()),
        "majors": _preview_items(list_current_featured_majors()),
    }
```

Update `apps/api/app/routers/admin.py` to extend the response models and include the preview in `get_featured_content()`:

```python
from ..services.featured_content import (
    build_featured_content_preview,
    list_featured_content,
    update_featured_major,
    update_rotation_rule,
    update_featured_school,
)


class FeaturedPreviewItemResponse(SQLModel):
    slug: str
    name: str


class FeaturedContentPreviewResponse(SQLModel):
    schools: list[FeaturedPreviewItemResponse]
    majors: list[FeaturedPreviewItemResponse]


class FeaturedContentResponse(SQLModel):
    schools: list[FeaturedSchoolConfigResponse]
    majors: list[FeaturedMajorConfigResponse]
    rotation: FeaturedContentRotationResponse
    preview: FeaturedContentPreviewResponse


@router.get("/featured-content", response_model=FeaturedContentResponse)
def get_featured_content(
    _authorized: None = Depends(require_admin),
) -> FeaturedContentResponse:
    payload = list_featured_content()
    preview = build_featured_content_preview()
    return FeaturedContentResponse(
        schools=[
            FeaturedSchoolConfigResponse(**school)
            for school in payload["schools"]
        ],
        majors=[
            FeaturedMajorConfigResponse(**major)
            for major in payload["majors"]
        ],
        rotation=FeaturedContentRotationResponse(
            schools=FeaturedRotationRuleResponse(**payload["rotation"]["schools"]),
            majors=FeaturedRotationRuleResponse(**payload["rotation"]["majors"]),
        ),
        preview=FeaturedContentPreviewResponse(
            schools=[
                FeaturedPreviewItemResponse(**school)
                for school in preview["schools"]
            ],
            majors=[
                FeaturedPreviewItemResponse(**major)
                for major in preview["majors"]
            ],
        ),
    )
```

- [ ] **Step 4: Run the API test to verify it passes**

Run:

```powershell
python -m pytest apps/api/tests/test_admin_api.py::test_featured_content_endpoint_returns_today_preview -v
```

Expected: `PASS`

- [ ] **Step 5: Commit the API preview change**

Run:

```powershell
git add apps/api/tests/test_admin_api.py apps/api/app/services/featured_content.py apps/api/app/routers/admin.py
git commit -m "feat(api): add featured content preview payload"
```

### Task 2: Surface the preview in the web admin client and page

**Files:**
- Modify: `apps/web/tests/admin-review-api.test.ts`
- Modify: `apps/web/tests/admin-page.test.tsx`
- Modify: `apps/web/lib/admin-featured-content-api.ts`
- Modify: `apps/web/app/(admin)/admin/page.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`

- [ ] **Step 1: Write the failing web tests**

Update `apps/web/tests/admin-review-api.test.ts` so `listFeaturedContent` expects the new preview payload:

```ts
expect(payload.preview).toEqual({
  schools: [
    {
      slug: 'southeast-university',
      name: '东南大学',
    },
  ],
  majors: [
    {
      slug: 'clinical-medicine',
      name: '临床医学',
    },
  ],
});
```

Add the matching mocked API payload in that test:

```ts
preview: {
  schools: [
    {
      slug: 'southeast-university',
      name: '东南大学',
    },
  ],
  majors: [
    {
      slug: 'clinical-medicine',
      name: '临床医学',
    },
  ],
},
```

Update `apps/web/tests/admin-page.test.tsx` so the admin page expects the new preview sections and entries:

```tsx
expect(screen.getByRole('heading', { name: '今日展示学校' })).toBeInTheDocument();
expect(screen.getByRole('heading', { name: '今日展示专业' })).toBeInTheDocument();
expect(screen.getByText('东南大学')).toBeInTheDocument();
expect(screen.getByText('southeast-university')).toBeInTheDocument();
expect(screen.getByText('临床医学')).toBeInTheDocument();
expect(screen.getByText('clinical-medicine')).toBeInTheDocument();
```

Add a second page test for empty preview lists:

```tsx
test('renders empty preview states when today preview is empty', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [],
    majors: [],
    rotation: {
      schools: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
      majors: {
        enabled: false,
        frequencyDays: 1,
        windowSize: 1,
        orderedSlugs: [],
      },
    },
    preview: {
      schools: [],
      majors: [],
    },
  });

  render(await AdminPage());

  expect(screen.getByText('当前没有可展示学校')).toBeInTheDocument();
  expect(screen.getByText('当前没有可展示专业')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the focused web tests to verify they fail**

Run:

```powershell
node .\apps\web\node_modules\vitest\vitest.mjs run apps/web/tests/admin-review-api.test.ts apps/web/tests/admin-page.test.tsx
```

Expected: `FAIL` because `AdminFeaturedContent` does not expose `preview`, and the admin page does not render the new sections.

- [ ] **Step 3: Write the minimal web implementation**

Update `apps/web/lib/admin-featured-content-api.ts` to add preview types and mapping:

```ts
export type AdminFeaturedPreviewItem = {
  slug: string;
  name: string;
};

export type AdminFeaturedContent = {
  schools: AdminFeaturedSchool[];
  majors: AdminFeaturedMajor[];
  rotation: {
    schools: AdminRotationRule;
    majors: AdminRotationRule;
  };
  preview: {
    schools: AdminFeaturedPreviewItem[];
    majors: AdminFeaturedPreviewItem[];
  };
};

  const payload = await parseResponse<{
    schools: Array<{
      slug: string;
      name: string;
      is_featured: boolean;
      hero_image_url?: string | null;
    }>;
    majors: Array<{
      slug: string;
      name: string;
      is_featured: boolean;
    }>;
    rotation?: {
      schools?: {
        enabled: boolean;
        frequency_days: number;
        window_size: number;
        ordered_slugs: string[];
      };
      majors?: {
        enabled: boolean;
        frequency_days: number;
        window_size: number;
        ordered_slugs: string[];
      };
    };
    preview?: {
      schools?: Array<{
        slug: string;
        name: string;
      }>;
      majors?: Array<{
        slug: string;
        name: string;
      }>;
    };
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
    rotation: {
      schools: mapRotationRule(payload.rotation?.schools),
      majors: mapRotationRule(payload.rotation?.majors),
    },
    preview: {
      schools: payload.preview?.schools ?? [],
      majors: payload.preview?.majors ?? [],
    },
  };
```

Update `apps/web/app/(admin)/admin/page.tsx` to pass preview into `DashboardShell`:

```tsx
import {
  type AdminFeaturedMajor,
  type AdminFeaturedPreviewItem,
  type AdminFeaturedSchool,
  type AdminRotationRule,
  listFeaturedContent,
} from '../../../lib/admin-featured-content-api';

  let featuredSchoolPreview: AdminFeaturedPreviewItem[] = [];
  let featuredMajorPreview: AdminFeaturedPreviewItem[] = [];

    featuredSchoolPreview = featuredContent.preview.schools;
    featuredMajorPreview = featuredContent.preview.majors;

    <DashboardShell
      title="内容运营后台"
      queueItems={queueItems}
      featuredSchools={featuredSchools}
      featuredMajors={featuredMajors}
      schoolRotation={schoolRotation}
      majorRotation={majorRotation}
      featuredSchoolPreview={featuredSchoolPreview}
      featuredMajorPreview={featuredMajorPreview}
      queueError={queueError}
      featuredContentError={featuredContentError}
      approveAction={approveReviewQueueAction}
      rejectAction={rejectReviewQueueAction}
      updateFeaturedSchoolAction={updateFeaturedSchoolAction}
      updateFeaturedMajorAction={updateFeaturedMajorAction}
      updateSchoolRotationAction={updateSchoolRotationAction}
      updateMajorRotationAction={updateMajorRotationAction}
    />
```

Update `apps/web/components/admin/dashboard-shell.tsx` to add preview props and render the new sections under the rotation controls:

```tsx
import type {
  AdminFeaturedMajor,
  AdminFeaturedPreviewItem,
  AdminFeaturedSchool,
  AdminRotationRule,
} from '../../lib/admin-featured-content-api';

type DashboardShellProps = {
  title: string;
  queueItems: AdminReviewItem[];
  featuredSchools: AdminFeaturedSchool[];
  featuredMajors: AdminFeaturedMajor[];
  schoolRotation: AdminRotationRule;
  majorRotation: AdminRotationRule;
  featuredSchoolPreview: AdminFeaturedPreviewItem[];
  featuredMajorPreview: AdminFeaturedPreviewItem[];
  queueError?: string;
  featuredContentError?: string;
  approveAction: (formData: FormData) => Promise<void>;
  rejectAction: (formData: FormData) => Promise<void>;
  updateFeaturedSchoolAction: (formData: FormData) => Promise<void>;
  updateFeaturedMajorAction: (formData: FormData) => Promise<void>;
  updateSchoolRotationAction: (formData: FormData) => Promise<void>;
  updateMajorRotationAction: (formData: FormData) => Promise<void>;
};

      <section aria-labelledby="featured-school-preview-heading">
        <h2 id="featured-school-preview-heading">今日展示学校</h2>

        {featuredContentError ? null : featuredSchoolPreview.length === 0 ? (
          <p>当前没有可展示学校</p>
        ) : (
          <ul>
            {featuredSchoolPreview.map((school) => (
              <li key={school.slug}>
                <span>{school.name}</span>
                <span>{school.slug}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="featured-major-preview-heading">
        <h2 id="featured-major-preview-heading">今日展示专业</h2>

        {featuredContentError ? null : featuredMajorPreview.length === 0 ? (
          <p>当前没有可展示专业</p>
        ) : (
          <ul>
            {featuredMajorPreview.map((major) => (
              <li key={major.slug}>
                <span>{major.name}</span>
                <span>{major.slug}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
```

- [ ] **Step 4: Run the focused web tests to verify they pass**

Run:

```powershell
node .\apps\web\node_modules\vitest\vitest.mjs run apps/web/tests/admin-review-api.test.ts apps/web/tests/admin-page.test.tsx
```

Expected: `PASS`

- [ ] **Step 5: Commit the web preview change**

Run:

```powershell
git add apps/web/tests/admin-review-api.test.ts apps/web/tests/admin-page.test.tsx apps/web/lib/admin-featured-content-api.ts "apps/web/app/(admin)/admin/page.tsx" apps/web/components/admin/dashboard-shell.tsx
git commit -m "feat(web): show featured content preview in admin"
```

### Task 3: Verify the full feature end-to-end before handoff

**Files:**
- Modify: none
- Test: `apps/api/tests/test_admin_api.py`
- Test: `apps/web/tests/admin-review-api.test.ts`
- Test: `apps/web/tests/admin-page.test.tsx`

- [ ] **Step 1: Run the focused API regression suite**

Run:

```powershell
python -m pytest apps/api/tests/test_admin_api.py -v
```

Expected: `PASS`, including the new preview coverage and existing featured-content/review-queue coverage.

- [ ] **Step 2: Run the focused web admin regression suite**

Run:

```powershell
node .\apps\web\node_modules\vitest\vitest.mjs run apps/web/tests/admin-review-api.test.ts apps/web/tests/admin-page.test.tsx
```

Expected: `PASS`

- [ ] **Step 3: Run the full web test suite**

Run:

```powershell
node .\apps\web\node_modules\vitest\vitest.mjs run
```

Expected: `PASS`

- [ ] **Step 4: Run the production web build**

Run:

```powershell
node .\apps\web\node_modules\next\dist\bin\next build
```

Expected: `Build completed successfully` with the already-known Windows SWC warning still acceptable.

- [ ] **Step 5: Confirm the worktree is in the expected state**

Run:

```powershell
git status --short
```

Expected:
- no unexpected untracked files
- no uncommitted changes beyond the already-planned preview implementation commits from Tasks 1 and 2
