# Release smoke and rollback runbook

This runbook is for a deployment owner operating a tagged release. It is
deliberately separate from local development startup and does not contain real
hosts, credentials or commands that mutate an external system automatically.

## Inputs and invariants

Before deployment, record:

- release tag, for example `1.0.0`;
- full Git commit SHA and the image tag selected for API and Web;
- database path and the last successful backup path;
- public API/Web base URLs and the operator responsible for rollback.

The API environment must set the same non-secret release identifier that will
be checked after deployment:

```env
GAOKAO_AGENT_RELEASE_VERSION=1.0.0
```

Do not put secrets in the release identifier, command transcript, screenshot or
verification report.

## Pre-deploy gate

1. Confirm the tag points to the intended commit and the reusable CI workflow
   passed for that commit.
2. Confirm the production Web API URL is set and is reachable by a browser.
3. Take a separate database backup and verify it with
   [`backup-sqlite.py`](../../scripts/backup-sqlite.py).
4. Confirm the migration plan is forward-only for the release. Do not couple an
   application rollback to an automatic database downgrade.
5. Record the previous image/tag and the current `/version` response.

## Deploy and verify

After the deployment owner has updated the API/Web service, run the smoke
against the public HTTPS origin. Use a private secret store or environment
injection for the admin and WeChat values; do not paste them into a report.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke-local-stack.ps1 `
  -ApiBaseUrl 'https://api.example.invalid' `
  -WebBaseUrl 'https://app.example.invalid' `
  -ExpectedReleaseVersion '1.0.0' `
  -ApiEnvFilePath '<private-runtime-env-file>'
```

The smoke must observe:

- API `/health` and `/version` are successful;
- `/version` equals the release identifier recorded before deployment;
- Chat health, skills, Web pages and admin settings are reachable;
- the deterministic chat and generic WeChat adapter probes pass;
- if official-account credentials are deliberately enabled, the dedicated
  plaintext/AES callback smoke also passes.

Record the command outcome, timestamp, release tag, commit SHA and non-secret
endpoint status. Never record raw headers, tokens, cookies or user messages.

## Rollback decision and procedure

Rollback the application when the new image fails startup, the version probe
does not match, or post-deploy smoke fails in a way that the operator cannot
repair within the release window.

1. Preserve failed-release logs, the failed tag/SHA, smoke output and migration
   revision.
2. Point API and Web back to the previously recorded image/tag or service
   artifact.
3. Restore the previous non-secret `GAOKAO_AGENT_RELEASE_VERSION` value.
4. Restart the application services using the deployment platform's normal
   mechanism; do not run an automatic Alembic downgrade.
5. Run the same health, `/version` and Web smoke against the previous release.
6. If data is damaged or incompatible, stop write traffic and follow the
   [`SQLite backup/restore runbook`](backup-restore-runbook.md) using a new
   restore target first.
7. Record whether the rollback restored application availability and whether a
   separate data recovery action is still required.

## Local synthetic rehearsal

The repository can rehearse version switching without Docker or production
credentials. Use the same temporary SQLite path for each run, a separate state
file, synthetic tokens, and an explicit `-ReleaseVersion`; `-RunSmoke` then
asserts `/version` automatically. The verified sequence is:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 `
  -ReleaseVersion 'release-old' `
  -ApiEnvFilePath 'apps/api/.env.example' `
  -WebEnvFilePath 'apps/web/.env.example' `
  -AdminToken '<synthetic-admin-token>' `
  -WechatOfficialAccountToken '<synthetic-wechat-token>' `
  -WechatOfficialAccountAppId '<synthetic-app-id>' `
  -WechatOfficialAccountEncodingAesKey '<43-character-synthetic-aes-key>' `
  -DatabasePath '.tmp/release-rehearsal.db' `
  -StateFilePath '.tmp/release-old.state.json' `
  -RunSmoke
```

Stop the stack, repeat with `release-new` and another state file, then repeat
with `release-old` to model rollback. This local sequence is evidence for the
repository boundary only; it does not replace a public HTTPS deployment,
monitoring check, or deployment-owner rollback rehearsal.

## Repository boundary

The repository provides the version endpoint, expected-version smoke assertion,
backup/restore scripts and deployment templates. A Docker daemon, GitHub
Environment, public HTTPS origin, monitoring system, secret store and rollback
owner are external prerequisites; none is claimed as completed by local tests.
