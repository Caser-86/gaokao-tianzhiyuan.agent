# Featured Content Rotation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add independently configurable school and major rotation rules so the public homepage can rotate featured entities on a controllable day-based cadence.

**Architecture:** Extend `data/featured-content.json` with a `rotation` section and centralize all rule validation and window calculation inside `apps/api/app/services/featured_content.py`. Keep the public API surface unchanged so the homepage continues to consume the normal list endpoints, while the admin API and admin shell grow the minimal form controls needed to manage school and major rotation rules.

**Tech Stack:** FastAPI, Python, Next.js 15, React 19, TypeScript, Vitest, Testing Library, Pytest

---

### Task 1: Add rotation config storage and admin API coverage

**Files:**
- Modify: `data/featured-content.json`
- Modify: `apps/api/app/services/featured_content.py`
- Modify: `apps/api/app/routers/admin.py`
- Modify: `apps/api/tests/test_admin_api.py`

- [ ] **Step 1: Write the failing test**

Extend `apps/api/tests/test_admin_api.py` so featured-content responses include rotation rules and new rotation update endpoints persist validated configuration.

```python
def test_featured_content_endpoint_includes_rotation_rules(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client

    response = client.get(
        "/api/admin/featured-content",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json()["rotation"] == {
        "schools": {
            "enabled": True,
            "frequency_days": 1,
            "window_size": 1,
            "ordered_slugs": [
                "southeast-university",
                "west-china-medical-center",
            ],
        },
        "majors": {
            "enabled": True,
            "frequency_days": 1,
            "window_size": 1,
            "ordered_slugs": [
                "clinical-medicine",
                "computer-science",
            ],
        },
    }
```

```python
def test_update_school_rotation_rule_persists_configuration(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client

    response = client.post(
        "/api/admin/featured-content/rotation/schools",
        headers={"x-admin-token": settings.admin_token},
        json={
            "enabled": True,
            "frequency_days": 2,
            "window_size": 2,
            "ordered_slugs": [
                "west-china-medical-center",
                "southeast-university",
            ],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "enabled": True,
        "frequency_days": 2,
        "window_size": 2,
        "ordered_slugs": [
            "west-china-medical-center",
            "southeast-university",
        ],
    }
    saved = json.loads(featured_content_file.read_text(encoding="utf-8"))
    assert saved["rotation"]["schools"]["frequency_days"] == 2
```

```python
def test_update_major_rotation_rule_rejects_unknown_slug(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client

    response = client.post(
        "/api/admin/featured-content/rotation/majors",
        headers={"x-admin-token": settings.admin_token},
        json={
            "enabled": True,
            "frequency_days": 1,
            "window_size": 1,
            "ordered_slugs": ["missing-major"],
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "featured rotation slug not found"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_admin_api.py -v`

Expected: FAIL because featured-content responses do not yet include `rotation` and the admin router does not expose rotation update endpoints.

- [ ] **Step 3: Write minimal implementation**

Extend `data/featured-content.json` with seed rotation rules:

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
  ],
  "rotation": {
    "schools": {
      "enabled": true,
      "frequency_days": 1,
      "window_size": 1,
      "ordered_slugs": [
        "southeast-university",
        "west-china-medical-center"
      ]
    },
    "majors": {
      "enabled": true,
      "frequency_days": 1,
      "window_size": 1,
      "ordered_slugs": [
        "clinical-medicine",
        "computer-science"
      ]
    }
  }
}
```

Add a shared rotation-rule shape and read/write helpers in `apps/api/app/services/featured_content.py`:

```python
from datetime import date

ROTATION_ANCHOR_DATE = date(2026, 4, 14)
DEFAULT_ROTATION_RULE = {
    "enabled": False,
    "frequency_days": 1,
    "window_size": 1,
    "ordered_slugs": [],
}


def _normalize_rotation(payload: dict[str, Any]) -> dict[str, Any]:
    rotation = payload.setdefault("rotation", {})
    rotation.setdefault("schools", DEFAULT_ROTATION_RULE.copy())
    rotation.setdefault("majors", DEFAULT_ROTATION_RULE.copy())
    return rotation


def _validate_rotation_rule(entity_key: str, ordered_slugs: list[str]) -> None:
    catalog_slugs = {item["slug"] for item in _catalog_entities(entity_key)}
    if len(ordered_slugs) != len(set(ordered_slugs)):
        raise ValueError("featured rotation contains duplicate slugs")
    for slug in ordered_slugs:
        if slug not in catalog_slugs:
            raise KeyError(slug)
```

```python
def update_rotation_rule(
    rotation_key: str,
    *,
    enabled: bool,
    frequency_days: int,
    window_size: int,
    ordered_slugs: list[str],
) -> dict[str, Any]:
    if frequency_days < 1 or window_size < 1:
        raise ValueError("featured rotation values must be positive")

    entity_key = "schools" if rotation_key == "schools" else "majors"
    _validate_rotation_rule(entity_key, ordered_slugs)

    payload = _read_featured_content()
    rotation = _normalize_rotation(payload)
    rotation[rotation_key] = {
        "enabled": enabled,
        "frequency_days": frequency_days,
        "window_size": window_size,
        "ordered_slugs": ordered_slugs,
    }
    _write_featured_content(payload)
    return rotation[rotation_key]
```

Make `list_featured_content()` include the normalized `rotation` payload:

```python
def list_featured_content() -> dict[str, Any]:
    payload = _read_featured_content()
    rotation = _normalize_rotation(payload)
    ...
    return {
        "schools": schools,
        "majors": majors,
        "rotation": rotation,
    }
```

Add router models and handlers in `apps/api/app/routers/admin.py`:

```python
class FeaturedRotationRuleResponse(SQLModel):
    enabled: bool
    frequency_days: int
    window_size: int
    ordered_slugs: list[str]


class FeaturedRotationRuleRequest(SQLModel):
    enabled: bool
    frequency_days: int
    window_size: int
    ordered_slugs: list[str]


class FeaturedContentResponse(SQLModel):
    schools: list[FeaturedSchoolConfigResponse]
    majors: list[FeaturedMajorConfigResponse]
    rotation: dict[str, FeaturedRotationRuleResponse]
```

```python
@router.post(
    "/featured-content/rotation/schools",
    response_model=FeaturedRotationRuleResponse,
)
def update_school_rotation_rule(
    payload: FeaturedRotationRuleRequest,
    _authorized: None = Depends(require_admin),
) -> FeaturedRotationRuleResponse:
    try:
        updated = update_rotation_rule(
            "schools",
            enabled=payload.enabled,
            frequency_days=payload.frequency_days,
            window_size=payload.window_size,
            ordered_slugs=payload.ordered_slugs,
        )
    except KeyError as exc:
        raise HTTPException(status_code=422, detail="featured rotation slug not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return FeaturedRotationRuleResponse(**updated)
```

Mirror the same handler for majors.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_admin_api.py -v`

Expected: PASS with featured-content responses now exposing rotation rules and school or major rotation updates persisting through admin endpoints.

- [ ] **Step 5: Commit**

```bash
git add data/featured-content.json apps/api/app/services/featured_content.py apps/api/app/routers/admin.py apps/api/tests/test_admin_api.py
git commit -m "feat(api): add featured content rotation admin endpoints"
```

### Task 2: Apply rotation rules to public school and major lists

**Files:**
- Modify: `apps/api/app/services/featured_content.py`
- Modify: `apps/api/app/services/catalog.py`
- Modify: `apps/api/tests/test_public_catalog_api.py`

- [ ] **Step 1: Write the failing test**

Extend `apps/api/tests/test_public_catalog_api.py` so public list responses return only the current rotation window when automatic rotation is enabled, and fall back to manual featured lists when it is disabled.

```python
def test_list_schools_returns_current_rotation_window(tmp_path, monkeypatch) -> None:
    featured_content_path = tmp_path / "featured-content.json"
    featured_content_path.write_text(
        json.dumps(
            {
                "schools": [
                    {"slug": "southeast-university", "is_featured": True, "hero_image_url": ""},
                    {"slug": "west-china-medical-center", "is_featured": True, "hero_image_url": ""},
                ],
                "majors": [
                    {"slug": "clinical-medicine", "is_featured": True},
                    {"slug": "computer-science", "is_featured": True},
                ],
                "rotation": {
                    "schools": {
                        "enabled": True,
                        "frequency_days": 1,
                        "window_size": 1,
                        "ordered_slugs": [
                            "west-china-medical-center",
                            "southeast-university",
                        ],
                    },
                    "majors": {
                        "enabled": False,
                        "frequency_days": 1,
                        "window_size": 1,
                        "ordered_slugs": [],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(featured_content_service, "FEATURED_CONTENT_PATH", featured_content_path)
    monkeypatch.setattr(featured_content_service, "ROTATION_ANCHOR_DATE", date.today())

    response = client.get("/api/public/schools")

    assert response.status_code == 200
    assert [item["slug"] for item in response.json()["items"]] == ["west-china-medical-center"]
```

```python
def test_list_majors_falls_back_to_all_featured_items_when_rotation_disabled(
    tmp_path,
    monkeypatch,
) -> None:
    featured_content_path = tmp_path / "featured-content.json"
    _write_featured_content(featured_content_path)
    monkeypatch.setattr(featured_content_service, "FEATURED_CONTENT_PATH", featured_content_path)

    response = client.get("/api/public/majors")

    assert response.status_code == 200
    assert {item["slug"] for item in response.json()["items"]} == {
        "clinical-medicine",
        "computer-science",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_public_catalog_api.py -v`

Expected: FAIL because public lists still return every manually featured entity without applying a rotation window.

- [ ] **Step 3: Write minimal implementation**

Add helpers in `apps/api/app/services/featured_content.py` to compute the current visible school and major configs:

```python
from datetime import date


def _current_rotation_window(
    entries: list[dict[str, Any]],
    rule: dict[str, Any],
    *,
    today: date | None = None,
) -> list[dict[str, Any]]:
    eligible = [item for item in entries if item.get("is_featured")]
    if not rule.get("enabled"):
        return eligible

    ordered = [
        next(item for item in eligible if item["slug"] == slug)
        for slug in rule.get("ordered_slugs", [])
        if any(item["slug"] == slug for item in eligible)
    ]
    if not ordered:
        return eligible

    today = today or date.today()
    step = ((today - ROTATION_ANCHOR_DATE).days // rule["frequency_days"]) % len(ordered)
    window_size = min(rule["window_size"], len(ordered))
    return [ordered[(step + offset) % len(ordered)] for offset in range(window_size)]
```

```python
def list_current_featured_schools() -> list[dict[str, Any]]:
    payload = list_featured_content()
    return _current_rotation_window(payload["schools"], payload["rotation"]["schools"])


def list_current_featured_majors() -> list[dict[str, Any]]:
    payload = list_featured_content()
    return _current_rotation_window(payload["majors"], payload["rotation"]["majors"])
```

Update `apps/api/app/services/catalog.py` to consume the computed current window:

```python
from .featured_content import (
    list_current_featured_majors,
    list_current_featured_schools,
)


def list_schools(*, region: str | None = None, keyword: str | None = None) -> dict[str, Any]:
    schools = load_catalog()["schools"]
    featured_schools = {
        school["slug"]: school
        for school in list_current_featured_schools()
    }
    ...
```

```python
def list_majors() -> dict[str, Any]:
    majors = load_catalog()["majors"]
    featured_majors = {
        major["slug"]
        for major in list_current_featured_majors()
    }
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_public_catalog_api.py -v`

Expected: PASS with public list endpoints now returning only the current rotation window when automatic rotation is enabled, while still falling back to manual featured items otherwise.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/services/featured_content.py apps/api/app/services/catalog.py apps/api/tests/test_public_catalog_api.py
git commit -m "feat(api): apply featured content rotation to public lists"
```

### Task 3: Add admin-side rotation rule editing UI and actions

**Files:**
- Modify: `apps/web/lib/admin-featured-content-api.ts`
- Modify: `apps/web/app/(admin)/admin/actions.ts`
- Modify: `apps/web/app/(admin)/admin/page.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`
- Modify: `apps/web/tests/admin-review-api.test.ts`
- Modify: `apps/web/tests/admin-page.test.tsx`

- [ ] **Step 1: Write the failing test**

Extend the admin client and page tests so the admin page renders school and major rotation forms and the actions post the expected payload.

```ts
test('listFeaturedContent maps rotation rules from the admin api', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      schools: [],
      majors: [],
      rotation: {
        schools: {
          enabled: true,
          frequency_days: 1,
          window_size: 2,
          ordered_slugs: ['southeast-university', 'west-china-medical-center'],
        },
        majors: {
          enabled: false,
          frequency_days: 3,
          window_size: 4,
          ordered_slugs: ['clinical-medicine'],
        },
      },
    }),
  });

  const payload = await listFeaturedContent();

  expect(payload.rotation.schools).toEqual({
    enabled: true,
    frequencyDays: 1,
    windowSize: 2,
    orderedSlugs: ['southeast-university', 'west-china-medical-center'],
  });
})
```

```ts
test('updateSchoolRotationAction posts rotation configuration', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      enabled: true,
      frequency_days: 2,
      window_size: 3,
      ordered_slugs: ['west-china-medical-center', 'southeast-university'],
    }),
  });

  const formData = new FormData();
  formData.set('enabled', 'on');
  formData.set('frequencyDays', '2');
  formData.set('windowSize', '3');
  formData.set('orderedSlugs', 'west-china-medical-center\nsoutheast-university');

  await updateSchoolRotationAction(formData);

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/admin/featured-content/rotation/schools',
    expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        enabled: true,
        frequency_days: 2,
        window_size: 3,
        ordered_slugs: ['west-china-medical-center', 'southeast-university'],
      }),
    }),
  );
});
```

```tsx
test('renders school and major rotation forms', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [],
    majors: [],
    rotation: {
      schools: {
        enabled: true,
        frequencyDays: 1,
        windowSize: 2,
        orderedSlugs: ['southeast-university', 'west-china-medical-center'],
      },
      majors: {
        enabled: false,
        frequencyDays: 3,
        windowSize: 4,
        orderedSlugs: ['clinical-medicine'],
      },
    },
  });

  render(await AdminPage());

  expect(screen.getByRole('heading', { name: '学校轮换规则' })).toBeInTheDocument();
  expect(screen.getByDisplayValue('1')).toBeInTheDocument();
  expect(screen.getByDisplayValue('southeast-university\nwest-china-medical-center')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '专业轮换规则' })).toBeInTheDocument();
  expect(screen.getByDisplayValue('clinical-medicine')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-review-api.test.ts tests/admin-page.test.tsx`

Expected: FAIL because the admin client, server actions, and admin page do not yet expose rotation configuration.

- [ ] **Step 3: Write minimal implementation**

Add a rotation-rule type and API helpers in `apps/web/lib/admin-featured-content-api.ts`:

```ts
export type AdminRotationRule = {
  enabled: boolean;
  frequencyDays: number;
  windowSize: number;
  orderedSlugs: string[];
};

export type AdminFeaturedContent = {
  schools: AdminFeaturedSchool[];
  majors: AdminFeaturedMajor[];
  rotation: {
    schools: AdminRotationRule;
    majors: AdminRotationRule;
  };
};
```

```ts
const mapRotationRule = (item: {
  enabled: boolean;
  frequency_days: number;
  window_size: number;
  ordered_slugs: string[];
}): AdminRotationRule => ({
  enabled: item.enabled,
  frequencyDays: item.frequency_days,
  windowSize: item.window_size,
  orderedSlugs: item.ordered_slugs,
});
```

```ts
export async function updateSchoolRotationRule(rule: AdminRotationRule): Promise<AdminRotationRule> {
  const response = await fetch(`${getApiUrl()}/api/admin/featured-content/rotation/schools`, {
    method: 'POST',
    headers: buildHeaders('application/json'),
    body: JSON.stringify({
      enabled: rule.enabled,
      frequency_days: rule.frequencyDays,
      window_size: rule.windowSize,
      ordered_slugs: rule.orderedSlugs,
    }),
  });
  return mapRotationRule(await parseResponse(response));
}
```

Mirror the same helper for majors.

Extend `apps/web/app/(admin)/admin/actions.ts`:

```ts
const parseOrderedSlugs = (value: FormDataEntryValue | null): string[] =>
  String(value ?? '')
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);

export async function updateSchoolRotationAction(formData: FormData): Promise<void> {
  try {
    await updateSchoolRotationRule({
      enabled: formData.get('enabled') === 'on',
      frequencyDays: Number.parseInt(String(formData.get('frequencyDays') ?? '1'), 10),
      windowSize: Number.parseInt(String(formData.get('windowSize') ?? '1'), 10),
      orderedSlugs: parseOrderedSlugs(formData.get('orderedSlugs')),
    });
    revalidatePath('/admin');
    revalidatePath('/');
  } catch {
    return;
  }
}
```

Load and pass rotation state through `apps/web/app/(admin)/admin/page.tsx`:

```tsx
import type {
  AdminFeaturedContent,
  AdminFeaturedMajor,
  AdminFeaturedSchool,
  AdminRotationRule,
} from '../../../lib/admin-featured-content-api';

...
  let schoolRotation: AdminRotationRule = {
    enabled: false,
    frequencyDays: 1,
    windowSize: 1,
    orderedSlugs: [],
  };
  let majorRotation: AdminRotationRule = {
    enabled: false,
    frequencyDays: 1,
    windowSize: 1,
    orderedSlugs: [],
  };
...
    schoolRotation = featuredContent.rotation.schools;
    majorRotation = featuredContent.rotation.majors;
...
      schoolRotation={schoolRotation}
      majorRotation={majorRotation}
      updateSchoolRotationAction={updateSchoolRotationAction}
      updateMajorRotationAction={updateMajorRotationAction}
```

Render the new forms in `apps/web/components/admin/dashboard-shell.tsx`:

```tsx
      <section aria-labelledby="school-rotation-heading">
        <h2 id="school-rotation-heading">学校轮换规则</h2>
        <form action={updateSchoolRotationAction}>
          <label>
            <input type="checkbox" name="enabled" defaultChecked={schoolRotation.enabled} />
            启用自动轮换
          </label>
          <input type="number" name="frequencyDays" min={1} defaultValue={schoolRotation.frequencyDays} />
          <input type="number" name="windowSize" min={1} defaultValue={schoolRotation.windowSize} />
          <textarea
            name="orderedSlugs"
            defaultValue={schoolRotation.orderedSlugs.join('\n')}
            aria-label="学校轮换顺序"
          />
          <button type="submit">保存轮换规则</button>
        </form>
      </section>
```

Mirror the same structure for majors.

- [ ] **Step 4: Run test to verify it passes**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-review-api.test.ts tests/admin-page.test.tsx`

Expected: PASS with rotation rules now flowing through the admin client, actions, and admin shell.

- [ ] **Step 5: Commit**

```bash
git add apps/web/lib/admin-featured-content-api.ts apps/web/app/(admin)/admin/actions.ts apps/web/app/(admin)/admin/page.tsx apps/web/components/admin/dashboard-shell.tsx apps/web/tests/admin-review-api.test.ts apps/web/tests/admin-page.test.tsx
git commit -m "feat(web): add featured content rotation controls"
```

### Task 4: Run final verification

**Files:**
- Test: `apps/api/tests/test_admin_api.py`
- Test: `apps/api/tests/test_public_catalog_api.py`
- Test: `apps/web/tests/admin-review-api.test.ts`
- Test: `apps/web/tests/admin-page.test.tsx`
- Test: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Run focused API verification**

Run: `python -m pytest tests/test_admin_api.py tests/test_public_catalog_api.py -v`

Expected: PASS

- [ ] **Step 2: Run focused admin Web verification**

Run: `node ./node_modules/vitest/vitest.mjs run tests/admin-review-api.test.ts tests/admin-page.test.tsx`

Expected: PASS

- [ ] **Step 3: Run homepage regression coverage**

Run: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`

Expected: PASS with the homepage continuing to consume the public API without any browser-side rotation logic

- [ ] **Step 4: Run full Web test suite**

Run: `node ./node_modules/vitest/vitest.mjs run`

Expected: PASS with all `apps/web` tests green

- [ ] **Step 5: Run production build**

Run: `node ./node_modules/next/dist/bin/next build`

Expected: PASS with a successful Next.js production build

- [ ] **Step 6: Review git status**

Run: `git status --short`

Expected: clean working tree after the intended commits, or only the plan file before its own commit
