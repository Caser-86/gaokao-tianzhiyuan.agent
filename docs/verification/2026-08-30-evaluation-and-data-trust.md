# Evaluation and Data Trust Verification

> Date: 2026-08-30
> Base revision: `f5a8340`
> Scope: working-tree verification before delivery commit

## Changes verified

- The offline evaluation runner now uses the first project default candidate,
  `skills/zhangxuefeng/SKILL.md`, which is also the runtime default Prompt.
- The fixed evaluation set contains 13 cases covering catalog lookup, missing
  context, volunteer strategy, major choice, sensitive-request boundary,
  Provider failures, invalid JSON, and successful structured output.
- Demo data remains under the root `data/` directory and is explicitly marked
  as non-authoritative. Future real records require source and freshness
  metadata plus human review before publication.
- The untracked `apps/data/` directory was not modified or staged.

## Results

| Check | Result |
|---|---|
| API full test suite | `213 passed` |
| Web test baseline | `129 passed` |
| Offline evaluation | `13/13 passed` |
| Offline routing/schema/fallback metrics | `100% / 100% / 100%` |
| Data asset validation | Passed |
| Ruff check for changed Python files | Passed |

The offline metrics are fixed-case, no-network results. They do not represent
online model quality, admissions recommendation accuracy, or production SLA.
The local Ark credential was used only outside Git for the separately reported
real-model smoke test; it is not included in this verification note or the
repository.

## Remaining external confirmation

Production HTTPS deployment, public post-deploy smoke, monitoring and alert
routing, secret-manager provisioning/rotation, and deployment-owner rollback
confirmation remain outside this local verification.
