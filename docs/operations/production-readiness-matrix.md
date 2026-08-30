# Production readiness matrix

This matrix separates what is reproducible in the repository from what still
requires a deployment owner, a host, or an external provider account.

| Area | Repository evidence | Required external confirmation |
|---|---|---|
| API/Web config | `apps/api/.env.example`, `deploy/*/*.env.example`, Compose and systemd templates | Real relay, database path, public HTTPS origin and host-specific values |
| Secret policy | `.env*` ignored, production-like config rejects default admin/session values, no real keys in fixtures | Secret manager/GitHub Environment provisioning and rotation |
| Data source | [`data/README.md`](../../data/README.md), root `data/` validator, `data_provenance` API/UI contract, source/year/region boundary | Authoritative source agreement, data refresh owner and source-truth review |
| Database | Alembic is the schema entry point; upgrade/downgrade/upgrade has been rehearsed in a temporary DB | Production migration window and backup confirmation |
| Backup/restore | [`backup-restore-runbook.md`](backup-restore-runbook.md), standard-library SQLite backup/restore scripts | Off-host encrypted backup, retention, restore drill and access review |
| Release | CI workflow and Release workflow share the verification gate; production Web API URL is required | GitHub tag workflow, Docker daemon build, approval and artifact promotion |
| Post-deploy | Health, `/version` and local smoke scripts cover API/Web/chat/admin/WeChat fixtures; `smoke-local-stack.ps1 -ExpectedReleaseVersion` can compare a deployed value | Public HTTPS smoke, monitoring, alert routing and rollback owner |
| Privacy | API startup/request cleanup and `DELETE /api/privacy/me`; trace retention depends on runtime logs | Journald/container rotation, backup deletion policy and incident process |

## Configuration rules

- Never copy a real `.env` into Git, a screenshot, a trace, or a test fixture.
- Replace every `<...>`/`replace-with-...` placeholder outside the operator's
  private environment before deployment.
- Production-like API configuration must use a non-default admin token, a
  non-default session secret, a valid public Web API URL and a deliberate
  database path.
- Keep demo data and production data in separate storage locations.

## Release decision

The repository can claim “locally verified” when `scripts/verify-project.ps1`
passes. It must not claim “production deployed” until the external
confirmation column has been completed and recorded by the deployment owner.
