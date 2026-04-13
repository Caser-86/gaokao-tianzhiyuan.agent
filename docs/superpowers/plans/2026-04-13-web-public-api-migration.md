# Web Public API Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `apps/web` reproducible to install and test, then migrate the public-facing pages to use the API as their only runtime data source.

**Architecture:** First normalize the web workspace so Vitest runs from declared dependencies and a checked-in lockfile. Then add the missing public majors list API needed by the existing homepage, introduce a server-only public API client in `apps/web`, and finally migrate the homepage and detail pages away from local JSON reads while preserving clear `404` and non-`404` behavior.

**Tech Stack:** FastAPI, Next.js App Router, React 19, TypeScript, Vitest, Testing Library, npm

---

## File Structure

- `apps/web/package.json`: declare a reproducible Vitest execution path and any explicit dependency overrides needed for Windows-safe test execution
- `apps/web/package-lock.json`: committed install snapshot matching the normalized web dependency graph
- `apps/web/tests/toolchain-config.test.ts`: verifies the web workspace declares the reproducible test toolchain
- `apps/api/app/services/catalog.py`: add public major list projection for homepage cards
- `apps/api/app/routers/public.py`: expose `GET /api/public/majors`
- `apps/api/tests/test_public_catalog_api.py`: prove the new public majors list route works
- `apps/web/lib/public-content-api.ts`: server-only public API client and shared types/error class
- `apps/web/tests/public-content-api.test.ts`: verifies request paths, response parsing, and error classification
- `apps/web/app/page.tsx`: homepage server fetch via public API client
- `apps/web/app/schools/[slug]/page.tsx`: school detail page via public API client
- `apps/web/app/majors/[slug]/page.tsx`: major detail page via public API client
- `apps/web/tests/public-pages.test.tsx`: verifies API-backed public page rendering, `404`, and non-`404` behavior
- `apps/web/lib/content-catalog.ts`: remove after no imports remain

### Task 1: Normalize The Web Test Toolchain

**Files:**
- Modify: `apps/web/package.json`
- Modify: `apps/web/package-lock.json`
- Create: `apps/web/tests/toolchain-config.test.ts`
- Test: `apps/web/tests/toolchain-config.test.ts`

- [ ] **Step 1: Write the failing test**

Create `apps/web/tests/toolchain-config.test.ts` with:

```ts
import packageJson from '../package.json';

test('declares a reproducible vitest toolchain for the web workspace', () => {
  expect(packageJson.scripts.dev).toBe('node ./node_modules/next/dist/bin/next dev');
  expect(packageJson.scripts.build).toBe('node ./node_modules/next/dist/bin/next build');
  expect(packageJson.scripts.test).toBe('node ./node_modules/vitest/vitest.mjs run');
  expect(packageJson.devDependencies.rollup).toBe('npm:@rollup/wasm-node@4.60.1');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run from `apps/web`: `node ./node_modules/vitest/vitest.mjs run tests/toolchain-config.test.ts`

Expected: `FAIL` because `package.json` does not yet declare `rollup` as `npm:@rollup/wasm-node@4.60.1`.

- [ ] **Step 3: Write minimal implementation**

Update `apps/web/package.json` to:

```json
{
  "name": "gaokao-agent-web",
  "private": true,
  "scripts": {
    "dev": "node ./node_modules/next/dist/bin/next dev",
    "build": "node ./node_modules/next/dist/bin/next build",
    "test": "node ./node_modules/vitest/vitest.mjs run"
  },
  "dependencies": {
    "next": "15.4.0",
    "react": "19.1.0",
    "react-dom": "19.1.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.9.1",
    "@testing-library/react": "^16.3.2",
    "@types/node": "^22.15.3",
    "@types/react": "^19.1.0",
    "jsdom": "^29.0.2",
    "rollup": "npm:@rollup/wasm-node@4.60.1",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.5.0",
    "vitest": "^1.3.0"
  }
}
```

Then refresh the lockfile from the app workspace:

```bash
npm install
```

- [ ] **Step 4: Run test to verify it passes**

Run from `apps/web`: `node ./node_modules/vitest/vitest.mjs run tests/toolchain-config.test.ts`

Expected: `PASS` with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add apps/web/package.json apps/web/package-lock.json apps/web/tests/toolchain-config.test.ts
git commit -m "chore(web): normalize vitest toolchain"
```

### Task 2: Add The Public Majors List Endpoint Needed By The Homepage

**Files:**
- Modify: `apps/api/app/services/catalog.py`
- Modify: `apps/api/app/routers/public.py`
- Modify: `apps/api/tests/test_public_catalog_api.py`
- Test: `apps/api/tests/test_public_catalog_api.py`

- [ ] **Step 1: Write the failing test**

Append to `apps/api/tests/test_public_catalog_api.py`:

```python
def test_list_majors_returns_catalog_cards() -> None:
    response = client.get("/api/public/majors")

    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] == 4
    assert payload["items"][0] == {
        "slug": "clinical-medicine",
        "name": "临床医学",
        "discipline": "医学",
        "recommended_regions": ["江苏", "浙江", "四川"],
        "summary": "培养周期长、学习压力高，但职业壁垒强，适合抗压强且愿意长期投入的考生。",
    }
    assert payload["items"][-1]["slug"] == "microelectronics"
```

- [ ] **Step 2: Run test to verify it fails**

Run from `apps/api`: `python -m pytest tests/test_public_catalog_api.py -v`

Expected: `FAIL` with a `404` or missing route failure for `/api/public/majors`.

- [ ] **Step 3: Write minimal implementation**

Update `apps/api/app/services/catalog.py` to:

```python
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


CATALOG_PATH = Path(__file__).resolve().parents[4] / "data" / "catalog.json"


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def get_search_entry() -> dict[str, Any]:
    return load_catalog()["search_entry"]


def list_schools(*, region: str | None = None, keyword: str | None = None) -> dict[str, Any]:
    schools = load_catalog()["schools"]
    filtered = []

    for school in schools:
        if region and school["region"] != region:
            continue

        if keyword:
            haystack = " ".join(
                [
                    school["name"],
                    school["city"],
                    school["region"],
                    school["summary"],
                    " ".join(school["tags"]),
                ]
            )
            if keyword.lower() not in haystack.lower():
                continue

        filtered.append(
            {
                "slug": school["slug"],
                "name": school["name"],
                "region": school["region"],
                "city": school["city"],
                "tags": school["tags"],
                "summary": school["summary"],
            }
        )

    return {
        "items": filtered,
        "total": len(filtered),
    }


def list_majors() -> dict[str, Any]:
    majors = load_catalog()["majors"]
    items = [
        {
            "slug": major["slug"],
            "name": major["name"],
            "discipline": major["discipline"],
            "recommended_regions": major["recommended_regions"],
            "summary": major["summary"],
        }
        for major in majors
    ]

    return {
        "items": items,
        "total": len(items),
    }


def get_school_detail(slug: str) -> dict[str, Any] | None:
    schools = load_catalog()["schools"]
    return next((school for school in schools if school["slug"] == slug), None)


def get_major_detail(slug: str) -> dict[str, Any] | None:
    majors = load_catalog()["majors"]
    return next((major for major in majors if major["slug"] == slug), None)
```

Update `apps/api/app/routers/public.py` to:

```python
from fastapi import APIRouter, HTTPException, status

from ..services.catalog import (
    get_major_detail,
    get_school_detail,
    get_search_entry,
    list_majors,
    list_schools,
)

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/search-entry")
def search_entry() -> dict[str, object]:
    return get_search_entry()


@router.get("/schools")
def school_list(region: str | None = None, keyword: str | None = None) -> dict[str, object]:
    return list_schools(region=region, keyword=keyword)


@router.get("/majors")
def major_list() -> dict[str, object]:
    return list_majors()


@router.get("/schools/{slug}")
def school_detail(slug: str) -> dict[str, object]:
    school = get_school_detail(slug)
    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="school not found",
        )
    return school


@router.get("/majors/{slug}")
def major_detail(slug: str) -> dict[str, object]:
    major = get_major_detail(slug)
    if major is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="major not found",
        )
    return major
```

- [ ] **Step 4: Run test to verify it passes**

Run from `apps/api`: `python -m pytest tests/test_public_catalog_api.py -v`

Expected: `PASS` with `4 passed`.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/services/catalog.py apps/api/app/routers/public.py apps/api/tests/test_public_catalog_api.py
git commit -m "feat(api): add public major list endpoint"
```

### Task 3: Add A Server-Only Public Content API Client

**Files:**
- Create: `apps/web/lib/public-content-api.ts`
- Create: `apps/web/tests/public-content-api.test.ts`
- Test: `apps/web/tests/public-content-api.test.ts`

- [ ] **Step 1: Write the failing test**

Create `apps/web/tests/public-content-api.test.ts` with:

```ts
import { afterEach, beforeEach, expect, test, vi } from 'vitest';

import {
  PublicApiError,
  getMajorBySlug,
  getSearchEntry,
  getSchoolBySlug,
  listMajors,
  listSchools,
} from '../lib/public-content-api';

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
  process.env.GAOKAO_AGENT_API_URL = 'http://api.example.com';
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  delete process.env.GAOKAO_AGENT_API_URL;
});

test('getSearchEntry fetches public search metadata without caching', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      title: '高考志愿助手',
      description: '帮助考生和家长快速看学校、专业、地域与就业。',
      quick_prompts: ['查学校', '查专业'],
    }),
  });

  const entry = await getSearchEntry();

  expect(fetchMock).toHaveBeenCalledWith(
    'http://api.example.com/api/public/search-entry',
    { cache: 'no-store' },
  );
  expect(entry.quickPrompts).toEqual(['查学校', '查专业']);
});

test('listSchools returns public school cards', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      items: [
        {
          slug: 'southeast-university',
          name: '东南大学',
          region: '江苏',
          city: '南京',
          tags: ['985'],
          summary: '工科见长。',
        },
      ],
      total: 1,
    }),
  });

  const payload = await listSchools();

  expect(payload.total).toBe(1);
  expect(payload.items[0]?.slug).toBe('southeast-university');
});

test('listMajors returns public major cards', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      items: [
        {
          slug: 'clinical-medicine',
          name: '临床医学',
          discipline: '医学',
          recommended_regions: ['江苏', '浙江'],
          summary: '培养周期长。',
        },
      ],
      total: 1,
    }),
  });

  const payload = await listMajors();

  expect(payload.total).toBe(1);
  expect(payload.items[0]?.recommendedRegions).toEqual(['江苏', '浙江']);
});

test('getSchoolBySlug throws a 404 PublicApiError for missing schools', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: false,
    status: 404,
    text: async () => 'school not found',
  });

  await expect(getSchoolBySlug('missing-school')).rejects.toEqual(
    expect.objectContaining<Partial<PublicApiError>>({
      status: 404,
      message: 'school not found',
    }),
  );
});

test('getMajorBySlug propagates non-404 failures with status', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: false,
    status: 500,
    text: async () => 'server error',
  });

  await expect(getMajorBySlug('clinical-medicine')).rejects.toEqual(
    expect.objectContaining<Partial<PublicApiError>>({
      status: 500,
      message: 'server error',
    }),
  );
});
```

- [ ] **Step 2: Run test to verify it fails**

Run from `apps/web`: `node ./node_modules/vitest/vitest.mjs run tests/public-content-api.test.ts`

Expected: `FAIL` because `apps/web/lib/public-content-api.ts` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `apps/web/lib/public-content-api.ts` with:

```ts
import 'server-only';

export type PageSection = {
  type: string;
  title: string;
  items: string[];
};

export type SearchEntryData = {
  title: string;
  description: string;
  quickPrompts: string[];
};

export type SchoolSummary = {
  slug: string;
  name: string;
  region: string;
  city: string;
  tags: string[];
  summary: string;
};

export type MajorSummary = {
  slug: string;
  name: string;
  discipline: string;
  recommendedRegions: string[];
  summary: string;
};

export type SchoolDetail = SchoolSummary & {
  sections: PageSection[];
  relatedMajors: string[];
};

export type MajorDetail = MajorSummary & {
  sections: PageSection[];
  relatedSchools: string[];
};

export class PublicApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message || `Request failed with status ${status}`);
    this.name = 'PublicApiError';
    this.status = status;
  }
}

const getPublicApiUrl = (): string =>
  process.env.GAOKAO_AGENT_API_URL ?? 'http://127.0.0.1:8000';

async function fetchPublicJson<T>(path: string): Promise<T> {
  const response = await fetch(`${getPublicApiUrl()}${path}`, {
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new PublicApiError(
      response.status,
      (await response.text()) || `Request failed with status ${response.status}`,
    );
  }

  return (await response.json()) as T;
}

export async function getSearchEntry(): Promise<SearchEntryData> {
  const payload = await fetchPublicJson<{
    title: string;
    description: string;
    quick_prompts: string[];
  }>('/api/public/search-entry');

  return {
    title: payload.title,
    description: payload.description,
    quickPrompts: payload.quick_prompts,
  };
}

export async function listSchools(): Promise<{ items: SchoolSummary[]; total: number }> {
  return fetchPublicJson<{ items: SchoolSummary[]; total: number }>('/api/public/schools');
}

export async function listMajors(): Promise<{ items: MajorSummary[]; total: number }> {
  const payload = await fetchPublicJson<{
    items: Array<{
      slug: string;
      name: string;
      discipline: string;
      recommended_regions: string[];
      summary: string;
    }>;
    total: number;
  }>('/api/public/majors');

  return {
    items: payload.items.map((item) => ({
      slug: item.slug,
      name: item.name,
      discipline: item.discipline,
      recommendedRegions: item.recommended_regions,
      summary: item.summary,
    })),
    total: payload.total,
  };
}

export async function getSchoolBySlug(slug: string): Promise<SchoolDetail> {
  const payload = await fetchPublicJson<{
    slug: string;
    name: string;
    region: string;
    city: string;
    tags: string[];
    summary: string;
    sections: PageSection[];
    related_majors: string[];
  }>(`/api/public/schools/${slug}`);

  return {
    slug: payload.slug,
    name: payload.name,
    region: payload.region,
    city: payload.city,
    tags: payload.tags,
    summary: payload.summary,
    sections: payload.sections,
    relatedMajors: payload.related_majors,
  };
}

export async function getMajorBySlug(slug: string): Promise<MajorDetail> {
  const payload = await fetchPublicJson<{
    slug: string;
    name: string;
    discipline: string;
    recommended_regions: string[];
    summary: string;
    sections: PageSection[];
    related_schools: string[];
  }>(`/api/public/majors/${slug}`);

  return {
    slug: payload.slug,
    name: payload.name,
    discipline: payload.discipline,
    recommendedRegions: payload.recommended_regions,
    summary: payload.summary,
    sections: payload.sections,
    relatedSchools: payload.related_schools,
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run from `apps/web`: `node ./node_modules/vitest/vitest.mjs run tests/public-content-api.test.ts`

Expected: `PASS` with `5 passed`.

- [ ] **Step 5: Commit**

```bash
git add apps/web/lib/public-content-api.ts apps/web/tests/public-content-api.test.ts
git commit -m "feat(web): add public content api client"
```

### Task 4: Migrate The Public Pages To The API Client

**Files:**
- Modify: `apps/web/app/page.tsx`
- Modify: `apps/web/app/schools/[slug]/page.tsx`
- Modify: `apps/web/app/majors/[slug]/page.tsx`
- Delete: `apps/web/lib/content-catalog.ts`
- Create: `apps/web/tests/public-pages.test.tsx`
- Test: `apps/web/tests/public-pages.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `apps/web/tests/public-pages.test.tsx` with:

```tsx
import { render, screen } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

class MockPublicApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const getSearchEntryMock = vi.fn();
const listSchoolsMock = vi.fn();
const listMajorsMock = vi.fn();
const getSchoolBySlugMock = vi.fn();
const getMajorBySlugMock = vi.fn();
const notFoundMock = vi.fn(() => {
  throw new Error('NEXT_NOT_FOUND');
});

vi.mock('../lib/public-content-api', () => ({
  PublicApiError: MockPublicApiError,
  getSearchEntry: getSearchEntryMock,
  listSchools: listSchoolsMock,
  listMajors: listMajorsMock,
  getSchoolBySlug: getSchoolBySlugMock,
  getMajorBySlug: getMajorBySlugMock,
}));

vi.mock('next/navigation', () => ({
  notFound: notFoundMock,
}));

import HomePage from '../app/page';
import MajorPage from '../app/majors/[slug]/page';
import SchoolPage from '../app/schools/[slug]/page';

beforeEach(() => {
  getSearchEntryMock.mockReset();
  listSchoolsMock.mockReset();
  listMajorsMock.mockReset();
  getSchoolBySlugMock.mockReset();
  getMajorBySlugMock.mockReset();
  notFoundMock.mockClear();
});

test('home page renders API-backed search and catalog data', async () => {
  getSearchEntryMock.mockResolvedValue({
    title: '高考志愿助手',
    description: '帮助考生和家长快速看学校、专业、地域与就业。',
    quickPrompts: ['查学校', '查专业'],
  });
  listSchoolsMock.mockResolvedValue({
    items: [
      {
        slug: 'southeast-university',
        name: '东南大学',
        region: '江苏',
        city: '南京',
        tags: ['985'],
        summary: '工科见长。',
      },
    ],
    total: 1,
  });
  listMajorsMock.mockResolvedValue({
    items: [
      {
        slug: 'clinical-medicine',
        name: '临床医学',
        discipline: '医学',
        recommendedRegions: ['江苏', '浙江'],
        summary: '培养周期长。',
      },
    ],
    total: 1,
  });

  render(await HomePage());

  expect(screen.getByRole('heading', { name: '高考志愿助手' })).toBeInTheDocument();
  expect(screen.getByText('东南大学')).toBeInTheDocument();
  expect(screen.getByText('临床医学')).toBeInTheDocument();
});

test('home page renders an explicit error state on public API failure', async () => {
  getSearchEntryMock.mockRejectedValue(new Error('boom'));

  render(await HomePage());

  expect(screen.getByText('公开内容加载失败，请稍后重试。')).toBeInTheDocument();
});

test('school page renders API-backed detail data', async () => {
  getSchoolBySlugMock.mockResolvedValue({
    slug: 'southeast-university',
    name: '东南大学',
    region: '江苏',
    city: '南京',
    tags: ['985'],
    summary: '工科见长。',
    sections: [{ type: 'highlights', title: '学校亮点', items: ['建筑强'] }],
    relatedMajors: ['architecture'],
  });

  render(await SchoolPage({ params: Promise.resolve({ slug: 'southeast-university' }) }));

  expect(screen.getByRole('heading', { name: '东南大学' })).toBeInTheDocument();
  expect(screen.getByText('学校亮点')).toBeInTheDocument();
});

test('school page calls notFound on 404 detail responses', async () => {
  getSchoolBySlugMock.mockRejectedValue(new MockPublicApiError(404, 'school not found'));

  await expect(
    SchoolPage({ params: Promise.resolve({ slug: 'missing-school' }) }),
  ).rejects.toThrow('NEXT_NOT_FOUND');

  expect(notFoundMock).toHaveBeenCalled();
});

test('major page calls notFound on 404 detail responses', async () => {
  getMajorBySlugMock.mockRejectedValue(new MockPublicApiError(404, 'major not found'));

  await expect(
    MajorPage({ params: Promise.resolve({ slug: 'missing-major' }) }),
  ).rejects.toThrow('NEXT_NOT_FOUND');

  expect(notFoundMock).toHaveBeenCalled();
});

test('major page renders an explicit error state on non-404 failures', async () => {
  getMajorBySlugMock.mockRejectedValue(new MockPublicApiError(500, 'server error'));

  render(await MajorPage({ params: Promise.resolve({ slug: 'clinical-medicine' }) }));

  expect(screen.getByText('公开内容加载失败，请稍后重试。')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run from `apps/web`: `node ./node_modules/vitest/vitest.mjs run tests/public-pages.test.tsx`

Expected: `FAIL` because the public pages still import `apps/web/lib/content-catalog.ts` instead of the new API client.

- [ ] **Step 3: Write minimal implementation**

Update `apps/web/app/page.tsx` to:

```tsx
import Link from 'next/link';

import SearchEntry from '../components/public/search-entry';
import { getSearchEntry, listMajors, listSchools } from '../lib/public-content-api';

export default async function HomePage() {
  try {
    const [searchEntry, schoolPayload, majorPayload] = await Promise.all([
      getSearchEntry(),
      listSchools(),
      listMajors(),
    ]);

    return (
      <main className="page-shell">
        <SearchEntry
          title={searchEntry.title}
          description={searchEntry.description}
          quickPrompts={searchEntry.quickPrompts}
        />

        <section className="grid two" style={{ marginTop: 28 }}>
          <article className="panel">
            <h2 className="panel-title">学校速查</h2>
            <div className="catalog-list">
              {schoolPayload.items.map((school) => (
                <Link key={school.slug} href={`/schools/${school.slug}`} className="catalog-card">
                  <strong>{school.name}</strong>
                  <p>{school.summary}</p>
                  <div className="meta">
                    <span>{school.region}</span>
                    <span>{school.city}</span>
                    {school.tags.map((tag) => (
                      <span key={tag}>{tag}</span>
                    ))}
                  </div>
                </Link>
              ))}
            </div>
          </article>

          <article className="panel">
            <h2 className="panel-title">专业速查</h2>
            <div className="catalog-list">
              {majorPayload.items.map((major) => (
                <Link key={major.slug} href={`/majors/${major.slug}`} className="catalog-card">
                  <strong>{major.name}</strong>
                  <p>{major.summary}</p>
                  <div className="meta">
                    <span>{major.discipline}</span>
                    {major.recommendedRegions.slice(0, 3).map((region) => (
                      <span key={region}>{region}</span>
                    ))}
                  </div>
                </Link>
              ))}
            </div>
          </article>
        </section>
      </main>
    );
  } catch {
    return (
      <main className="page-shell">
        <section className="panel">
          <h1 className="panel-title">公开内容暂时不可用</h1>
          <p>公开内容加载失败，请稍后重试。</p>
        </section>
      </main>
    );
  }
}
```

Update `apps/web/app/schools/[slug]/page.tsx` to:

```tsx
import Link from 'next/link';
import { notFound } from 'next/navigation';

import PageSectionRenderer from '../../../components/public/page-section-renderer';
import { PublicApiError, getSchoolBySlug } from '../../../lib/public-content-api';

type SchoolPageProps = {
  params: Promise<{ slug: string }>;
};

export default async function SchoolPage({ params }: SchoolPageProps) {
  const { slug } = await params;

  try {
    const school = await getSchoolBySlug(slug);

    return (
      <main className="page-shell">
        <section className="masthead">
          <span className="eyebrow">学校解读</span>
          <h1 className="hero-title">{school.name}</h1>
          <p className="hero-copy">{school.summary}</p>
          <div className="meta">
            <span>{school.region}</span>
            <span>{school.city}</span>
            {school.tags.map((tag) => (
              <span key={tag}>{tag}</span>
            ))}
          </div>
          <div className="link-row">
            {school.relatedMajors.map((majorSlug) => (
              <Link key={majorSlug} href={`/majors/${majorSlug}`} className="cta secondary">
                查看相关专业
              </Link>
            ))}
          </div>
        </section>

        <PageSectionRenderer sections={school.sections} />
      </main>
    );
  } catch (error) {
    if (error instanceof PublicApiError && error.status === 404) {
      notFound();
    }

    return (
      <main className="page-shell">
        <section className="panel">
          <h1 className="panel-title">学校内容暂时不可用</h1>
          <p>公开内容加载失败，请稍后重试。</p>
        </section>
      </main>
    );
  }
}
```

Update `apps/web/app/majors/[slug]/page.tsx` to:

```tsx
import Link from 'next/link';
import { notFound } from 'next/navigation';

import PageSectionRenderer from '../../../components/public/page-section-renderer';
import { PublicApiError, getMajorBySlug } from '../../../lib/public-content-api';

type MajorPageProps = {
  params: Promise<{ slug: string }>;
};

export default async function MajorPage({ params }: MajorPageProps) {
  const { slug } = await params;

  try {
    const major = await getMajorBySlug(slug);

    return (
      <main className="page-shell">
        <section className="masthead">
          <span className="eyebrow">专业解读</span>
          <h1 className="hero-title">{major.name}</h1>
          <p className="hero-copy">{major.summary}</p>
          <div className="meta">
            <span>{major.discipline}</span>
            {major.recommendedRegions.map((region) => (
              <span key={region}>{region}</span>
            ))}
          </div>
          <div className="link-row">
            {major.relatedSchools.map((schoolSlug) => (
              <Link key={schoolSlug} href={`/schools/${schoolSlug}`} className="cta secondary">
                查看相关学校
              </Link>
            ))}
          </div>
        </section>

        <PageSectionRenderer sections={major.sections} />
      </main>
    );
  } catch (error) {
    if (error instanceof PublicApiError && error.status === 404) {
      notFound();
    }

    return (
      <main className="page-shell">
        <section className="panel">
          <h1 className="panel-title">专业内容暂时不可用</h1>
          <p>公开内容加载失败，请稍后重试。</p>
        </section>
      </main>
    );
  }
}
```

Delete `apps/web/lib/content-catalog.ts`.

- [ ] **Step 4: Run test to verify it passes**

Run from `apps/api`:

```bash
python -m pytest tests/test_public_catalog_api.py -v
```

Run from `apps/web`:

```bash
node ./node_modules/vitest/vitest.mjs run tests/toolchain-config.test.ts tests/public-content-api.test.ts tests/public-pages.test.tsx tests/public-content.test.tsx
```

Expected:

- `apps/api/tests/test_public_catalog_api.py` reports `4 passed`
- the Vitest command reports `13 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/web/app/page.tsx apps/web/app/schools/[slug]/page.tsx apps/web/app/majors/[slug]/page.tsx apps/web/tests/public-pages.test.tsx
git rm apps/web/lib/content-catalog.ts
git commit -m "feat(web): migrate public pages to public api"
```
