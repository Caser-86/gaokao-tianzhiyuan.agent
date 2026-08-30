# Demo data governance

`catalog.json` and `featured-content.json` are small, tracked demo fixtures for
local development, tests, screenshots and interview walkthroughs. They are not
an authoritative admissions, ranking or recommendation dataset.

## Current provenance boundary

| Field | Current meaning |
|---|---|
| `region` / `city` / `discipline` | Demo classification used by catalog lookup and UI filters |
| `summary` / `sections` / relation fields | Hand-authored demo copy used to exercise structured responses |
| `ranking_references[].source` / `year` / `scope` / `note` | Example citation shape; the current records are not a verified live ranking feed |
| `ranking_references[].url` | Placeholder URL in the fixture; never present it as an official source |
| `featured-content.json` | Editorial display and rotation fixture, not a recommendation rank |

## Rules for adding real data

Every non-demo record must carry, at minimum, a source URL, source name, source
publication/update date, applicable year, region, and an explicit note about
whether it is an official policy/source or a secondary reference. Keep raw
personal data, API credentials and unverified score predictions out of this
directory.

The UI and README must continue to state that admissions policies, plans and
cutoffs vary by year and region. A future ingestion job must preserve source
metadata instead of overwriting the demo fixtures in place.

## Pre-release checklist

Before presenting a record as non-demo content, confirm that it includes the
source name, source URL, publication or update date, applicable year, region,
and an explicit `official` or `secondary` classification. Display the source
and freshness boundary in the UI, keep stale records identifiable, and require
human review before publishing a policy, admissions plan, cutoff, ranking, or
recommendation claim. Run `python scripts/verify-data-assets.py` after changing
the JSON fixtures; that validator checks structure and relations, not the
truth of an external source.

The authoritative tracked data directory is the repository root `data/`. The
validator is:

```powershell
python scripts/verify-data-assets.py
```
