# Data Provenance Contract Verification

> Date: 2026-08-31
> Base revision: `ce72eb56f3de22df7b594f8036045ebc75f6299d`
> Scope: working-tree verification before delivery commit

## Changes verified

- The tracked root `data/catalog.json` now declares a top-level
  `data_provenance` object with status, source, freshness, applicable scope,
  official/secondary boundary and a user-facing disclaimer.
- `scripts/verify-data-assets.py` validates the provenance contract. Demo data
  may omit a source URL and applicable year; non-demo data must provide both,
  and demo data cannot be marked official.
- Public search, school/major list and school/major detail responses expose
  the same provenance metadata. The Web API client maps the snake_case payload
  and school/major detail pages render the boundary before the content.
- The untracked `apps/data/` directory was not modified or staged.

## Results

| Check | Result |
|---|---|
| API full test suite | `215 passed` |
| Web full test suite | `28 test files, 130 passed` |
| Web coverage | `87.03% statements / 84.17% branches / 73.15% functions` |
| Web typecheck | Passed |
| Web lint | Passed; 3 existing `<img>` optimization warnings |
| Data asset validator | Passed: 2 schools, 4 majors |
| Data asset validator tests | `4 passed` |
| Ruff changed Python files | Passed |
| Documentation consistency | Passed as part of API suite |

The API/Web tests and asset checks are local, fixed-fixture verification. The
provenance contract records declared metadata; it does not independently prove
that an external source is authoritative or that a recommendation is correct.
The repository does not claim a production data refresh, public HTTPS smoke,
monitoring or release rollback from this record.

## Commands

```powershell
Set-Location apps/api
.\.venv\Scripts\python.exe -m pytest -q --cov=app --cov-report=term-missing
Set-Location ../..
Set-Location apps/web
npm run test:coverage
npm run typecheck
npm run lint
Set-Location ../..
.\apps\api\.venv\Scripts\python.exe scripts/verify-data-assets.py
.\apps\api\.venv\Scripts\python.exe scripts/tests/test_verify_data_assets.py
.\apps\api\.venv\Scripts\ruff.exe check apps/api/app/services/data_provenance.py apps/api/app/services/catalog.py apps/api/tests/test_data_provenance.py apps/api/tests/test_public_catalog_api.py scripts/verify-data-assets.py scripts/tests/test_verify_data_assets.py
```

## Remaining external confirmation

Authoritative source agreement, refresh ownership, source-truth review,
production HTTPS deployment, monitoring, secret-manager provisioning and
deployment-owner rollback confirmation remain outside this local verification.
