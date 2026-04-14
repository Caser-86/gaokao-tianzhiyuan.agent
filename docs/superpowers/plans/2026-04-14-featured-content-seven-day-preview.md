# Featured Content Seven-Day Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the admin featured-content payload and admin page so operators can see today's preview plus the next seven days of featured-school and featured-major rotation results.

**Architecture:** Reuse the existing API-side featured-content rotation helper for arbitrary dates, then expand the admin featured-content response so `preview` contains both `today` and a seven-day `schedule`. The web admin data client will map the nested preview payload into camelCase types, and the admin dashboard will render a text-first seven-day schedule under the existing today preview sections.

**Tech Stack:** FastAPI, SQLModel response models, Next.js App Router, TypeScript, Vitest, Testing Library

---

### Task 1: Add seven-day schedule data to the admin featured-content API

**Files:**
- Modify: `apps/api/tests/test_admin_api.py`
- Modify: `apps/api/app/services/featured_content.py`
- Modify: `apps/api/app/routers/admin.py`

- [ ] **Step 1: Write the failing API tests**

Update the imports in `apps/api/tests/test_admin_api.py` to include `date`:

```python
from datetime import date, datetime, timedelta, timezone
```

Replace the existing preview assertion with a nested `today` assertion and add a second test for the seven-day schedule:

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
    assert response.json()["preview"]["today"] == {
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


def test_featured_content_endpoint_returns_seven_day_schedule(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client
    today = date.today()

    response = client.get(
        "/api/admin/featured-content",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    schedule = response.json()["preview"]["schedule"]

    assert len(schedule) == 7
    assert schedule[0]["date"] == today.isoformat()
    assert schedule[0]["schools"] == [
        {
            "slug": "southeast-university",
            "name": "东南大学",
        }
    ]
    assert schedule[0]["majors"] == [
        {
            "slug": "clinical-medicine",
            "name": "临床医学",
        }
    ]
    assert schedule[1]["date"] == (today + timedelta(days=1)).isoformat()
    assert schedule[1]["schools"] == [
        {
            "slug": "west-china-medical-center",
            "name": "华西医学中心",
        }
    ]
    assert schedule[1]["majors"] == [
        {
            "slug": "computer-science",
            "name": "计算机科学与技术",
        }
    ]
```

- [ ] **Step 2: Run the focused API tests to verify they fail**

Run:

```powershell
python -m pytest tests/test_admin_api.py::test_featured_content_endpoint_returns_today_preview tests/test_admin_api.py::test_featured_content_endpoint_returns_seven_day_schedule -v
```

Expected: `FAIL` because the current API returns a flat `preview` object and has no `schedule`.

- [ ] **Step 3: Write the minimal API implementation**

Update `apps/api/app/services/featured_content.py` so preview generation supports arbitrary dates and seven-day schedules:

```python
from datetime import date, timedelta

WEEKDAY_LABELS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _preview_entry_for_date(
    payload: dict[str, Any],
    target_date: date,
) -> dict[str, Any]:
    schools = _current_rotation_window(
        payload["schools"],
        payload["rotation"]["schools"],
        today=target_date,
    )
    majors = _current_rotation_window(
        payload["majors"],
        payload["rotation"]["majors"],
        today=target_date,
    )
    return {
        "date": target_date.isoformat(),
        "weekday": WEEKDAY_LABELS[target_date.weekday()],
        "schools": _preview_items(schools),
        "majors": _preview_items(majors),
    }


def build_featured_content_preview() -> dict[str, Any]:
    payload = list_featured_content()
    today = date.today()

    today_entry = _preview_entry_for_date(payload, today)
    schedule = [
        _preview_entry_for_date(payload, today + timedelta(days=offset))
        for offset in range(7)
    ]

    return {
        "today": {
            "schools": today_entry["schools"],
            "majors": today_entry["majors"],
        },
        "schedule": schedule,
    }
```

Update `apps/api/app/routers/admin.py` to expand the preview response models:

```python
class FeaturedPreviewDayResponse(SQLModel):
    date: str
    weekday: str
    schools: list[FeaturedPreviewItemResponse]
    majors: list[FeaturedPreviewItemResponse]


class FeaturedTodayPreviewResponse(SQLModel):
    schools: list[FeaturedPreviewItemResponse]
    majors: list[FeaturedPreviewItemResponse]


class FeaturedContentPreviewResponse(SQLModel):
    today: FeaturedTodayPreviewResponse
    schedule: list[FeaturedPreviewDayResponse]
```

Update the `preview` mapping in `get_featured_content()`:

```python
        preview=FeaturedContentPreviewResponse(
            today=FeaturedTodayPreviewResponse(
                schools=[
                    FeaturedPreviewItemResponse(**school)
                    for school in preview["today"]["schools"]
                ],
                majors=[
                    FeaturedPreviewItemResponse(**major)
                    for major in preview["today"]["majors"]
                ],
            ),
            schedule=[
                FeaturedPreviewDayResponse(
                    date=day["date"],
                    weekday=day["weekday"],
                    schools=[
                        FeaturedPreviewItemResponse(**school)
                        for school in day["schools"]
                    ],
                    majors=[
                        FeaturedPreviewItemResponse(**major)
                        for major in day["majors"]
                    ],
                )
                for day in preview["schedule"]
            ],
        ),
```

- [ ] **Step 4: Run the focused API tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_admin_api.py::test_featured_content_endpoint_returns_today_preview tests/test_admin_api.py::test_featured_content_endpoint_returns_seven_day_schedule -v
```

Expected: `PASS`

- [ ] **Step 5: Commit the API schedule change**

Run:

```powershell
git add apps/api/tests/test_admin_api.py apps/api/app/services/featured_content.py apps/api/app/routers/admin.py
git commit -m "feat(api): add featured content seven-day schedule"
```

### Task 2: Map the seven-day preview in the web admin data client

**Files:**
- Modify: `apps/web/tests/admin-review-api.test.ts`
- Modify: `apps/web/lib/admin-featured-content-api.ts`

- [ ] **Step 1: Write the failing web data-client test**

Update the mocked API response in `apps/web/tests/admin-review-api.test.ts`:

```ts
      preview: {
        today: {
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
        schedule: [
          {
            date: '2026-04-14',
            weekday: '周二',
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
          {
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
          },
        ],
      },
```

Replace the existing preview expectation with:

```ts
  expect(payload.preview.today).toEqual({
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
  expect(payload.preview.schedule).toEqual([
    {
      date: '2026-04-14',
      weekday: '周二',
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
    {
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
    },
  ]);
```

- [ ] **Step 2: Run the focused web data-client test to verify it fails**

Run:

```powershell
node .\node_modules\vitest\vitest.mjs run tests/admin-review-api.test.ts
```

Expected: `FAIL` because `listFeaturedContent` only maps a flat `preview`.

- [ ] **Step 3: Write the minimal web data-client implementation**

Update `apps/web/lib/admin-featured-content-api.ts` to add schedule-aware preview types:

```ts
export type AdminFeaturedPreviewDay = {
  date: string;
  weekday: string;
  schools: AdminFeaturedPreviewItem[];
  majors: AdminFeaturedPreviewItem[];
};
```

Update `AdminFeaturedContent`:

```ts
export type AdminFeaturedContent = {
  schools: AdminFeaturedSchool[];
  majors: AdminFeaturedMajor[];
  rotation: {
    schools: AdminRotationRule;
    majors: AdminRotationRule;
  };
  preview: {
    today: {
      schools: AdminFeaturedPreviewItem[];
      majors: AdminFeaturedPreviewItem[];
    };
    schedule: AdminFeaturedPreviewDay[];
  };
};
```

Update the parsed response type and mapping:

```ts
    preview?: {
      today?: {
        schools?: Array<{
          slug: string;
          name: string;
        }>;
        majors?: Array<{
          slug: string;
          name: string;
        }>;
      };
      schedule?: Array<{
        date: string;
        weekday: string;
        schools?: Array<{
          slug: string;
          name: string;
        }>;
        majors?: Array<{
          slug: string;
          name: string;
        }>;
      }>;
    };

    preview: {
      today: {
        schools: payload.preview?.today?.schools ?? [],
        majors: payload.preview?.today?.majors ?? [],
      },
      schedule: (payload.preview?.schedule ?? []).map((day) => ({
        date: day.date,
        weekday: day.weekday,
        schools: day.schools ?? [],
        majors: day.majors ?? [],
      })),
    },
```

- [ ] **Step 4: Run the focused web data-client test to verify it passes**

Run:

```powershell
node .\node_modules\vitest\vitest.mjs run tests/admin-review-api.test.ts
```

Expected: `PASS`

- [ ] **Step 5: Commit the web data-client schedule change**

Run:

```powershell
git add apps/web/tests/admin-review-api.test.ts apps/web/lib/admin-featured-content-api.ts
git commit -m "feat(web): map featured content seven-day schedule"
```

### Task 3: Render the seven-day schedule in the admin page

**Files:**
- Modify: `apps/web/tests/admin-page.test.tsx`
- Modify: `apps/web/tests/admin-dashboard.test.tsx`
- Modify: `apps/web/app/(admin)/admin/page.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`

- [ ] **Step 1: Write the failing page and dashboard tests**

Update the mocked preview in `apps/web/tests/admin-page.test.tsx`:

```ts
    preview: {
      today: {
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
      schedule: [
        {
          date: '2026-04-14',
          weekday: '周二',
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
        {
          date: '2026-04-15',
          weekday: '周三',
          schools: [],
          majors: [],
        },
      ],
    },
```

Add these expectations to the main page test:

```tsx
  expect(screen.getByRole('heading', { name: '未来 7 天轮换预览' })).toBeInTheDocument();
  expect(screen.getByText('2026-04-14')).toBeInTheDocument();
  expect(screen.getByText('周二')).toBeInTheDocument();
  expect(screen.getByText('2026-04-15')).toBeInTheDocument();
  expect(screen.getByText('周三')).toBeInTheDocument();
```

Add a page-level empty-schedule test:

```tsx
test('renders per-day empty states in the seven-day schedule', async () => {
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
      today: {
        schools: [],
        majors: [],
      },
      schedule: [
        {
          date: '2026-04-14',
          weekday: '周二',
          schools: [],
          majors: [],
        },
      ],
    },
  });

  render(await AdminPage());

  expect(screen.getByText('当天没有可展示学校')).toBeInTheDocument();
  expect(screen.getByText('当天没有可展示专业')).toBeInTheDocument();
});
```

Update `apps/web/tests/admin-dashboard.test.tsx` with a seven-day preview fixture:

```tsx
const schedulePreview = [
  {
    date: '2026-04-14',
    weekday: '周二',
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
];
```

Pass it into `DashboardShell`:

```tsx
      featuredSchedulePreview={schedulePreview}
```

Add these expectations:

```tsx
  expect(screen.getByRole('heading', { name: '未来 7 天轮换预览' })).toBeInTheDocument();
  expect(screen.getByText('2026-04-14')).toBeInTheDocument();
  expect(screen.getByText('周二')).toBeInTheDocument();
```

- [ ] **Step 2: Run the focused page tests to verify they fail**

Run:

```powershell
node .\node_modules\vitest\vitest.mjs run tests/admin-page.test.tsx tests/admin-dashboard.test.tsx
```

Expected: `FAIL` because the page and dashboard do not yet accept or render a seven-day schedule.

- [ ] **Step 3: Write the minimal admin page implementation**

Update the imports in `apps/web/app/(admin)/admin/page.tsx`:

```tsx
import {
  type AdminFeaturedMajor,
  type AdminFeaturedPreviewDay,
  type AdminFeaturedPreviewItem,
  type AdminFeaturedSchool,
  type AdminRotationRule,
  listFeaturedContent,
} from '../../../lib/admin-featured-content-api';
```

Add schedule state and map the nested preview:

```tsx
  let featuredSchedulePreview: AdminFeaturedPreviewDay[] = [];

    featuredSchoolPreview = featuredContent.preview.today.schools;
    featuredMajorPreview = featuredContent.preview.today.majors;
    featuredSchedulePreview = featuredContent.preview.schedule;
```

Pass the new prop into `DashboardShell`:

```tsx
      featuredSchedulePreview={featuredSchedulePreview}
```

Update the imports in `apps/web/components/admin/dashboard-shell.tsx`:

```tsx
import type {
  AdminFeaturedMajor,
  AdminFeaturedPreviewDay,
  AdminFeaturedPreviewItem,
  AdminFeaturedSchool,
  AdminRotationRule,
} from '../../lib/admin-featured-content-api';
```

Update the prop type:

```tsx
  featuredSchoolPreview: AdminFeaturedPreviewItem[];
  featuredMajorPreview: AdminFeaturedPreviewItem[];
  featuredSchedulePreview: AdminFeaturedPreviewDay[];
```

Render the new schedule section under the existing today preview:

```tsx
      <section aria-labelledby="featured-schedule-preview-heading">
        <h2 id="featured-schedule-preview-heading">未来 7 天轮换预览</h2>

        {featuredContentError ? null : (
          <div>
            {featuredSchedulePreview.map((day) => (
              <article key={day.date}>
                <h3>{day.date}</h3>
                <p>{day.weekday}</p>

                <div>
                  <h4>学校</h4>
                  {day.schools.length === 0 ? (
                    <p>当天没有可展示学校</p>
                  ) : (
                    <ul>
                      {day.schools.map((school) => (
                        <li key={`${day.date}-${school.slug}`}>
                          <span>{school.name}</span>
                          <span>{school.slug}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <div>
                  <h4>专业</h4>
                  {day.majors.length === 0 ? (
                    <p>当天没有可展示专业</p>
                  ) : (
                    <ul>
                      {day.majors.map((major) => (
                        <li key={`${day.date}-${major.slug}`}>
                          <span>{major.name}</span>
                          <span>{major.slug}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
```

- [ ] **Step 4: Run the focused page tests to verify they pass**

Run:

```powershell
node .\node_modules\vitest\vitest.mjs run tests/admin-page.test.tsx tests/admin-dashboard.test.tsx
```

Expected: `PASS`

- [ ] **Step 5: Commit the admin page schedule change**

Run:

```powershell
git add apps/web/tests/admin-page.test.tsx apps/web/tests/admin-dashboard.test.tsx "apps/web/app/(admin)/admin/page.tsx" apps/web/components/admin/dashboard-shell.tsx
git commit -m "feat(web): render featured content seven-day preview"
```

### Task 4: Verify the full feature end-to-end before handoff

**Files:**
- Modify: none
- Test: `apps/api/tests/test_admin_api.py`
- Test: `apps/web/tests/admin-review-api.test.ts`
- Test: `apps/web/tests/admin-page.test.tsx`
- Test: `apps/web/tests/admin-dashboard.test.tsx`

- [ ] **Step 1: Run the focused API regression suite**

Run:

```powershell
python -m pytest tests/test_admin_api.py -v
```

Expected: `PASS`, including the new seven-day preview coverage.

- [ ] **Step 2: Run the focused web admin regression suite**

Run:

```powershell
node .\node_modules\vitest\vitest.mjs run tests/admin-review-api.test.ts tests/admin-page.test.tsx tests/admin-dashboard.test.tsx
```

Expected: `PASS`

- [ ] **Step 3: Run the full web test suite**

Run:

```powershell
node .\node_modules\vitest\vitest.mjs run
```

Expected: `PASS`

- [ ] **Step 4: Run the production web build**

Run:

```powershell
node .\node_modules\next\dist\bin\next build
```

Expected: `Build completed successfully` with the existing Windows SWC warning still acceptable.

- [ ] **Step 5: Confirm the worktree is in the expected state**

Run:

```powershell
git status --short
```

Expected:
- no unexpected untracked files
- no uncommitted changes beyond the already-planned schedule implementation commits from Tasks 1 through 3
