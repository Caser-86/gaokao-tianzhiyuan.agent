# Web Public API Migration And Toolchain Normalization Design

## Goal

Make `apps/web` reproducible to install and test, then migrate the public-facing pages to use the API as their only runtime data source.

## Current Context

- `apps/api` already exposes public catalog endpoints:
  - `GET /api/public/search-entry`
  - `GET /api/public/schools`
  - `GET /api/public/schools/{slug}`
  - `GET /api/public/majors/{slug}`
- `apps/web` currently renders:
  - the public home page at `app/page.tsx`
  - school detail pages at `app/schools/[slug]/page.tsx`
  - major detail pages at `app/majors/[slug]/page.tsx`
- Those public pages still read local JSON through `apps/web/lib/content-catalog.ts`.
- The web test environment was only made to pass on this machine through an environment-level Rollup workaround inside `node_modules`. That is not a durable project setup.
- The admin dashboard already uses a server-only API client pattern. That is the right precedent for public content as well.

## Scope

This design covers:

1. Normalizing the `apps/web` install and test setup so it works through declared dependencies and checked-in lockfiles
2. Replacing local JSON reads in public pages with server-side calls to the public API
3. Preserving current public page structure and visual output as much as practical
4. Adding focused web tests that prove the public pages now depend on API data

This design does not cover:

- Client-side fetching for public pages
- Offline or local-file fallback behavior
- Search UX expansion, filtering, or pagination
- Publishing workflows
- Broader frontend redesign work

## Recommended Approach

Use the API as the only runtime data source for public pages and keep all fetching on the server. Introduce a small server-only `public-content-api` module in `apps/web`, migrate the home page and both detail pages to use it, and remove the old local file reader. In parallel, normalize the web toolchain by checking in the lockfile and making the test command work from declared project dependencies instead of machine-specific `node_modules` edits.

This is the smallest durable architecture:

- one clear data boundary between web and api
- one public content path instead of API plus JSON duplication
- predictable install and test behavior for future work

## Alternatives Considered

### Option A: Toolchain-only cleanup

Normalize `apps/web` dependencies and test execution, but keep public pages reading local JSON.

Pros:

- smallest immediate code change
- lowest migration risk

Cons:

- keeps two runtime data paths in the system
- delays the API boundary cleanup we already need

### Option B: Toolchain normalization plus API-only public pages (recommended)

Normalize the web environment and migrate all public pages to a server-only API client.

Pros:

- removes duplicate data-source logic
- keeps public pages aligned with API contracts
- matches the admin-side architecture already in the repo

Cons:

- slightly larger change set than toolchain-only cleanup

### Option C: Shared universal client layer

Create a broader shared web data layer for admin and public routes at once, including caching policy unification.

Pros:

- most complete long-term structure

Cons:

- too much structural change for the current milestone
- mixes environment cleanup with a larger refactor

## Architecture

### Toolchain normalization

`apps/web` should be installable and testable without ad hoc edits in `node_modules`.

Responsibilities:

- keep `package.json` scripts explicit and runnable from the app workspace
- keep `package-lock.json` checked in as the canonical install snapshot
- ensure the chosen Rollup or Vitest execution path is expressed through declared project dependencies or committed package metadata

The outcome should be that a clean install in `apps/web` can run the existing Vitest suite without relying on manual one-off commands.

### Public API client

Create a server-only module at `apps/web/lib/public-content-api.ts`.

Responsibilities:

- fetch `/api/public/search-entry`
- fetch `/api/public/schools`
- fetch `/api/public/schools/{slug}`
- fetch `/api/public/majors/{slug}`
- centralize API base URL configuration
- normalize API errors into a small set of web-facing behaviors

This module should become the only runtime source of public content in the web app.

### Page responsibilities

The existing public routes remain the entry points:

- `apps/web/app/page.tsx`
- `apps/web/app/schools/[slug]/page.tsx`
- `apps/web/app/majors/[slug]/page.tsx`

Responsibilities:

- call the public API client on the server
- pass the fetched data to presentational components
- distinguish `404` from general API failures

The existing public components should remain presentational. This work should not restructure them unless a small prop adjustment is required.

### Removal of local runtime JSON reads

`apps/web/lib/content-catalog.ts` is a transitional implementation and should be removed from the public page runtime path.

If any types in that file are still useful, they may be moved or renamed into the new API client module. The important constraint is that public pages no longer call `fs.readFile()` or depend on `data/catalog.json` at runtime.

## Data Flow

### Home page

1. `app/page.tsx` calls the public API client on the server.
2. The client fetches:
   - search entry metadata
   - school list
   - major list
3. The page renders the existing public landing layout using those API responses.

### School detail page

1. `app/schools/[slug]/page.tsx` receives the route slug.
2. The public API client fetches `/api/public/schools/{slug}`.
3. If the API returns `404`, the page calls `notFound()`.
4. Otherwise the page renders the school detail content and related-major links.

### Major detail page

1. `app/majors/[slug]/page.tsx` receives the route slug.
2. The public API client fetches `/api/public/majors/{slug}`.
3. If the API returns `404`, the page calls `notFound()`.
4. Otherwise the page renders the major detail content and related-school links.

## Error Handling

Public pages must distinguish missing content from backend failures.

### Not found behavior

- `404` from the school detail API maps to `notFound()`
- `404` from the major detail API maps to `notFound()`

### Non-404 failures

- home page failures should render a visible error state instead of pretending data exists
- school and major detail pages should render a simple error block for non-404 failures
- no route should silently fall back to `data/catalog.json`

### Configuration failures

If the public API base URL is missing, malformed, or unreachable, the API client should fail clearly enough that the page can show a deterministic error state.

## Caching Strategy

Use a conservative server-fetch strategy first.

- public page fetches should default to `cache: 'no-store'` or an equivalent explicit non-cached mode
- do not introduce incremental revalidation yet
- revisit caching only after the API-backed rendering path is stable

This keeps debugging straightforward while the public API boundary is still new.

## Toolchain Notes

The durable setup should satisfy these constraints:

- no manual `npm install --no-save ...` follow-up is required after cloning
- the declared `apps/web` dependencies and lockfile are enough to install the project
- the committed test command works on a clean workspace

If the Windows execution environment still requires a wasm-based Rollup path, that choice should be committed in project metadata rather than left as an implicit machine-local workaround.

## Testing Strategy

### Public API client tests

Add focused tests for:

- search entry fetching
- school list fetching
- school detail fetching
- major detail fetching
- `404` classification for detail endpoints
- non-`404` failure propagation

### Page tests

Update or add page-level tests that verify:

- the home page renders API-backed search entry and catalog data
- the school page renders API-backed detail data
- the major page renders API-backed detail data
- detail pages call `notFound()` on API `404`
- pages show explicit error states for non-`404` failures

These tests should mock the web API client and avoid real network requests.

### Regression coverage

Retain the existing presentational component tests. They still provide useful coverage for the public layout while the data source changes underneath them.

## File Impact

Expected implementation work will likely touch:

- `apps/web/package.json`
- `apps/web/package-lock.json`
- `apps/web/app/page.tsx`
- `apps/web/app/schools/[slug]/page.tsx`
- `apps/web/app/majors/[slug]/page.tsx`
- `apps/web/lib/content-catalog.ts`
- `apps/web/lib/public-content-api.ts`
- `apps/web/tests/public-content.test.tsx`

Additional test files may be added if splitting page and API-client coverage is cleaner.

## Success Criteria

The work is complete when:

- `apps/web` can be installed and its test suite run through committed dependency metadata
- public web pages no longer read `data/catalog.json` at runtime
- the home page, school page, and major page all fetch content through the public API client
- school and major `404` responses map to `notFound()`
- non-`404` failures show explicit error states
- web tests demonstrate that the public pages now depend on API data rather than local file reads
