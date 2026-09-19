# SQLite backup and restore runbook

This runbook covers the local SQLite deployment boundary. It does not upload
data, change production state, or erase an existing file unless `--force` is
explicitly supplied to the restore command.

## Backup

Stop write traffic or run the backup against a maintenance window. Use the
standard-library SQLite online backup API so the backup is not a blind file
copy:

```powershell
python scripts/backup-sqlite.py `
  .tmp/gaokao-agent.db `
  .tmp/backups/gaokao-agent-2026-08-25.db
```

The command refuses to overwrite an existing backup and runs
`PRAGMA integrity_check` before reporting success. Store production backups
outside the Git workspace with OS-level access control and an independent
retention policy.

## Restore rehearsal

Restore into a new temporary path first:

```powershell
python scripts/restore-sqlite.py `
  .tmp/backups/gaokao-agent-2026-08-25.db `
  .tmp/restore-rehearsal/gaokao-agent.db
```

Then run the migration and health checks against the restored environment:

```powershell
Set-Location apps/api
python -m alembic upgrade head
Invoke-RestMethod http://127.0.0.1:8000/health
```

Only after an operator has verified the rehearsal should a stopped service be
pointed at a production restore target. Existing targets require explicit
`--force`; take a separate backup before replacing them.

## Rollback boundary

- Application rollback and database rollback are separate decisions.
- Apply Alembic migrations forward on the restored copy; do not downgrade a
  production database automatically during a failed deployment.
- Preserve the failed release logs and migration revision for postmortem work.
- This repository does not claim that a cloud backup, object-store retention,
  or production restore has been executed; those remain deployment-specific.
