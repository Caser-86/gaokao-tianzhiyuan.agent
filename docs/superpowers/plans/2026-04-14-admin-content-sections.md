# Admin Content Sections Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add admin-side editing for school and major content sections so operations can create, update, and remove `sections` without editing `data/catalog.json` by hand.

**Architecture:** Extend the existing catalog-backed admin APIs with a new content-sections read/write surface, then connect the admin page to those endpoints with a small web client and server actions. Keep the first version server-rendered and form-driven: one extra blank section row enables “add”, and fully blank rows are ignored to support “delete” without introducing client-side section state.

**Tech Stack:** FastAPI, Python, Next.js App Router, TypeScript, Vitest, pytest, JSON catalog persistence

---

### Task 1: Add API coverage for admin content sections

**Files:**
- Create: `apps/api/tests/test_admin_content_sections_api.py`
- Modify: `apps/api/app/services/catalog.py`
- Modify: `apps/api/app/routers/admin.py`

- [ ] **Step 1: Write the failing API tests**

```python
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def auth_headers() -> dict[str, str]:
    return {"x-admin-token": settings.admin_token}


def test_content_sections_endpoint_returns_school_and_major_entries() -> None:
    response = client.get("/api/admin/content-sections", headers=auth_headers())

    assert response.status_code == 200
    payload = response.json()
    assert any(item["slug"] == "southeast-university" for item in payload["schools"])
    assert any(item["slug"] == "clinical-medicine" for item in payload["majors"])


def test_update_school_sections() -> None:
    response = client.post(
        "/api/admin/content-sections/schools/southeast-university",
        headers=auth_headers(),
        json={
            "sections": [
                {
                    "type": "highlights",
                    "title": "学校亮点",
                    "items": ["资源密集", "适合自驱型学生"],
                },
                {
                    "type": "pitfalls",
                    "title": "坑点提醒",
                    "items": ["课程强度高"],
                },
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["slug"] == "southeast-university"
    assert len(payload["sections"]) == 2
    assert payload["sections"][1]["title"] == "坑点提醒"


def test_update_major_sections_rejects_partially_filled_section() -> None:
    response = client.post(
        "/api/admin/content-sections/majors/clinical-medicine",
        headers=auth_headers(),
        json={
            "sections": [
                {
                    "type": "fit_for",
                    "title": "",
                    "items": ["培养周期长"],
                }
            ]
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "content section row is invalid"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_admin_content_sections_api.py -v`
Expected: `FAIL` because `/api/admin/content-sections` routes do not exist yet.

- [ ] **Step 3: Write the minimal API implementation**

```python
# apps/api/app/services/catalog.py
def list_admin_content_sections() -> dict[str, Any]:
    catalog = load_catalog()
    return {
        "schools": [
            {
                "slug": school["slug"],
                "name": school["name"],
                "sections": school.get("sections", []),
            }
            for school in catalog["schools"]
        ],
        "majors": [
            {
                "slug": major["slug"],
                "name": major["name"],
                "sections": major.get("sections", []),
            }
            for major in catalog["majors"]
        ],
    }


def update_content_sections(
    entity_key: str,
    slug: str,
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    catalog = load_catalog()
    entries = catalog[entity_key]
    entity = next((item for item in entries if item["slug"] == slug), None)
    if entity is None:
        raise KeyError(slug)

    entity["sections"] = sections
    CATALOG_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    load_catalog.cache_clear()

    return {
        "slug": entity["slug"],
        "name": entity["name"],
        "sections": entity.get("sections", []),
    }
```

```python
# apps/api/app/routers/admin.py
class ContentSectionResponse(SQLModel):
    type: str
    title: str
    items: list[str]


class ContentSectionEntityResponse(SQLModel):
    slug: str
    name: str
    sections: list[ContentSectionResponse]


class ContentSectionListResponse(SQLModel):
    schools: list[ContentSectionEntityResponse]
    majors: list[ContentSectionEntityResponse]


class ContentSectionRequest(SQLModel):
    type: str
    title: str
    items: list[str]


class ContentSectionUpdateRequest(SQLModel):
    sections: list[ContentSectionRequest]


def normalize_content_sections(
    sections: list[ContentSectionRequest],
) -> list[dict[str, str | list[str]]]:
    normalized: list[dict[str, str | list[str]]] = []

    for section in sections:
      type_value = section.type.strip()
      title_value = section.title.strip()
      items = [item.strip() for item in section.items if item.strip()]

      if not type_value and not title_value and not items:
          continue

      if not type_value or not title_value or not items:
          raise HTTPException(
              status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
              detail="content section row is invalid",
          )

      normalized.append(
          {
              "type": type_value,
              "title": title_value,
              "items": items,
          }
      )

    return normalized


@router.get("/content-sections", response_model=ContentSectionListResponse)
def get_content_sections(
    _authorized: None = Depends(require_admin),
) -> ContentSectionListResponse:
    payload = list_admin_content_sections()
    return ContentSectionListResponse(
        schools=[ContentSectionEntityResponse(**item) for item in payload["schools"]],
        majors=[ContentSectionEntityResponse(**item) for item in payload["majors"]],
    )


@router.post(
    "/content-sections/schools/{slug}",
    response_model=ContentSectionEntityResponse,
)
def update_school_content_sections(
    slug: str,
    payload: ContentSectionUpdateRequest,
    _authorized: None = Depends(require_admin),
) -> ContentSectionEntityResponse:
    updated = update_content_sections("schools", slug, normalize_content_sections(payload.sections))
    return ContentSectionEntityResponse(**updated)


@router.post(
    "/content-sections/majors/{slug}",
    response_model=ContentSectionEntityResponse,
)
def update_major_content_sections(
    slug: str,
    payload: ContentSectionUpdateRequest,
    _authorized: None = Depends(require_admin),
) -> ContentSectionEntityResponse:
    updated = update_content_sections("majors", slug, normalize_content_sections(payload.sections))
    return ContentSectionEntityResponse(**updated)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_admin_content_sections_api.py -v`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/api/tests/test_admin_content_sections_api.py apps/api/app/services/catalog.py apps/api/app/routers/admin.py
git commit -m "feat(api): add admin content sections endpoints"
```

### Task 2: Add web client and server actions for content sections

**Files:**
- Create: `apps/web/lib/admin-content-sections-api.ts`
- Modify: `apps/web/app/(admin)/admin/actions.ts`

- [ ] **Step 1: Write the failing web client/action test**

```typescript
import { expect, test, vi } from 'vitest';

import { listContentSections, updateSchoolSections } from '../lib/admin-content-sections-api';

test('maps admin content sections payload', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        schools: [
          {
            slug: 'southeast-university',
            name: '东南大学',
            sections: [{ type: 'highlights', title: '学校亮点', items: ['资源密集'] }],
          },
        ],
        majors: [],
      }),
    }),
  );

  const payload = await listContentSections();

  expect(payload.schools[0].sections[0].title).toBe('学校亮点');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-content-sections-api.test.ts`
Expected: `FAIL` because the module does not exist yet.

- [ ] **Step 3: Write the minimal web client and actions**

```typescript
// apps/web/lib/admin-content-sections-api.ts
export type AdminContentSection = {
  type: string;
  title: string;
  items: string[];
};

export type AdminContentSectionsEntity = {
  slug: string;
  name: string;
  sections: AdminContentSection[];
};

export type AdminContentSectionsList = {
  schools: AdminContentSectionsEntity[];
  majors: AdminContentSectionsEntity[];
};

export async function listContentSections(): Promise<AdminContentSectionsList> { /* fetch + map */ }
export async function updateSchoolSections(slug: string, sections: AdminContentSection[]) { /* fetch + map */ }
export async function updateMajorSections(slug: string, sections: AdminContentSection[]) { /* fetch + map */ }
```

```typescript
// apps/web/app/(admin)/admin/actions.ts
const parseSectionRows = (formData: FormData): AdminContentSection[] => {
  const rowCount = parsePositiveNumber(formData.get('rowCount'), 'rowCount');
  const sections: AdminContentSection[] = [];

  for (let index = 0; index < rowCount; index += 1) {
    const type = String(formData.get(`section_type_${index}`) ?? '').trim();
    const title = String(formData.get(`section_title_${index}`) ?? '').trim();
    const items = String(formData.get(`section_items_${index}`) ?? '')
      .split(/\r?\n/)
      .map((item) => item.trim())
      .filter(Boolean);

    if (!type && !title && items.length === 0) {
      continue;
    }

    if (!type || !title || items.length === 0) {
      throw new Error('content section row is invalid');
    }

    sections.push({ type, title, items });
  }

  return sections;
};

export async function updateSchoolSectionsAction(formData: FormData): Promise<void> {
  const slug = parseRequiredSlug(formData.get('slug'));
  const sections = parseSectionRows(formData);
  await updateSchoolSections(slug, sections);
  revalidatePath('/admin');
  revalidatePath('/');
  revalidatePath(`/schools/${slug}`);
}

export async function updateMajorSectionsAction(formData: FormData): Promise<void> {
  const slug = parseRequiredSlug(formData.get('slug'));
  const sections = parseSectionRows(formData);
  await updateMajorSections(slug, sections);
  revalidatePath('/admin');
  revalidatePath('/');
  revalidatePath(`/majors/${slug}`);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-content-sections-api.test.ts`
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/web/lib/admin-content-sections-api.ts apps/web/app/(admin)/admin/actions.ts tests/admin-content-sections-api.test.ts
git commit -m "feat(web): add admin content sections client"
```

### Task 3: Render content sections editors in admin

**Files:**
- Create: `apps/web/tests/admin-content-sections.test.tsx`
- Modify: `apps/web/app/(admin)/admin/page.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`
- Modify: `apps/web/tests/admin-page.test.tsx`
- Modify: `apps/web/tests/admin-ranking-reference.test.tsx`
- Modify: `apps/web/tests/admin-missing-image-filter.test.tsx`
- Modify: `apps/web/tests/admin-scheduled-missing-image-filter.test.tsx`

- [ ] **Step 1: Write the failing admin UI test**

```typescript
import { render, screen } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

const { listContentSectionsMock } = vi.hoisted(() => ({
  listContentSectionsMock: vi.fn(),
}));

vi.mock('../lib/admin-content-sections-api', () => ({
  listContentSections: listContentSectionsMock,
}));

test('renders school and major content section editors in admin', async () => {
  listContentSectionsMock.mockResolvedValue({
    schools: [
      {
        slug: 'southeast-university',
        name: '东南大学',
        sections: [{ type: 'highlights', title: '学校亮点', items: ['资源密集'] }],
      },
    ],
    majors: [
      {
        slug: 'clinical-medicine',
        name: '临床医学',
        sections: [{ type: 'fit_for', title: '适合人群', items: ['接受长周期培养'] }],
      },
    ],
  });

  render(await AdminPage({}));

  expect(screen.getByRole('heading', { name: '学校正文编辑' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '专业正文编辑' })).toBeInTheDocument();
  expect(screen.getByDisplayValue('学校亮点')).toBeInTheDocument();
  expect(screen.getByDisplayValue('highlights')).toBeInTheDocument();
  expect(screen.getByDisplayValue('资源密集')).toBeInTheDocument();
  expect(screen.getAllByRole('button', { name: '保存正文' })).toHaveLength(2);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-content-sections.test.tsx`
Expected: `FAIL` because admin page and shell do not render the new sections yet.

- [ ] **Step 3: Write the minimal page and shell implementation**

```typescript
// apps/web/app/(admin)/admin/page.tsx
let sectionSchools: AdminContentSectionsEntity[] = [];
let sectionMajors: AdminContentSectionsEntity[] = [];
let contentSectionError: string | undefined;

try {
  const contentSections = await listContentSections();
  sectionSchools = contentSections.schools;
  sectionMajors = contentSections.majors;
} catch {
  contentSectionError = '正文内容加载失败，请稍后重试';
}

<DashboardShell
  sectionSchools={sectionSchools}
  sectionMajors={sectionMajors}
  contentSectionError={contentSectionError}
  updateSchoolSectionsAction={updateSchoolSectionsAction}
  updateMajorSectionsAction={updateMajorSectionsAction}
/>
```

```tsx
// apps/web/components/admin/dashboard-shell.tsx
function ContentSectionsForm({ entity, action }: { ... }) {
  const rows = [
    ...entity.sections,
    { type: '', title: '', items: [] },
  ];

  return (
    <form action={action}>
      <input type="hidden" name="slug" value={entity.slug} />
      <input type="hidden" name="rowCount" value={rows.length} />
      <h3>{entity.name}</h3>
      <p>{entity.slug}</p>
      {rows.map((row, index) => (
        <fieldset key={`${entity.slug}-${index}`}>
          <label>
            类型
            <input name={`section_type_${index}`} defaultValue={row.type} />
          </label>
          <label>
            标题
            <input name={`section_title_${index}`} defaultValue={row.title} />
          </label>
          <label>
            条目
            <textarea
              name={`section_items_${index}`}
              defaultValue={row.items.join('\n')}
            />
          </label>
        </fieldset>
      ))}
      <button type="submit">保存正文</button>
    </form>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-content-sections.test.tsx`
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/web/app/(admin)/admin/page.tsx apps/web/components/admin/dashboard-shell.tsx apps/web/tests/admin-content-sections.test.tsx apps/web/tests/admin-page.test.tsx apps/web/tests/admin-ranking-reference.test.tsx apps/web/tests/admin-missing-image-filter.test.tsx apps/web/tests/admin-scheduled-missing-image-filter.test.tsx
git commit -m "feat(web): edit content sections in admin"
```

### Task 4: Verify full content-sections integration

**Files:**
- Test: `apps/api/tests/test_admin_content_sections_api.py`
- Test: `apps/web/tests/admin-content-sections.test.tsx`
- Test: `apps/web/tests/admin-page.test.tsx`
- Test: `apps/web/tests/admin-ranking-reference.test.tsx`
- Test: `apps/web/tests/admin-missing-image-filter.test.tsx`
- Test: `apps/web/tests/admin-scheduled-missing-image-filter.test.tsx`

- [ ] **Step 1: Run focused API regression**

Run: `python -m pytest tests/test_admin_content_sections_api.py -v`
Expected: `3 passed`

- [ ] **Step 2: Run focused web admin regression**

Run: `node .\node_modules\vitest\vitest.mjs run tests/admin-content-sections.test.tsx tests/admin-page.test.tsx tests/admin-ranking-reference.test.tsx tests/admin-missing-image-filter.test.tsx tests/admin-scheduled-missing-image-filter.test.tsx`
Expected: all selected tests pass

- [ ] **Step 3: Run full web test suite**

Run: `node .\node_modules\vitest\vitest.mjs run`
Expected: all web tests pass

- [ ] **Step 4: Run production build**

Run: `node .\node_modules\next\dist\bin\next build`
Expected: build succeeds; the known Windows SWC block warning may still appear while wasm fallback succeeds

- [ ] **Step 5: Run full API test suite**

Run: `python -m pytest`
Expected: all API tests pass; the existing FastAPI `on_event` deprecation warnings may still appear
